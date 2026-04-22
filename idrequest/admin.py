from django.contrib import admin

from .models import IDRequest


@admin.register(IDRequest)
class IDRequestAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "alumni_id", "full_name", "status", "created_at", "updated_at")
    list_filter = ("status", "created_at", "updated_at")
    search_fields = (
        "user__email",
        "user__first_name",
        "user__middle_name",
        "user__last_name",
        "user__alumni_id",
    )
    readonly_fields = ("created_at", "updated_at")
    ordering = ("-created_at",)

    def alumni_id(self, obj):
        return obj.user.alumni_id or "-"

    def full_name(self, obj):
        middle = f" {obj.user.middle_name}" if obj.user.middle_name else ""
        return f"{obj.user.first_name}{middle} {obj.user.last_name}".strip()

    alumni_id.short_description = "Alumni ID"
    full_name.short_description = "Full Name"
