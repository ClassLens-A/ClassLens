from django.shortcuts import render
from rest_framework import api_view, status
from rest_framework.response import Response
from .models import Department
from .serializers import DepartmentSerializer

@api_view(['GET'])
def getDepartments(request):
    if request.method == 'GET':
        departments = Department.objects.all()
        serializer = DepartmentSerializer(departments, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
    return Response({"detail": "Method not allowed"}, status=status.HTTP_405_METHOD_NOT_ALLOWED)