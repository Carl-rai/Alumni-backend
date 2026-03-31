from django.contrib import admin
from .models import JobApplication

# @admin.register(JobApplication)
# class JobApplicationAdmin(admin.ModelAdmin):
#     list_display = ["applicant", "job", "phone", "status", "applied_at"]
#     list_filter = ["status"]
#     search_fields = ["applicant__email", "job_title", "phone"]
