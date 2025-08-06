from django.contrib import admin

# Register your models here.

from .models import Student, Subject, Teacher, Department, Enrollment, ClassSession,SubjectFromDept

admin.site.register(Student)
admin.site.register(Teacher)
admin.site.register(Subject)

admin.site.register(Department)

admin.site.register(SubjectFromDept)
