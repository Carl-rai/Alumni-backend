from rest_framework import serializers
from .models import EventRegistration
from addevent.serializers import EventSerializer
from user.serializers import UserSerializer

class EventRegistrationSerializer(serializers.ModelSerializer):
    event_details = EventSerializer(source='event', read_only=True)
    user_details = UserSerializer(source='user', read_only=True)

    class Meta:
        model = EventRegistration
        fields = ['id', 'event', 'user', 'guest_count', 'registration_date', 'status', 'remarks', 'event_details', 'user_details']
        read_only_fields = ['registration_date']

    def validate(self, data):
        if data.get('guest_count', 0) < 0:
            raise serializers.ValidationError("Guest count cannot be negative")
        return data
