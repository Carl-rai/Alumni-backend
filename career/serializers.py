from rest_framework import serializers
from .models import JobPost


class JobPostSerializer(serializers.ModelSerializer):
    posted_by_name = serializers.SerializerMethodField(read_only=True)
    image_upload = serializers.ImageField(write_only=True, required=False)
    image = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = JobPost
        fields = '__all__'
        read_only_fields = ['posted_by', 'date_posted']

    def get_posted_by_name(self, obj):
        if obj.posted_by:
            return f"{obj.posted_by.first_name} {obj.posted_by.last_name}"
        return None

    def get_image(self, obj):
        if obj.image:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.image.url)
            return obj.image.url
        return None

    def create(self, validated_data):
        image_upload = validated_data.pop('image_upload', None)
        instance = super().create(validated_data)
        if image_upload:
            instance.image = image_upload
            instance.save()
        return instance

    def update(self, instance, validated_data):
        image_upload = validated_data.pop('image_upload', None)
        instance = super().update(instance, validated_data)
        if image_upload:
            instance.image = image_upload
            instance.save()
        return instance
