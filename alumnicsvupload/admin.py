from django.contrib import admin

from .models import AlumniStudentCSVUpload


@admin.register(AlumniStudentCSVUpload)
class AlumniStudentCSVUploadAdmin(admin.ModelAdmin):
    list_display = ["title", "csv_file", "uploaded_at"]
    search_fields = ["title", "csv_file"]

