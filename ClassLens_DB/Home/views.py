from rest_framework import status
from rest_framework.decorators import api_view, parser_classes
from deepface import DeepFace
from PIL import Image
import numpy as np
from rest_framework.response import Response
from .models import Department, Student, Teacher, SubjectFromDept, AttendanceRecord
from django.db.models import Count, Q
from .serializers import DepartmentSerializer,SubjectSerializer
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
import cv2
import matplotlib.pyplot as plt
from azure.communication.email import EmailClient
import uuid

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
            return Response({"subjects": subjects}, status=status.HTTP_200_OK)
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
@parser_classes([MultiPartParser])
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
        student_id = request.data.get("student_id")

        if student_id is None:
            return Response(
                {"detail": "student_id is required"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Aggregate attendance per subject
        attendance_data = (
            AttendanceRecord.objects
            .filter(student_id=student_id)
            .values('class_session__subject__id', 'class_session__subject__name')
            .annotate(
                total_classes=Count('id'),
                attended_classes=Count('id', filter=Q(status=True))
            )
        )

        result = []
        for record in attendance_data:
            total = record['total_classes']
            attended = record['attended_classes']
            percentage = round((attended / total) * 100, 2) if total > 0 else 0

            result.append({
                "subject_id": record['class_session__subject__id'],
                "subject_name": record['class_session__subject__name'],
                "total_classes": total,
                "attended_classes": attended,
                "attendance_percentage": percentage
            })

        return Response(
            {"student_id": student_id, "attendance": result},
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
def take_attendance(request, *args, **kwargs):
    photo = request.FILES.get("photo")

    if not photo:
        return Response({"error": "No photo provided."}, status=400)

    file_bytes = np.asarray(bytearray(photo.read()), dtype=np.uint8)
    image = cv2.imdecode(file_bytes, cv2.IMREAD_COLOR)

    try:
        all_faces = DeepFace.extract_faces(
            img_path=image,
            detector_backend='retinaface',
            enforce_detection=True,
            align=True
        )
    except ValueError:
        return Response({"error": "No faces detected in the image."}, status=400)

    for face_img in all_faces:
        facial_area = face_img['facial_area']
        x, y, w, h = facial_area['x'], facial_area['y'], facial_area['w'], facial_area['h']
        cv2.rectangle(image, (x, y), (x + w, y + h), (0, 255, 0), 2)

    plt.figure(figsize=(15, 10))
    plt.imshow(cv2.cvtColor(image, cv2.COLOR_BGR2RGB))
    plt.title(f"Detected {len(all_faces)} Faces", fontsize=20)
    plt.axis('off')

    unique_id = uuid.uuid4()
    filename = f"detected_{unique_id}.jpeg"

    output_dir = settings.BASE_DIR / 'media' / 'images'
    output_dir.mkdir(parents=True, exist_ok=True)
    
    file_path = output_dir / filename
    plt.savefig(file_path, bbox_inches='tight', pad_inches=0)
    plt.close()

    image_url = f"{request.scheme}://{request.get_host()}/media/images/{filename}"

    return Response({
        "facesDetected": len(all_faces),
        "url": image_url
    }, status=200)