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
@shared_task
def evaluate_attendance(image_path, scheme, host):
    image = cv2.imread(image_path)
    if image is None:
        print("Error: Unable to load image. {image_path} may be incorrect.")
        return
    print(f'Image processing started for {image_path}')
    try:
        all_faces = DeepFace.extract_faces(
            img_path=image,
            detector_backend='retinaface',
            enforce_detection=True,
            align=True
        )
    except ValueError:
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
    
    os.remove(image_path)
    print(f'Image processing completed for {image_path}. Result saved at {file_path}')
    return