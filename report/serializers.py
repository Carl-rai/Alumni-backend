from rest_framework import serializers
from .models import Report

class ReportSerializer(serializers.ModelSerializer):
    is_registered_user = serializers.SerializerMethodField()
    has_reply = serializers.SerializerMethodField()

    class Meta:
        model = Report
        fields = '__all__'

    def get_is_registered_user(self, obj):
        return obj.user is not None

    def get_has_reply(self, obj):
        return bool(obj.reply)
