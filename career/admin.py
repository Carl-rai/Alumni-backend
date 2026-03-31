from django.contrib import admin
from .models import JobPost

@admin.register(JobPost)
class JobPostAdmin(admin.ModelAdmin):
    list_display = ['job_title', 'company_name', 'employment_type', 'status', 'date_posted']
    list_filter = ['status', 'employment_type', 'work_setup', 'experience_level']
    search_fields = ['job_title', 'company_name', 'industry']
