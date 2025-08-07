from django.shortcuts import render
from rest_framework import  status
from rest_framework.decorators import  api_view,parser_classes
from rest_framework.response import Response
from .models import Department
from .serializers import DepartmentSerializer
from rest_framework.parsers import JSONParser,MultiPartParser,FormParser

@api_view(['GET'])
def getDepartments(request):
    if request.method == 'GET':
        departments = Department.objects.all()
        serializer = DepartmentSerializer(departments, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
    return Response({"detail": "Method not allowed"}, status=status.HTTP_405_METHOD_NOT_ALLOWED)


@api_view(['POST'])
@parser_classes([JSONParser,MultiPartParser,FormParser])
def registerNewStudent(request,*args,**kwargs):
    if request.method == 'POST':
        pass
    pass


@api_view(['POST'])
def registerNewTeacher(request,*args,**kwargs):
    if request.method == 'POST':
        pass


@api_view(['POST'])
def validateStudent(request,*args,**kwargs):
    if request.method == 'POST':
        pass


@api_view(['POST'])
def validateTeacher(request,*args,**kwargs):
    if request.method == 'POST':
        pass