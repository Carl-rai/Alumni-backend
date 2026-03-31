from django.db import models
from user.models import CustomUser
from career.models import JobPost


class JobApplication(models.Model):
    STATUS_CHOICES = [
        ("pending", "Pending"),
        ("reviewed", "Reviewed"),
        ("accepted", "Accepted"),
        ("rejected", "Rejected"),
    ]

    applicant = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name="job_applications")
    job = models.ForeignKey(JobPost, on_delete=models.CASCADE, related_name="applications")
    phone = models.CharField(max_length=20)
    address = models.TextField()
    resume = models.FileField(upload_to="resumes/")
    cover_letter = models.TextField(blank=True, null=True)
    portfolio_link = models.URLField(blank=True, null=True)
    skills = models.TextField()
    work_experience = models.TextField()
    remarks = models.TextField(blank=True, null=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="pending")
    applied_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.applicant.email} - {self.job_title}"

    class Meta:
        ordering = ["-applied_at"]
