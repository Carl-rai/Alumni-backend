from django.db import models


class AuditLog(models.Model):
    ROLE_CHOICES = [
        ("admin", "Admin"),
        ("staff", "Staff"),
        ("id-staff", "ID Staff"),
        ("user", "User"),
        ("anonymous", "Anonymous"),
        ("system", "System"),
    ]

    actor_email = models.EmailField(null=True, blank=True)
    actor_name = models.CharField(max_length=150, null=True, blank=True)
    actor_role = models.CharField(max_length=20, choices=ROLE_CHOICES, default="anonymous")
    action = models.CharField(max_length=120)
    method = models.CharField(max_length=10)
    path = models.CharField(max_length=255)
    resource = models.CharField(max_length=100, null=True, blank=True)
    resource_id = models.CharField(max_length=50, null=True, blank=True)
    success = models.BooleanField(default=True)
    status_code = models.PositiveIntegerField(null=True, blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(null=True, blank=True)
    details = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        db_table = "user_auditlog"
        indexes = [
            models.Index(fields=["-created_at"]),
            models.Index(fields=["actor_role", "-created_at"]),
            models.Index(fields=["action", "-created_at"]),
        ]

    def __str__(self):
        return f"{self.created_at:%Y-%m-%d %H:%M:%S} - {self.actor_role} - {self.action}"

