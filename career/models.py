from django.db import models
from user.models import CustomUser


class JobPost(models.Model):
    EMPLOYMENT_TYPE_CHOICES = [
        ('full_time', 'Full-time'),
        ('part_time', 'Part-time'),
        ('internship', 'Internship'),
        ('contract', 'Contract'),
    ]

    WORK_SETUP_CHOICES = [
        ('on_site', 'On-site'),
        ('remote', 'Remote'),
        ('hybrid', 'Hybrid'),
    ]

    EXPERIENCE_LEVEL_CHOICES = [
        ('entry', 'Entry-level'),
        ('mid', 'Mid-level'),
        ('senior', 'Senior'),
    ]

    STATUS_CHOICES = [
        ('open', 'Open'),
        ('closed', 'Closed'),
    ]

    # Basic Job Information
    job_title = models.CharField(max_length=200)
    company_name = models.CharField(max_length=200)
    job_description = models.TextField()
    industry = models.CharField(max_length=100)

    # Job Details
    employment_type = models.CharField(max_length=20, choices=EMPLOYMENT_TYPE_CHOICES)
    work_setup = models.CharField(max_length=20, choices=WORK_SETUP_CHOICES)
    location = models.CharField(max_length=200)
    salary_range = models.CharField(max_length=100, blank=True, null=True)

    # Requirements
    required_skills = models.TextField( blank=True, null=True)
    education_requirement = models.CharField(max_length=200)
    experience_level = models.CharField(max_length=20, choices=EXPERIENCE_LEVEL_CHOICES)

    # Application Information
    application_deadline = models.DateField()
    application_link_or_email = models.CharField(max_length=300)
    contact_person = models.CharField(max_length=100, blank=True, null=True)

    # Image
    image = models.ImageField(upload_to='jobs/', blank=True, null=True)

    # Posting Details
    posted_by = models.ForeignKey(CustomUser, on_delete=models.SET_NULL, null=True, related_name='job_posts')
    date_posted = models.DateField(auto_now_add=True)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='open')

    class Meta:
        ordering = ['-date_posted']

    def __str__(self):
        return f"{self.job_title} at {self.company_name}"
