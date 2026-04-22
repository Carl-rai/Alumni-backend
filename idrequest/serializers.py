from rest_framework import serializers

from user.serializers import UserSerializer

from .models import IDRequest


class IDRequestStaffSerializer(serializers.ModelSerializer):
    user_id = serializers.IntegerField(source="user.id", read_only=True)
    user_details = UserSerializer(source="user", read_only=True)
    full_name = serializers.SerializerMethodField()
    alumni_id = serializers.CharField(source="user.alumni_id", read_only=True)
    email = serializers.CharField(source="user.email", read_only=True)
    first_name = serializers.CharField(source="user.first_name", read_only=True)
    middle_name = serializers.CharField(source="user.middle_name", read_only=True, allow_null=True, allow_blank=True)
    last_name = serializers.CharField(source="user.last_name", read_only=True)
    course = serializers.CharField(source="user.course", read_only=True)
    year_graduate = serializers.IntegerField(source="user.year_graduate", read_only=True)
    gender = serializers.CharField(source="user.gender", read_only=True)

    class Meta:
        model = IDRequest
        fields = [
            "id",
            "user",
            "user_id",
            "user_details",
            "full_name",
            "alumni_id",
            "email",
            "first_name",
            "middle_name",
            "last_name",
            "course",
            "year_graduate",
            "gender",
            "note",
            "status",
            "created_at",
            "updated_at",
        ]
        read_only_fields = fields

    def get_full_name(self, obj):
        middle = f" {obj.user.middle_name}" if obj.user.middle_name else ""
        return f"{obj.user.first_name}{middle} {obj.user.last_name}".strip()
