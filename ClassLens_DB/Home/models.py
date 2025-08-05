from django.db import models
from pgvector.django import VectorField, IvfflatIndex, HnswIndex

class Department(models.Model):
    name = models.TextField(unique=True, null=False)
    
    def __str__(self):
        return self.name

class Teacher(models.Model):
    name = models.TextField(null=False)
    email = models.EmailField(unique=True, null=False)
    password_hash = models.TextField(null=False)
    department = models.ForeignKey(
        Department, 
        on_delete=models.CASCADE, 
    )

    def __str__(self):
        return self.name
    
class Student(models.Model):
    prn = models.IntegerField(unique=True, null=False)
    name = models.TextField(null=False)
    email = models.EmailField(unique=True, null=False)
    password_hash = models.TextField(null=False)
    year = models.IntegerField(null=False)
    department = models.ForeignKey(
        Department, 
        on_delete=models.CASCADE, 
    )
    face_embedding = VectorField(dimensions=512, null=True, blank=True)
    notification_token = models.TextField(null=True, blank=True)
    class Meta:
        indexes = [
           HnswIndex(
                name='student_face_embedding_idx',
                fields=['face_embedding'],
                m=16,                 # number of bi‐directional links per node
                ef_construction=200,  # controls recall vs build time
                opclasses=['vector_l2_ops']
            ),
        ]
    def __str__(self):
        return f"{self.name} ({self.prn})"
    
class Subject(models.Model):
    name = models.TextField(null=False)
    def __str__(self):
        return f"{self.name}"

class SubjectFromDept(models.Model):
    department = models.ForeignKey(Department, on_delete=models.CASCADE)
    year = models.IntegerField(null=False)
    subject = models.ManyToManyField(Subject,null=False)    
    class Meta:
        unique_together = ('department', 'year')

    def __str__(self):
        return f"{self.department} - {self.year}"
    
class Enrollment(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE)
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE)
    teacher = models.ForeignKey(Teacher, on_delete=models.CASCADE)

    class Meta:
        unique_together = ('student', 'subject')

    def __str__(self):
        return f"{self.student} enrolled in {self.subject}"
    
class ClassSession(models.Model):
    department = models.ForeignKey(Department, on_delete=models.CASCADE)
    year = models.IntegerField(null=False)
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE)
    teacher = models.ForeignKey(Teacher, on_delete=models.CASCADE)
    class_datetime = models.DateTimeField(null=False)
    attendance_photo = models.ImageField(upload_to='attendance_photos/', null=True, blank=True) 

    def __str__(self):
        return f"Class for {self.subject.name} at {self.class_datetime}"

class AttendanceRecord(models.Model):
    class_session = models.ForeignKey(ClassSession, on_delete=models.CASCADE)
    student = models.ForeignKey(Student, on_delete=models.CASCADE)
    status = models.BooleanField()
    marked_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('class_session', 'student')

    def __str__(self):
        return f"{self.student.name} - {self.status} for class {self.class_session.id}"
    
class StudentAttendancePercentage(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE)
    subjectAttendancePercentage = models.JSONField(default=dict,null=True, blank=True)
