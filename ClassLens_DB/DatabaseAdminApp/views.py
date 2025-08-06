from django.shortcuts import render
from django.http import HttpResponse
from deepface import DeepFace
from Home import models

# Create your views here.

def embeddings(request,*args,**kwargs):
    path = r"C:\Users\YASH SOLANKI\Untitled Folder\1 (4).png"
    vector = DeepFace.represent(img_path=path, model_name='Facenet512', enforce_detection=True,detector_backend='retinaface')
    vector = vector[0]['embedding']
    model=models.Student.objects.create(
        prn = 8022053514,
        name = "Joe Jams",
        email = "q2o8o@example.ac.in",
        password_hash = "5704621d9514b3f64372e1ed8d827068f852951d4f9d5f58547d1b44611edf2b",
        year = 2025,
        department = models.Department.objects.get(name="Department of Metallurgical and Materials Engineering"),
        face_embedding = vector,
         notification_token = "token3"
    )

    model.save()
    return HttpResponse("success")

def compare(request,*args,**kwargs):

    path = r""

