from django.contrib import admin

from .models import AuditLog


@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = ("created_at", "actor_role", "actor_email", "action", "method", "path", "success")
    list_filter = ("actor_role", "action", "method", "success", "created_at")
    search_fields = ("actor_email", "actor_name", "action", "path", "resource", "resource_id")
    readonly_fields = (
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
    )
    ordering = ("-created_at",)

