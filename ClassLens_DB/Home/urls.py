from django.urls import path
from django.urls import include
from Home.views import getDepartments

urlpatterns=[
    path('getDepartments/', getDepartments, name='get_departments'),
]