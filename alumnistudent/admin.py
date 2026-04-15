from django.contrib import admin
from .models import AlumniStudent, AlumniStudentCSVUpload, Category

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'description', 'created_at']
    search_fields = ['name']

@admin.register(AlumniStudent)
class AlumniStudentAdmin(admin.ModelAdmin):
    list_display = ['alumni_id', 'first_name', 'last_name', 'gender', 'age', 'year_graduate', 'category']
    search_fields = ['alumni_id', 'first_name', 'last_name']
    list_filter = ['gender', 'year_graduate', 'category']


@admin.register(AlumniStudentCSVUpload)
class AlumniStudentCSVUploadAdmin(admin.ModelAdmin):
    list_display = ['title', 'csv_file', 'uploaded_at']
    search_fields = ['title', 'csv_file']
