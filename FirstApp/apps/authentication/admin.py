"""
Register custom User model in Django admin.
"""
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth import get_user_model

User = get_user_model()


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ['email', 'username', 'first_name', 'last_name', 'role', 'is_on_call', 'is_active']
    list_filter = ['role', 'is_on_call', 'is_active', 'is_staff']
    search_fields = ['email', 'username', 'first_name', 'last_name']
    ordering = ['-date_joined']

    fieldsets = BaseUserAdmin.fieldsets + (
        ('IncidentOps', {
            'fields': ('role', 'avatar_url', 'phone_number', 'is_on_call'),
        }),
    )

    add_fieldsets = BaseUserAdmin.add_fieldsets + (
        ('IncidentOps', {
            'fields': ('email', 'role'),
        }),
    )
