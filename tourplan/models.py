from django.db import models
from simple_history.models import HistoricalRecords

# Create your models here.
class Student(models.Model):
    SEMESTER_CHOICES = [
        (1, "1"),
        (2, "2"),
        (3, "3"),
        (4, "4"),
        (5, "5"),
        (6, "6"),
        (7, "7"),
        (8, "8"),
    ]
    student_semester = models.IntegerField(choices=SEMESTER_CHOICES)
    serial_number = models.IntegerField()
    student_name = models.CharField(max_length=100)
    participation = models.BooleanField()

    def __str__(self):
        return f"Semester {self.student_semester} - {self.student_name}"


    history = HistoricalRecords()