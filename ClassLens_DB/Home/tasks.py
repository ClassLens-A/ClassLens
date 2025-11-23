from celery import shared_task
import matplotlib.pyplot as plt
import cv2
import os
import shutil
from codeformer.app import inference_app
from rest_framework.response import Response
from deepface import DeepFace
import uuid
from django.conf import settings
from django.http import request
import numpy as np
from pgvector.django import CosineDistance

from .models import Student, AttendanceRecord, ClassSession, StudentEnrollment

@shared_task
def evaluate_attendance(image_path,class_session_id:int,scheme, host):

    image = cv2.imread(image_path)
    session = ClassSession.objects.get(id=class_session_id)

    restored_filename = f"restored_{uuid.uuid4()}.jpeg"
    restored_group_photo_path = settings.MEDIA_ROOT / 'images' / restored_filename
    
    (settings.MEDIA_ROOT / 'images').mkdir(parents=True, exist_ok=True)

    if image is None:
        print("Error: Unable to load image. {image_path} may be incorrect.")
        return
    print(f'Image processing started for {image_path}')

    try: 
        path=inference_app(
            image=image_path,
            background_enhance=False,
            face_upsample=True,
            upscale=2,
            codeformer_fidelity=0.7 
        )
        if not path or not os.path.exists(path):
            raise ValueError(f"CodeFormer failed to produce an output file for {image_path}")

        shutil.move(path, restored_group_photo_path)
        restored_group_photo = str(restored_group_photo_path)

        image=cv2.imread(restored_group_photo)
    except Exception as e:
        print(f"Error during CodeFormer enhancement: {e}")
        # If enhancement fails, we can't continue.
        return 

    try:
        all_faces = DeepFace.represent(
            img_path=restored_group_photo,
            model_name='ArcFace',
            detector_backend='retinaface',
            enforce_detection=True,
            align=True
        )
    except ValueError:
        print("Error: Unable to detect faces in the image.")
        return

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

    image_url = f"{scheme}://{host}/media/images/{filename}"
    
    SIMILARITY_THRESHOLD = 0.70 

    try:    
        enrolled_prns = StudentEnrollment.objects.filter(
            subject=session.subject
        ).values_list('student_prn', flat=True)

        all_enrolled_students = Student.objects.filter(prn__in=enrolled_prns)

        valid_students = all_enrolled_students.filter(
            face_embedding__isnull=False
        ).only('prn', 'name', 'face_embedding')

    except (ClassSession.DoesNotExist, ValueError) as e:
        print(f"Error: {e}")
        return f"Processing failed for session {class_session_id}. Reason: {str(e)}"
    
    present_student_prns = set()

    for face in all_faces:
        embedding = face['embedding']

        best_match = valid_students.annotate(
            distance=CosineDistance('face_embedding', embedding)
        ).order_by('distance').first()

        if best_match:
            similarity = 1 - best_match.distance

            if similarity >= SIMILARITY_THRESHOLD and best_match.prn not in present_student_prns:
                present_student_prns.add(best_match.prn)

    present_records = [
        AttendanceRecord(class_session=session, student=student, status=True, marked_at=session.class_datetime)
        for student in all_enrolled_students if student.prn in present_student_prns
    ]
    AttendanceRecord.objects.bulk_create(present_records)

    # enrolled_student_prns = set(all_enrolled_students.values_list('prn', flat=True))
    enrolled_student_prns = set(enrolled_prns)
    absent_student_prns = enrolled_student_prns - present_student_prns

    absent_records = [
        AttendanceRecord(class_session=session, student=student, status=False, marked_at=session.class_datetime)
        for student in all_enrolled_students if student.prn in absent_student_prns
    ]
    AttendanceRecord.objects.bulk_create(absent_records)

    return {
        "num_faces": int(len(all_faces)),
        "image_url": image_url,
        "class_session_id": class_session_id,
        "present_count": len(present_student_prns),
        "absent_count": len(absent_student_prns),
        "subject": session.subject.name
    }