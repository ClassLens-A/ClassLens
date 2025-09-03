from rest_framework import status
from rest_framework.decorators import api_view, parser_classes
from deepface import DeepFace
from PIL import Image
import numpy as np
from rest_framework.response import Response
from .models import Department, Student, Teacher, SubjectFromDept
from .serializers import DepartmentSerializer
from rest_framework.parsers import MultiPartParser
from django.contrib.auth.hashers import make_password, check_password
from django.shortcuts import get_object_or_404
import traceback
import random
from django.core.cache import cache
from django.core.mail import send_mail
from django.conf import settings
import environ
import os
from pathlib import Path
from azure.communication.email import EmailClient

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
@parser_classes([MultiPartParser])
def registerNewStudent(request, *args, **kwargs):
    if request.method == "POST":
        photo = request.FILES.get("photo")

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
            department = get_object_or_404(
                Department, name=request.POST.get("department")
            )

            student = Student.objects.create(
                name=request.POST.get("name"),
                prn=request.POST.get("prn"),
                email=request.POST.get("email"),
                year=request.POST.get("year"),
                password_hash=request.POST.get("password_hash"),
                department=department,
                face_embedding=image_embedding,
            )
            student.save()
            return Response(
                {"message": "Student registered successfully"},
                status=status.HTTP_201_CREATED,
            )
        except ValueError as ve:
            return Response(
                {"error": str(ve) + "Invalid photo uploaded"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        except Exception as e:
            traceback.print_exc()
            return Response(
                {"Error": str(e)}, status=status.HTTP_405_METHOD_NOT_ALLOWED
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
    if request.method == "POST":
        prn = request.data.get("prn")
        password_hash = request.data.get("password_hash")
        try:
            student = Student.objects.get(prn=prn, password_hash=password_hash)
            return Response(
                {"message": "Student validated successfully", "student_id": student.id},
                status=status.HTTP_200_OK,
            )
        except Student.DoesNotExist:
            return Response(
                {"error": "Invalid PRN or password"}, status=status.HTTP_400_BAD_REQUEST
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
        if not check_password(password, teacher.password_hash):
            return Response(
                {"error": "Invalid password"}, status=status.HTTP_400_BAD_REQUEST
            )
        else:
            return Response(
                {"message": "Teacher validated successfully", "teacher_id": teacher.id},
                status=status.HTTP_200_OK,
            )
    except Teacher.DoesNotExist:
        return Response(
            {"error": "Invalid email or user not registered"},
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
            subject_list = [
                {"code": subject.code, "name": subject.name} for subject in subjects
            ]
            return Response({"subjects": subject_list}, status=status.HTTP_200_OK)
        except Exception as e:
            traceback.print_exc()
            return Response(
                {"detail": "Method not allowed"},
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

        cache.set(email, otp, 120)
        
        teacher = Teacher.objects.filter(email=email).first()
        student = None if teacher else Student.objects.filter(email=email).first()
        
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

        This code is valid for 2 minutes. For your security, please do not share it with anyone.

        If you did not request this, you can safely ignore this email.

        Thank you,
        The ClassLens Team
        """
        
        html_message = f"""
        <p>Hello {display_name},</p>
        <p>Your One Time Password for ClassLens is: <strong>{otp}</strong></p>
        <p>This code is valid for <strong>2 minutes</strong>. For your security, please do not share it with anyone.</p>
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
        email = request.data.get("email")
        password = request.data.get("password")
        if email is None or password is None:
            return Response(
                {"detail": "Email and Password are required"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        teacher = Teacher.objects.get(email=email)
        teacher.password_hash = make_password(password)
        teacher.save()
        return Response({"message": "password set successfully"}, status=200)

    except Exception as e:
        traceback.print_exc()
        return Response(
            {"detail": "Method not allowed"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )
