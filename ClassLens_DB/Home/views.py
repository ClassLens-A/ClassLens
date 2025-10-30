from rest_framework import status
import string
from django.db.models import F
from rest_framework.decorators import api_view, parser_classes
from deepface import DeepFace
from PIL import Image
import numpy as np
from rest_framework.response import Response
from .models import Department, Student, Teacher, SubjectFromDept, AttendanceRecord, StudentEnrollment,TeacherSubject, ClassSession, Subject
from django.db.models import Count, Q
from .serializers import DepartmentSerializer,SubjectSerializer
from rest_framework.parsers import MultiPartParser
from django.contrib.auth.hashers import make_password, check_password
from django.shortcuts import get_object_or_404
import traceback
import random
from datetime import datetime
from django.core.cache import cache
from django.core.mail import send_mail
from django.conf import settings
import environ
import os
from pathlib import Path
import cv2
import matplotlib.pyplot as plt
from azure.communication.email import EmailClient
import uuid
from .tasks import evaluate_attendance
from django.core.files.storage import default_storage
from celery.result import AsyncResult
from pgvector.django import CosineDistance


BASE_DIR = Path(__file__).resolve().parent.parent

env = environ.Env()
environ.Env.read_env(os.path.join(BASE_DIR, ".env"))


@api_view(["GET"])
def getDepartments(request):
    if request.method == "GET":
        departments = Department.objects.all()
        serializer = DepartmentSerializer(departments, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
    return Response(
        {"detail": "Method not allowed"}, status=status.HTTP_405_METHOD_NOT_ALLOWED
    )


@api_view(["POST"])
def registerNewTeacher(request, *args, **kwargs):
    data = request.data

    required_fields = ["name", "email", "password", "departmentID"]
    if not all(field in data for field in required_fields):
        return Response(
            {"error": "Missing one or more required fields."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    try:
        if Teacher.objects.filter(email=data["email"]).exists():
            return Response(
                {"error": "Teacher with this email already exists."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        department = get_object_or_404(Department, id=data["departmentID"])
        teacher = Teacher.objects.create(
            name=data["name"],
            email=data["email"],
            password_hash=make_password(data["password"]),
            department=department,
        )
        return Response(
            {"message": "Teacher registered successfully"},
            status=status.HTTP_201_CREATED,
        )
    except Exception as e:
        traceback.print_exc()
        return Response(
            {"detail": "Method not allowed"}, status=status.HTTP_405_METHOD_NOT_ALLOWED
        )


@api_view(["POST"])
def validateStudent(request, *args, **kwargs):
    prn = request.data.get("prn")
    password = request.data.get("password")

    if prn is None or password is None:
        return Response(
            {"detail": "PRN and Password are required"},
            status=status.HTTP_400_BAD_REQUEST,
        )

    try:
        student = Student.objects.get(prn=prn)
        if not check_password(password, student.password_hash):
            return Response(
                {"detail": "Invalid password"}, status=status.HTTP_400_BAD_REQUEST
            )
        else:
            return Response(
                {"message": "Student validated successfully", "student_id": student.id, 'student_name': student.name},
                status=status.HTTP_200_OK,
            )
    except Student.DoesNotExist:
        return Response(
            {"detail": "Invalid PRN or password"}, status=status.HTTP_400_BAD_REQUEST
        )
    except Exception as e:
        traceback.print_exc()
        return Response(
            {"detail": "Method not allowed"},
            status=status.HTTP_405_METHOD_NOT_ALLOWED,
        )


@api_view(["POST"])
def validateTeacher(request, *args, **kwargs):
    email = request.data.get("email")
    password = request.data.get("password")

    if email is None or password is None:
        return Response(
            {"detail": "Email and Password are required"},
            status=status.HTTP_400_BAD_REQUEST,
        )
    try:

        teacher = Teacher.objects.get(email=email)
        if teacher.password_hash is None:
            return Response(
                {"detail": "User not registered"}, status=status.HTTP_400_BAD_REQUEST
            )
        if not check_password(password, teacher.password_hash):
            return Response(
                {"detail": "Invalid password"}, status=status.HTTP_400_BAD_REQUEST
            )
        else:
            return Response(
                {"message": "Teacher validated successfully", "teacher_id": teacher.id, 'teacher_name': teacher.name},
                status=status.HTTP_200_OK,
            )
    except Teacher.DoesNotExist:
        return Response(
            {"detail": "Invalid email or user not registered"},
            status=status.HTTP_400_BAD_REQUEST,
        )
    except Exception as e:
        traceback.print_exc()
        return Response(
            {"detail": "Method not allowed"}, status=status.HTTP_405_METHOD_NOT_ALLOWED
        )

@api_view(["POST"])
def get_subject_details(request, *args, **kwargs):
    if request.method == "POST":
        department_name = request.data.get("department")
        year = request.data.get("year")
        semester = request.data.get("semester")
        try:
            department = get_object_or_404(Department, name=department_name)
            subject_from_dept = get_object_or_404(
                SubjectFromDept, department=department, year=year, semester=semester
            )
            subjects = subject_from_dept.subject.all()
            subjects = SubjectSerializer(subjects, many=True).data
            return Response({"subjects": subjects,"message":"subject details"}, status=status.HTTP_200_OK)
        except Exception as e:
            traceback.print_exc()
            return Response(
                {"detail": "Something went wrong"},
                status=status.HTTP_405_METHOD_NOT_ALLOWED,
            )


@api_view(["POST"])
def send_otp(request, *args, **kwargs):
    try:
        email = request.data.get("email")
        otp = random.randint(1000, 9999)

        if email is None:
            return Response(
                {"detail": "Email is required"}, status=status.HTTP_400_BAD_REQUEST
            )
        
        teacher = Teacher.objects.filter(email=email).first()
        student = None if teacher else Student.objects.filter(email=email).first()

        if teacher is not None:
            if teacher.password_hash is not None:
                print("Password is not None")
                return Response(
                    {"detail": "Email is already registered"},
                    status=status.HTTP_400_BAD_REQUEST,
                )

        cache.set(email, otp, 600)

        print('OPT:', otp)

        display_name = teacher.name if teacher else student.name

        if not (teacher or student):
            return Response(
                {"detail": "No user found with this email"},
                status=status.HTTP_404_NOT_FOUND,
            )
            
        

        subject = "Your ClassLens OTP Verification Code"

        plain_message = f"""
        Hello,

        Your One Time Password for ClassLens is: {otp}

        This code is valid for 10 minutes. For your security, please do not share it with anyone.

        If you did not request this, you can safely ignore this email.

        Thank you,
        The ClassLens Team
        """
        
        html_message = f"""
        <p>Hello {display_name},</p>
        <p>Your One Time Password for ClassLens is: <strong>{otp}</strong></p>
        <p>This code is valid for <strong>10 minutes</strong>. For your security, please do not share it with anyone.</p>
        <p>If you did not request this, you can safely ignore this email.</p>
        <br>
        <p>Thank you,<br>
        <strong>The ClassLens Team</strong></p>
        """

        email_client = EmailClient.from_connection_string(env("CONNECTION_STRING"))

        message = {
            "content": {
                "subject": subject,
                "plainText": plain_message,
                "html": html_message,
            },
            "recipients": {"to": [{"address": email, "displayName": display_name}]},
            "senderAddress": "DoNotReply@5e413bf2-7085-4332-af0d-80905f679aac.azurecomm.net",
        }

        poller = email_client.begin_send(message)
        if poller.result()["status"] == "Succeeded":
            return Response({"message": "OTP sent successfully"}, status=200)
        else:
            return Response({"message": "Failed to send OTP"}, status=500)

    except Exception as e:
        traceback.print_exc()
        return Response(
            {"detail": "Method not allowed"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


@api_view(["POST"])
def verify_email(request, *args, **kwargs):
    try:
        email = request.data.get("email")
        if email is None:
            return Response(
                {"detail": "Email is required"}, status=status.HTTP_400_BAD_REQUEST
            )
        if not (Teacher.objects.filter(email=email).exists() or Student.objects.filter(email=email).exists()):
            return Response(
                {"detail": "No user found with this email"},
                status=status.HTTP_404_NOT_FOUND,
            )
        
        teacher = Teacher.objects.filter(email=email).first()
        student = None if teacher else Student.objects.filter(email=email).first()

        if teacher is not None:
            if teacher.password_hash is not None:
                print("Password is not None")
                return Response(
                    {"detail": "Email is already registered! Try login instead"},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            else:
                return Response({"message": "Email verified successfully"}, status=200)
        else:
            if student.password_hash is not None:
                print("Password is not None")
                return Response(
                    {"detail": "Email is already registered"},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            else:
                 return Response({"message": "Email verified successfully"}, status=200)

    except Exception as e:
        traceback.print_exc()
        return Response(
            {"detail": "Method not allowed"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


@api_view(["POST"])
def verify_prn(request, *args, **kwargs):
    try:
        prn = request.data.get("prn")
        if prn is None:
            return Response(
                {"detail": "PRN is required"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        student = Student.objects.filter(prn=prn).first()
        if not student:
            return Response(
                {"detail": "No user found with this PRN"},
                status=status.HTTP_404_NOT_FOUND,
            )

        if student.password_hash is not None:
            print("Password is not None")
            return Response(
                {"detail": "PRN is already registered! Try login instead"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        else:
            return Response({
                "message": "PRN verified successfully",
                "email": student.email
            }, status=200)
    except Exception as e:
        traceback.print_exc()
        return Response(
            {"detail": "Method not allowed"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


@api_view(["POST"])
def verify_otp(request, *args, **kwargs):
    try:
        email = request.data.get("email")
        otp = request.data.get("otp")
        if email is None or otp is None:
            return Response(
                {"detail": "Email and OTP are required"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        cached_otp = cache.get(email)

        if cached_otp is None or cached_otp != int(otp):
            return Response(
                {"detail": "Invalid or expired OTP"}, status=status.HTTP_400_BAD_REQUEST
            )
        cache.delete(email)
        return Response({"message": "OTP verified successfully"}, status=200)

    except Exception as e:
        traceback.print_exc()
        return Response(
            {"detail": "Method not allowed"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )

@api_view(["POST"])
def set_password(request, *args, **kwargs):
    try:
        password = request.data.get("password")
        if request.data.get("email"):
            email=request.data.get("email")
            if email is None or password is None:
                return Response(
                    {"detail": "Email and Password are required"},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            teacher = Teacher.objects.filter(email=email).first()
            if teacher : 
                teacher.password_hash = make_password(password)
                teacher.save()
                print("Teacher password set successfully")
                return Response({"message": "Teacher password set successfully"}, status=200)
            else : 
                return Response({"detail": "No Teacher found with this email"}, status=status.HTTP_404_NOT_FOUND)
        
        elif request.data.get("prn"):
            prn=request.data.get("prn")
            if prn is None or password is None:
                return Response(
                    {"detail": "PRN and Password are required"},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            
            student = Student.objects.filter(prn=prn).first()
            if student : 
                student.password_hash = make_password(password)
                try : 
                    student.face_embedding=registerNewStudent(request.FILES.get("photo"))
                except ValueError as ve :
                    return Response({"error": "Face Not Detected, Upload A New Image"}, status=status.HTTP_400_BAD_REQUEST)
                student.save()
                print("Student password set successfully")
                return Response({"message": "Student password set successfully"}, status=200)
            else:
                return Response({"detail": "No Student found with this prn"}, status=status.HTTP_404_NOT_FOUND)

    except Exception as e:
        traceback.print_exc()
        return Response(
            {"detail": "An error occurred while updating the password"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )
    
def registerNewStudent(photo):

    if not photo:
        return Response(
            {"error": "No photo uploaded"}, status=status.HTTP_400_BAD_REQUEST
        )

    try:
        image = Image.open(photo)
        image = image.convert("RGB")
        img_arr = np.array(image)
        image_embedding = DeepFace.represent(
            img_path=img_arr,
            model_name="Facenet512",
            detector_backend="retinaface",
            enforce_detection=True,
        )[0]["embedding"]

        return image_embedding
    except ValueError as ve:
        return ValueError(ve)

@api_view(["POST"])
def get_student_attendance(request, *args, **kwargs):
    try:
        subject_id = request.data.get("subject_id")

        if subject_id is None:
            return Response(
                {"detail": "subject_id is required"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        
        data = StudentEnrollment.objects.filter(subject_id=subject_id).values_list('student_prn',flat=True)
 
        student_data = Student.objects.filter(
            prn__in=data
        ).annotate(
            total_classes=Count(
                'attendancerecord',
                filter=Q(attendancerecord__class_session__subject_id=subject_id)
            ),
            attended_classes=Count(
                'attendancerecord',
                filter=Q(attendancerecord__class_session__subject_id=subject_id, 
                           attendancerecord__status=True)
            )
        )
        result = []
        for student in student_data:

            total = student.total_classes
            attended = student.attended_classes
            percentage = round((attended / total) * 100, 2) if total > 0 else 0.0

            result.append({
                "student_id": student.id,
                "student_name": student.name,
                "total_classes": total,
                "attended_classes": attended,
                "attendance_percentage": percentage
            })

        return Response(
            {"attendance": result},
            status=status.HTTP_200_OK,
        )

    except Exception as e:
        traceback.print_exc()
        return Response(
            {"detail": "Something went wrong"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )

@api_view(["POST"])
@parser_classes([MultiPartParser])
def mark_attendance(request, *args, **kwargs):
    """
    API endpoint to start an attendance session.
    Expects form-data with: photo, subject_id, teacher_id, department_id, year
    """
    photo = request.FILES.get("photo")
    subject_id = request.data.get("subjectID")
    teacher_id = request.data.get("teacherID")
    departmentName = request.data.get("departmentName")
    year = request.data.get("year")

    if not all([photo, subject_id, teacher_id, departmentName, year]):
        return Response({"error": "Missing required fields (photo, subject_id, teacher_id, department_id, year)."}, status=400)

    try:
        class_session = ClassSession.objects.create(
            department = get_object_or_404(Department, name=departmentName),
            year = year,
            subject = get_object_or_404(Subject, id=subject_id),
            teacher = get_object_or_404(Teacher, id=teacher_id),
            class_datetime = datetime.now(),
            attendance_photo = photo
        )

        task = evaluate_attendance.delay(class_session.attendance_photo.path, class_session.id,request.scheme, request.get_host())

        return Response({
            "message": "Attendance processing started. You will be notified once it's done.",
            "task_id": task.id
        }, status=202)
    
    except Exception as e:
        traceback.print_exc()
        return Response({"error": "Failed to start attendance session."}, status=500)

    # file_bytes = np.asarray(bytearray(photo.read()), dtype=np.uint8)
    # image = cv2.imdecode(file_bytes, cv2.IMREAD_COLOR)

    # task = evaluate_attendance.delay(absolute_file_path, request.scheme, request.get_host())
    # print(task.id)
    # return Response({
    #     "message": "Attendance processing started. You will be notified once it's done.",
    #     "task_id": task.id
    # }, status=202)

@api_view(["POST"])
def teacher_subjects(request,*args, **kwargs):
    teacher_id = request.data.get("teacher_id")
    if not teacher_id:
        return Response({"error": "Teacher ID is required"}, status=400)
    try:
        subjects = TeacherSubject.objects.filter(teacher_id=teacher_id).values(
            'subject__id', 
            'subject__code', 
            'subject__name'
        )

        clean_subjects = [
            {
                'id': s['subject__id'],
                'code': s['subject__code'],
                'name': s['subject__name'],
                'strength': StudentEnrollment.objects.filter(subject_id=s['subject__id']).count()
            }
            for s in subjects
        ]
        return Response({"subjects": clean_subjects}, status=200)
    except Exception as e:
        traceback.print_exc()
        return Response(
            {"detail": "Something went wrong"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )

@api_view(["POST"])
def get_absentees_list(request, *args, **kwargs):
    class_session_id = request.data.get("class_session_id")
    if not class_session_id:
        return Response({"error": "Class Session ID is required"}, status=400)
    
    absentees_students=AttendanceRecord.objects.filter(class_session_id=class_session_id, status=False).annotate(student_id=F('student__id'),student_name=F('student__name'),student_prn=F('student__prn')).values('student_id', 'student_name', 'student_prn')

    return Response({"students": absentees_students}, status=status.HTTP_200_OK)

@api_view(["POST"])
def change_attendance(request, *args, **kwargs):
    class_session_id = request.data.get("class_session_id")
    student_list=request.data.get("student_list")

    for student_id in student_list:
        attendance_record = AttendanceRecord.objects.filter(class_session_id=class_session_id, student_id=student_id).first()
        if attendance_record:
            attendance_record.status = True
            attendance_record.save()
    return Response(status=status.HTTP_200_OK)

@api_view(["GET"])
def attendance_status(request, task_id,*args, **kwargs):

    if not task_id:
        return Response({"error": "Task ID is required"}, status=400)

    task = AsyncResult(task_id)

    if task.successful():
        return Response({"status": task.status, "result": task.result}, status=200)
    elif task.failed():
        return Response({"status": task.status, "result": task.result}, status=500)
    
    return Response({"status": task.status,"result":{"num_faces":0,"image_url":""}}, status=202)