from rest_framework import  status
from rest_framework.decorators import  api_view,parser_classes
from deepface import DeepFace
from PIL import Image
import numpy as np
from rest_framework.response import Response
from .models import Department,Student,Teacher
from .serializers import DepartmentSerializer
from rest_framework.parsers import MultiPartParser
from django.shortcuts import get_object_or_404
import traceback

@api_view(['GET'])
def getDepartments(request):
    if request.method == 'GET':
        departments = Department.objects.all()
        serializer = DepartmentSerializer(departments, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
    return Response({"detail": "Method not allowed"}, status=status.HTTP_405_METHOD_NOT_ALLOWED)


@api_view(['POST'])
@parser_classes([MultiPartParser])
def registerNewStudent(request,*args,**kwargs):
    if request.method == 'POST':
        photo=request.FILES.get('photo')

        if not photo:
            return Response({'error': 'No photo uploaded'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            print("Received photo:", photo.name)
            image=Image.open(photo)
            image=image.convert('RGB')
            img_arr=np.array(image)
            image_embedding = DeepFace.represent(img_path =img_arr,model_name = 'Facenet512',detector_backend = 'retinaface')[0]["embedding"]
            department=get_object_or_404(Department,name=request.POST.get('department'))  

            student=Student.objects.create(
                name=request.POST.get('name'),
                prn=request.POST.get('prn'),
                email=request.POST.get('email'),
                year=request.POST.get('year'),
                password_hash=request.POST.get('password_hash'),
                department=department,
                face_embedding=image_embedding
            )
            student.save()
            return Response({'message': 'Student registered successfully'}, status=status.HTTP_201_CREATED)
        except Exception as e:
            traceback.print_exc() 
            return Response({"detail": "Method not allowed"}, status=status.HTTP_405_METHOD_NOT_ALLOWED)


@api_view(['POST'])
def registerNewTeacher(request,*args,**kwargs):
    if request.method == 'POST':
        try : 
            teacher=Teacher.objects.create(
                name=request.POST.get('name'),
                email=request.POST.get('email'),
                password_hash=request.POST.get('password_hash'),
                department=get_object_or_404(Department,name=request.POST.get('department'))
            )
            teacher.save()
            return Response({'message': 'Teacher registered successfully'}, status=status.HTTP_201_CREATED)
        except Exception as e:
            traceback.print_exc() 
            return Response({"detail": "Method not allowed"}, status=status.HTTP_405_METHOD_NOT_ALLOWED)


@api_view(['POST'])
def validateStudent(request,*args,**kwargs):
    if request.method == 'POST':
        prn= request.data.get('prn')
        password_hash = request.data.get('password_hash')
        try:
            student = Student.objects.get(prn=prn, password_hash=password_hash)
            return Response({'message': 'Student validated successfully', 'student_id': student.id}, status=status.HTTP_200_OK)
        except Student.DoesNotExist:
            return Response({'error': 'Invalid PRN or password'}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            traceback.print_exc()
            return Response({"detail": "Method not allowed"}, status=status.HTTP_405_METHOD_NOT_ALLOWED)


@api_view(['POST'])
def validateTeacher(request,*args,**kwargs):
    if request.method == 'POST':
        email = request.data.get('email')
        password_hash = request.data.get('password_hash')
        try:
            teacher = Teacher.objects.get(email=email, password_hash=password_hash)
            return Response({'message': 'Teacher validated successfully', 'teacher_id': teacher.id}, status=status.HTTP_200_OK)
        except Teacher.DoesNotExist:
            return Response({'error': 'Invalid email or password'}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            traceback.print_exc()
            return Response({"detail": "Method not allowed"}, status=status.HTTP_405_METHOD_NOT_ALLOWED)