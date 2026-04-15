from rest_framework import serializers

from .models import AuditLog


class AuditLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = AuditLog
        fields = [
            "id",
            "actor_email",
            "actor_name",
            "actor_role",
            "action",
            "method",
            "path",
            "resource",
            "resource_id",
            "success",
            "status_code",
            "ip_address",
            "user_agent",
            "details",
            "created_at",
        ]

