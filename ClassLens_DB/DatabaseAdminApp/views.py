from rest_framework import viewsets, status
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth.hashers import make_password
from django.http import HttpResponse
import pandas as pd
import io
from .pagination import StudentPagination
from Home.models import (
    Department, Teacher, Student, Subject, SubjectFromDept,
    StudentEnrollment, TeacherSubject, AdminUser, StudentAttendancePercentage
)
from .serializers import (
    DepartmentSerializer, TeacherSerializer, StudentSerializer,
    SubjectSerializer, SubjectFromDeptSerializer, StudentEnrollmentSerializer,
    TeacherSubjectSerializer, AdminUserSerializer
)

from rest_framework.permissions import BasePermission

class IsSuperUser(BasePermission):
    """
    Allow access only to superusers.
    """

    def has_permission(self, request, view):
      return bool(
          request.user
          and request.user.is_authenticated
          and getattr(request.user, "is_superuser", False)
      )

@api_view(['POST'])
@permission_classes([AllowAny])
def admin_login(request):
    username = request.data.get('username')
    password = request.data.get('password')
    
    try:
        admin = AdminUser.objects.get(username=username, is_active=True)
        if admin.check_password(password):
            refresh = RefreshToken.for_user(admin)
            refresh['username'] = admin.username
            refresh['user_id'] = admin.id 
            
            return Response({
                'access': str(refresh.access_token),
                'refresh': str(refresh),
                'username': admin.username
            })
        else:
            return Response({'error': 'Invalid credentials'}, status=status.HTTP_401_UNAUTHORIZED)
    except AdminUser.DoesNotExist:
        return Response({'error': 'Invalid credentials'}, status=status.HTTP_401_UNAUTHORIZED)

class AdminUserViewSet(viewsets.ModelViewSet):
  
    queryset = AdminUser.objects.all().order_by("id")
    serializer_class = AdminUserSerializer
    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        if instance.id == request.user.id:
            return Response(
                {"detail": "You cannot delete your own admin account."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        return super().destroy(request, *args, **kwargs)


@api_view(['GET'])
@permission_classes([AllowAny])
def get_dashboard_stats(request):
    print(f"Stats Request User: {request.user}") 
    print(f"Is Authenticated: {request.user.is_authenticated}")
    
    try:
        stats = {
            "teachers_count": Teacher.objects.count(),
            "students_count": Student.objects.count(),
            "subjects_count": Subject.objects.count(),
        }
        return Response(stats, status=status.HTTP_200_OK)
    except Exception as e:
        return Response(
            {"error": "Failed to fetch stats", "details": str(e)}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


class DepartmentViewSet(viewsets.ModelViewSet):
    queryset = Department.objects.all()
    serializer_class = DepartmentSerializer
    permission_classes = [IsAuthenticated]

class TeacherViewSet(viewsets.ModelViewSet):
    queryset = Teacher.objects.all().select_related('department')
    serializer_class = TeacherSerializer
   
    
    @action(detail=False, methods=['get'])
    def download_template(self, request):
        """Download Excel template for bulk teacher upload"""
        data = {
            'name': ['John Doe', 'Jane Smith'],
            'email': ['john@example.com', 'jane@example.com'],
            'department_name': ['Computer Science', 'Electronics']
        }
        df = pd.DataFrame(data)
        
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df.to_excel(writer, index=False, sheet_name='Teachers')
        output.seek(0)
        
        response = HttpResponse(
            output.read(),
            content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        response['Content-Disposition'] = 'attachment; filename=teachers_template.xlsx'
        return response
    
    @action(detail=False, methods=['post'])
    def bulk_upload(self, request):
        """
        Bulk upload teachers from CSV/Excel
        Expected columns: name, email, password, department_name
        """
        file = request.FILES.get('file')
        if not file:
            return Response({'error': 'No file provided'}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            if file.name.endswith('.csv'):
                df = pd.read_csv(file)
            elif file.name.endswith(('.xlsx', '.xls')):
                df = pd.read_excel(file)
            else:
                return Response({'error': 'Invalid file format. Use CSV or Excel'}, 
                              status=status.HTTP_400_BAD_REQUEST)
            
            created_count = 0
            errors = []
            
            for index, row in df.iterrows():
                try:
                    department = Department.objects.get(name=row['department_name'])
                    teacher_data = {
                        'name': row['name'],
                        'email': row['email'],
                        'password_hash': make_password(row.get('password', 'default123')),
                        'department': department
                    }
                    Teacher.objects.create(**teacher_data)
                    created_count += 1
                except Exception as e:
                    errors.append(f"Row {index + 1}: {str(e)}")
            
            return Response({
                'message': f'Successfully created {created_count} teachers',
                'errors': errors
            }, status=status.HTTP_201_CREATED)
            
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

class StudentViewSet(viewsets.ModelViewSet):
    queryset = Student.objects.all().select_related('department')
    serializer_class = StudentSerializer
    pagination_class = StudentPagination 
    
    @action(detail=False, methods=['get'])
    def download_template(self, request):
        """Download Excel template for bulk student upload"""
        data = {
            'prn': [2021001, 2021002],
            'name': ['Alice Johnson', 'Bob Williams'],
            'email': ['alice@example.com', 'bob@example.com'],
            'year': [2, 3],
            'department_name': ['Computer Science', 'Electronics']
        }
        df = pd.DataFrame(data)
        
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df.to_excel(writer, index=False, sheet_name='Students')
        output.seek(0)
        
        response = HttpResponse(
            output.read(),
            content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        response['Content-Disposition'] = 'attachment; filename=students_template.xlsx'
        return response
    
    @action(detail=False, methods=['post'])
    def bulk_upload(self, request):
        """
        Bulk upload students from CSV/Excel
        Expected columns: prn, name, email, password, year, department_name
        """
        file = request.FILES.get('file')
        if not file:
            return Response({'error': 'No file provided'}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            if file.name.endswith('.csv'):
                df = pd.read_csv(file)
            elif file.name.endswith(('.xlsx', '.xls')):
                df = pd.read_excel(file)
            else:
                return Response({'error': 'Invalid file format'}, status=status.HTTP_400_BAD_REQUEST)
            
            created_count = 0
            errors = []
            
            for index, row in df.iterrows():
                try:
                    department = Department.objects.get(name=row['department_name'])
                    student_data = {
                        'prn': int(row['prn']),
                        'name': row['name'],
                        'email': row['email'],
                        'password_hash': make_password(row.get('password', 'student123')),
                        'year': int(row['year']),
                        'department': department
                    }
                    Student.objects.create(**student_data)
                    created_count += 1
                except Exception as e:
                    errors.append(f"Row {index + 1}: {str(e)}")
            
            return Response({
                'message': f'Successfully created {created_count} students',
                'errors': errors
            }, status=status.HTTP_201_CREATED)
            
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

class SubjectViewSet(viewsets.ModelViewSet):
    queryset = Subject.objects.all()
    serializer_class = SubjectSerializer
    
    @action(detail=False, methods=['get'])
    def download_template(self, request):
        """Download Excel template for bulk subject upload"""
        data = {
            'code': ['CS101', 'CS102', 'EE201'],
            'name': ['Data Structures', 'Algorithms', 'Digital Electronics']
        }
        df = pd.DataFrame(data)
        
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df.to_excel(writer, index=False, sheet_name='Subjects')
        output.seek(0)
        
        response = HttpResponse(
            output.read(),
            content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        response['Content-Disposition'] = 'attachment; filename=subjects_template.xlsx'
        return response
    
    @action(detail=False, methods=['post'])
    def bulk_upload(self, request):
        """
        Bulk upload subjects from CSV/Excel
        Expected columns: code, name
        """
        file = request.FILES.get('file')
        if not file:
            return Response({'error': 'No file provided'}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            if file.name.endswith('.csv'):
                df = pd.read_csv(file)
            elif file.name.endswith(('.xlsx', '.xls')):
                df = pd.read_excel(file)
            else:
                return Response({'error': 'Invalid file format'}, status=status.HTTP_400_BAD_REQUEST)
            
            created_count = 0
            errors = []
            
            for index, row in df.iterrows():
                try:
                    Subject.objects.create(
                        code=row['code'],
                        name=row['name']
                    )
                    created_count += 1
                except Exception as e:
                    errors.append(f"Row {index + 1}: {str(e)}")
            
            return Response({
                'message': f'Successfully created {created_count} subjects',
                'errors': errors
            }, status=status.HTTP_201_CREATED)
            
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

class SubjectFromDeptViewSet(viewsets.ModelViewSet):
    queryset = SubjectFromDept.objects.all().select_related('department').prefetch_related('subject')
    serializer_class = SubjectFromDeptSerializer
    
    @action(detail=False, methods=['get'])
    def download_template(self, request):
        """Download Excel template for bulk subject-dept mapping upload"""
        data = {
            'department_name': ['Computer Science', 'Electronics'],
            'year': [2, 2],
            'semester': [3, 4],
            'subject_codes': ['CS101,CS102,CS103', 'EE201,EE202']
        }
        df = pd.DataFrame(data)
        
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df.to_excel(writer, index=False, sheet_name='SubjectFromDept')
            # Add instructions sheet
            instructions = pd.DataFrame({
                'Instructions': [
                    '1. department_name must match existing department',
                    '2. year should be 1, 2, 3, or 4',
                    '3. semester should be 1-8',
                    '4. subject_codes should be comma-separated (e.g., CS101,CS102)',
                    '5. All subject codes must exist in database'
                ]
            })
            instructions.to_excel(writer, index=False, sheet_name='Instructions')
        output.seek(0)
        
        response = HttpResponse(
            output.read(),
            content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        response['Content-Disposition'] = 'attachment; filename=subject_dept_template.xlsx'
        return response
    
    @action(detail=False, methods=['post'])
    def bulk_upload(self, request):
        """
        Bulk upload subject-dept mappings from CSV/Excel
        Expected columns: department_name, year, semester, subject_codes (comma-separated)
        """
        file = request.FILES.get('file')
        if not file:
            return Response({'error': 'No file provided'}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            if file.name.endswith('.csv'):
                df = pd.read_csv(file)
            elif file.name.endswith(('.xlsx', '.xls')):
                df = pd.read_excel(file)
            else:
                return Response({'error': 'Invalid file format'}, status=status.HTTP_400_BAD_REQUEST)
            
            created_count = 0
            errors = []
            
            for index, row in df.iterrows():
                try:
                    department = Department.objects.get(name=row['department_name'])
                    subject_codes = [code.strip() for code in str(row['subject_codes']).split(',')]
                    subjects = Subject.objects.filter(code__in=subject_codes)
                    
                    subject_dept, created = SubjectFromDept.objects.get_or_create(
                        department=department,
                        year=int(row['year']),
                        semester=int(row['semester'])
                    )
                    subject_dept.subject.set(subjects)
                    created_count += 1
                except Exception as e:
                    errors.append(f"Row {index + 1}: {str(e)}")
            
            return Response({
                'message': f'Successfully processed {created_count} records',
                'errors': errors
            }, status=status.HTTP_201_CREATED)
            
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

class StudentEnrollmentViewSet(viewsets.ModelViewSet):
    queryset = StudentEnrollment.objects.all().select_related('subject')
    serializer_class = StudentEnrollmentSerializer
    
    @action(detail=False, methods=['get'])
    def download_template(self, request):
        """Download Excel template for bulk student enrollment upload"""
        data = {
            'student_prn': [2021001, 2021001, 2021002],
            'subject_code': ['CS101', 'CS102', 'EE201']
        }
        df = pd.DataFrame(data)
        
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df.to_excel(writer, index=False, sheet_name='Enrollments')
            # Add instructions
            instructions = pd.DataFrame({
                'Instructions': [
                    '1. student_prn must exist in students table',
                    '2. subject_code must exist in subjects table',
                    '3. Each student-subject combination must be unique',
                    '4. One student can enroll in multiple subjects'
                ]
            })
            instructions.to_excel(writer, index=False, sheet_name='Instructions')
        output.seek(0)
        
        response = HttpResponse(
            output.read(),
            content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        response['Content-Disposition'] = 'attachment; filename=enrollments_template.xlsx'
        return response
    
    @action(detail=False, methods=['post'])
    def bulk_upload(self, request):
        """
        Bulk upload student enrollments from CSV/Excel
        Expected columns: student_prn, subject_code
        """
        file = request.FILES.get('file')
        if not file:
            return Response({'error': 'No file provided'}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            if file.name.endswith('.csv'):
                df = pd.read_csv(file)
            elif file.name.endswith(('.xlsx', '.xls')):
                df = pd.read_excel(file)
            else:
                return Response({'error': 'Invalid file format'}, status=status.HTTP_400_BAD_REQUEST)
            
            created_count = 0
            errors = []
            
            for index, row in df.iterrows():
                try:
                    subject = Subject.objects.get(code=row['subject_code'])
                    StudentEnrollment.objects.create(
                        student_prn=int(row['student_prn']),
                        subject=subject
                    )
                    StudentAttendancePercentage.objects.create(
                        student=Student.objects.get(prn=int(row['student_prn'])),
                        subject=subject,
                        present_count=0,
                        attendancePercentage=0.0
                    )
                    created_count += 1
                except Exception as e:
                    errors.append(f"Row {index + 1}: {str(e)}")
            
            return Response({
                'message': f'Successfully created {created_count} enrollments',
                'errors': errors
            }, status=status.HTTP_201_CREATED)
            
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
 
