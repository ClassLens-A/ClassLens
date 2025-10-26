from celery import shared_task
import matplotlib.pyplot as plt
import cv2
import os
from rest_framework.response import Response
from deepface import DeepFace
import uuid
from django.conf import settings
from django.http import request
import numpy as np
from pgvector.django import CosineDistance

from .models import Student, AttendanceRecord, ClassSession, StudentEnrollment

# @shared_task
# def evaluate_attendance(image_path, scheme, host):
  
#     image = cv2.imread(image_path)
#     if image is None:
#         print("Error: Unable to load image. {image_path} may be incorrect.")
#         return
#     print(f'Image processing started for {image_path}')
#     try:
#         all_faces = DeepFace.extract_faces(
#             img_path=image,
#             detector_backend='retinaface',
#             enforce_detection=True,
#             align=True
#         )
#     except ValueError:
#         return

#     for face_img in all_faces:
#         facial_area = face_img['facial_area']
#         x, y, w, h = facial_area['x'], facial_area['y'], facial_area['w'], facial_area['h']
#         cv2.rectangle(image, (x, y), (x + w, y + h), (0, 255, 0), 2)

#     plt.figure(figsize=(15, 10))
#     plt.imshow(cv2.cvtColor(image, cv2.COLOR_BGR2RGB))
#     plt.title(f"Detected {len(all_faces)} Faces", fontsize=20)
#     plt.axis('off')

#     unique_id = uuid.uuid4()
#     filename = f"detected_{unique_id}.jpeg"

#     output_dir = settings.BASE_DIR / 'media' / 'images'
#     output_dir.mkdir(parents=True, exist_ok=True)
    
#     file_path = output_dir / filename
#     plt.savefig(file_path, bbox_inches='tight', pad_inches=0)
#     plt.close()

#     image_url = f"{scheme}://{host}/media/images/{filename}"
    
#     os.remove(image_path)
#     return {
#         "num_faces": int(len(all_faces)),
#         "image_url": image_url
#     }

@shared_task
def evaluate_attendance(class_session_id: int):
    """
    Processes a class photo to identify enrolled students and mark attendance.
    """
    SIMILARITY_THRESHOLD = 0.70  # Match confidence must be > 70%

    try:
        session = ClassSession.objects.get(id=class_session_id)
        # image_path = session.attendance_photo.path
        image_path = r"D:\Final year project\WhatsApp Image 2025-09-28 at 11.59.53_0e980da4.jpg"
        enrolled_students = Student.objects.filter(
            studentenrollment__subject=session.subject
        ).only('prn', 'name', 'face_embedding')

        detected_faces = DeepFace.represent(
            img_path=image_path,
            model_name='ArcFace',
            detector_backend='retinaface',
            enforce_detection=True,
            align=True
        )

    except (ClassSession.DoesNotExist, ValueError) as e:
        print(f"Error: {e}")
        return f"Processing failed for session {class_session_id}. Reason: {str(e)}"
    
    present_student_prns = set()

    for face in detected_faces:
        embedding = face['embedding']

        best_match = enrolled_students.order_by(
            CosineDistance('face_embedding', embedding)
        ).first()

        if best_match:
            distance = best_match.face_embedding @ embedding
            similarity = (1 + distance) / 2  # Normalize to [0, 1]

            if similarity >= SIMILARITY_THRESHOLD and best_match.prn not in present_student_prns:
                present_student_prns.add(best_match.prn)

    present_records = [
        AttendanceRecord(class_session=session, student=student, status=True, marked_at=session.class_datetime)
        for student in enrolled_students if student.prn in present_student_prns
    ]
    AttendanceRecord.objects.bulk_create(present_records)

    enrolled_student_prns = set(enrolled_students.values_list('prn', flat=True))
    absent_student_prns = enrolled_student_prns - present_student_prns

    absent_records = [
        AttendanceRecord(class_session=session, student=student, status=False, marked_at=session.class_datetime)
        for student in enrolled_students if student.prn in absent_student_prns
    ]
    AttendanceRecord.objects.bulk_create(absent_records)

    if os.path.exists(image_path):
        os.remove(image_path)

    return f"Attendance processed for session {class_session_id}. Present: {len(present_student_prns)}, Absent: {len(absent_student_prns)}"