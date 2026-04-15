from django.db import models

from alumnicsvupload.models import AlumniStudentCSVUpload as BaseAlumniStudentCSVUpload

class Category(models.Model):
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name_plural = "Categories"
        ordering = ['name']

class AlumniStudent(models.Model):
    GENDER_CHOICES = [
        ('Male', 'Male'),
        ('Female', 'Female'),
    ]

    alumni_id = models.CharField(max_length=30, unique=True)
    first_name = models.CharField(max_length=50)
    middle_name = models.CharField(max_length=50, blank=True, null=True)
    last_name = models.CharField(max_length=50)
    gender = models.CharField(max_length=10, choices=GENDER_CHOICES)
    age = models.PositiveIntegerField(null=True, blank=True)
    year_graduate = models.PositiveIntegerField()
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, blank=True, related_name='alumni')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.alumni_id} - {self.first_name} {self.last_name}"

    class Meta:
        ordering = ['-year_graduate']


class AlumniStudentCSVUpload(BaseAlumniStudentCSVUpload):
    class Meta:
        proxy = True
