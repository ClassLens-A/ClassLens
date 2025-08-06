from django.shortcuts import render
from django.http import HttpResponse
from deepface import DeepFace
from Home import models
import os


def embeddings(request, *args, **kwargs):
    directory = r"C:\Users\Vyom\OneDrive\Pictures\Screenshots"
    image_files = os.listdir(directory)[:5] 
    department = models.Department.objects.get(name="Department of Metallurgical and Materials Engineering")

    for idx, filename in enumerate(image_files):
        image_path = os.path.join(directory, filename)

        try:
            vector = DeepFace.represent(
                img_path=image_path,
                model_name='Facenet512',
                enforce_detection=True,
                detector_backend='retinaface'
            )
            embedding = vector[0]['embedding']
        except Exception as e:
            print(f"Error processing {filename}: {e}")
            continue
        student = models.Student.objects.create(
            prn = 8022053500 + idx,
            name = f"Student {idx + 1}",
            email = f"student{idx + 1}@example.ac.in",
            password_hash = "5704621d9514b3f64372e1ed8d827068f852951d4f9d5f58547d1b44611edf2b",
            year = 2025,
            department = department,
            face_embedding = embedding,
            notification_token = f"token{idx + 1}"
        )

        student.save()

    return HttpResponse("5 students added successfully")

