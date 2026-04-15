from django.db import models
from django.conf import settings


class IDRequest(models.Model):
    STATUS_CHOICES = [
        ("pending", "Pending"),
        ("exported", "Exported"),
        ("done", "Done"),
    ]

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="id_request",
    )
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="pending")
    note = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"IDRequest({self.user.email} - {self.status})"
