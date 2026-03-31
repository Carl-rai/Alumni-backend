from rest_framework import serializers
from .models import CustomUser

class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)
    confirm_password = serializers.CharField(write_only=True)

    class Meta:
        model = CustomUser
        fields = [
            "alumni_id",
            "email",
            "first_name",
            "middle_name",
            "last_name",
            "gender",
            "age",
            "course",
            "year_graduate",
            "password",
            "confirm_password",
            "profile_image",
        ]

    def validate(self, data):
        if data["password"] != data["confirm_password"]:
            raise serializers.ValidationError("Passwords do not match.")
        return data

    def create(self, validated_data):
        validated_data.pop("confirm_password")
        password = validated_data.pop("password")
        validated_data['role'] = 'user'

        user = CustomUser.objects.create(**validated_data)
        user.set_password(password)
        user.save()

        return user


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomUser
        fields = ['id', 'email', 'first_name', 'middle_name', 'last_name', 'alumni_id', 'profile_image']


class StaffCreateSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)

    class Meta:
        model = CustomUser
        fields = [
            "email",
            "first_name",
            "middle_name",
            "last_name",
            "gender",
            "age",
            "position",
            "password",
            "role",
            "profile_image",
        ]

    def validate_role(self, value):
        if value not in ['staff', 'admin']:
            raise serializers.ValidationError("Role must be 'staff' or 'admin'")
        return value

    def create(self, validated_data):
        password = validated_data.pop("password")
        role = validated_data.get('role', 'staff')
        validated_data['status'] = 'approved'
        
        user = CustomUser.objects.create(**validated_data)
        user.set_password(password)
        
        if role == 'admin':
            user.is_staff = True
            user.is_superuser = True
        elif role == 'staff':
            user.is_staff = True
            
        user.save()
        return user
