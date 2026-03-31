from rest_framework import serializers
from .models import Event

ALLOWED_IMAGE_TYPES = [
    '.jpg', '.jpeg', '.png', '.gif', '.webp',
    '.svg', '.bmp', '.tiff', '.tif', '.ico', '.avif'
]

class EventSerializer(serializers.ModelSerializer):
    image = serializers.SerializerMethodField()
    image_upload = serializers.FileField(write_only=True, required=False)
    slots_remaining = serializers.SerializerMethodField()

    class Meta:
        model = Event
        fields = '__all__'
        extra_fields = ['image_upload', 'slots_remaining']

    def get_slots_remaining(self, obj):
        return obj.capacity  # capacity is already deducted on each registration

    def get_fields(self):
        fields = super().get_fields()
        fields['image_upload'] = serializers.FileField(write_only=True, required=False)
        return fields

    def get_image(self, obj):
        if obj.image:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.image.url)
            return obj.image.url
        return None

    def validate_image_upload(self, value):
        import os
        ext = os.path.splitext(value.name)[1].lower()
        if ext not in ALLOWED_IMAGE_TYPES:
            raise serializers.ValidationError(
                f"Unsupported file type '{ext}'. Allowed: {', '.join(ALLOWED_IMAGE_TYPES)}"
            )
        return value

    def create(self, validated_data):
        image = validated_data.pop('image_upload', None)
        instance = super().create(validated_data)
        if image:
            instance.image = image
            instance.save()
        return instance

    def update(self, instance, validated_data):
        image = validated_data.pop('image_upload', None)
        instance = super().update(instance, validated_data)
        if image:
            instance.image = image
            instance.save()
        return instance