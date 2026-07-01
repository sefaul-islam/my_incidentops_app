"""
Serializers for authentication, registration, and user management.
"""
from rest_framework import serializers
from django.contrib.auth import get_user_model

User = get_user_model()


class UserRegistrationSerializer(serializers.ModelSerializer):
    """Serializer for user registration."""

    password = serializers.CharField(write_only=True, min_length=8)
    password_confirm = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = [
            'id', 'email', 'username', 'first_name', 'last_name',
            'password', 'password_confirm', 'role',
        ]
        read_only_fields = ['id']

    def validate(self, attrs):
        if attrs['password'] != attrs.pop('password_confirm'):
            raise serializers.ValidationError({'password_confirm': 'Passwords do not match.'})
        return attrs

    def create(self, validated_data):
        password = validated_data.pop('password')
        user = User(**validated_data)
        user.set_password(password)
        user.save()
        return user


class UserProfileSerializer(serializers.ModelSerializer):
    """Serializer for viewing and updating user profile."""

    class Meta:
        model = User
        fields = [
            'id', 'email', 'username', 'first_name', 'last_name',
            'role', 'avatar_url', 'phone_number', 'is_on_call',
            'date_joined', 'last_login',
        ]
        read_only_fields = ['id', 'email', 'date_joined', 'last_login']


class UserListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for user lists (e.g., assignee dropdown)."""

    full_name = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ['id', 'email', 'username', 'full_name', 'role', 'avatar_url', 'is_on_call']

    def get_full_name(self, obj):
        return obj.get_full_name() or obj.username


class UserRoleUpdateSerializer(serializers.ModelSerializer):
    """Serializer for admins to update user roles."""

    class Meta:
        model = User
        fields = ['id', 'role']
        read_only_fields = ['id']


class OAuthCallbackSerializer(serializers.Serializer):
    """Serializer for OAuth2 callback with authorization code."""

    code = serializers.CharField(required=True)
    provider = serializers.ChoiceField(choices=['google', 'github'], required=True)
