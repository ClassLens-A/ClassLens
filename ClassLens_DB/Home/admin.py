from django.contrib import admin

# Register your models here.

from .models import Student, Subject, Teacher, Department, ClassSession, SubjectFromDept, Teacher_Subject, Student_Enrollment

admin.site.register(Student)
admin.site.register(Teacher)
admin.site.register(Subject)
admin.site.register(Teacher_Subject)
admin.site.register(Student_Enrollment)

admin.site.register(Department)

admin.site.register(SubjectFromDept)
