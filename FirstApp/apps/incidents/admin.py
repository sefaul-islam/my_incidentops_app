"""
Django admin configuration for Incident Management models.
"""
from django.contrib import admin
from .models import Incident, IncidentUpdate, PostMortem, OnCallSchedule, EscalationPolicy


@admin.register(Incident)
class IncidentAdmin(admin.ModelAdmin):
    list_display = ['incident_id', 'title', 'severity', 'status', 'assignee', 'created_at']
    list_filter = ['severity', 'status', 'created_at']
    search_fields = ['incident_id', 'title', 'description']
    readonly_fields = ['incident_id', 'created_at', 'updated_at']
    raw_id_fields = ['assignee', 'created_by']


@admin.register(IncidentUpdate)
class IncidentUpdateAdmin(admin.ModelAdmin):
    list_display = ['incident', 'update_type', 'author', 'created_at']
    list_filter = ['update_type', 'created_at']
    raw_id_fields = ['incident', 'author']


@admin.register(PostMortem)
class PostMortemAdmin(admin.ModelAdmin):
    list_display = ['incident', 'xai_confidence', 'generated_by', 'created_at']
    raw_id_fields = ['incident', 'generated_by']


@admin.register(OnCallSchedule)
class OnCallScheduleAdmin(admin.ModelAdmin):
    list_display = ['user', 'start_time', 'end_time', 'is_active']
    list_filter = ['is_active']
    raw_id_fields = ['user']


@admin.register(EscalationPolicy)
class EscalationPolicyAdmin(admin.ModelAdmin):
    list_display = ['name', 'severity', 'timeout_minutes', 'notify_oncall', 'notify_admins']
    list_filter = ['severity']
