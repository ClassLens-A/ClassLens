from django.urls import path
from django.urls import include
from Home.views import getDepartments,registerNewStudent,registerNewTeacher,validateStudent,validateTeacher,send_otp,verify_otp,set_password

urlpatterns=[
    path('getDepartments/', getDepartments, name='get_departments'),
    path('registerNewStudent',registerNewStudent,name='register_new_student'),
    path('registerNewTeacher',registerNewTeacher,name='register_new_teacher'),
    path('validateStudent',validateStudent,name='validate_student'),
    path('validateTeacher',validateTeacher,name='validate_teacher'),
    path('sendOtp',send_otp,name='send_otp'),
    path('verifyOtp',verify_otp,name='verify_otp'),
    path('setPassword',set_password,name='set_password'),    
]