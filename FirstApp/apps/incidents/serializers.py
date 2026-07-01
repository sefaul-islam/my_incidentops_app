"""
DRF Serializers for the Incident Management API.
"""
from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import Incident, IncidentUpdate, PostMortem, OnCallSchedule, EscalationPolicy

User = get_user_model()


class IncidentUpdateSerializer(serializers.ModelSerializer):
    """Serializer for incident timeline entries."""

    author_name = serializers.SerializerMethodField()

    class Meta:
        model = IncidentUpdate
        fields = [
            'id', 'incident', 'author', 'author_name', 'update_type',
            'message', 'old_status', 'new_status', 'created_at',
        ]
        read_only_fields = ['id', 'author', 'author_name', 'created_at']

    def get_author_name(self, obj):
        if obj.author:
            return obj.author.get_full_name() or obj.author.username
        return 'System'


class IncidentListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for incident list views."""

    assignee_name = serializers.SerializerMethodField()
    created_by_name = serializers.SerializerMethodField()
    update_count = serializers.SerializerMethodField()

    class Meta:
        model = Incident
        fields = [
            'id', 'incident_id', 'title', 'severity', 'status',
            'assignee', 'assignee_name', 'created_by', 'created_by_name',
            'created_at', 'updated_at', 'acknowledged_at', 'resolved_at',
            'tags', 'affected_services', 'update_count',
        ]

    def get_assignee_name(self, obj):
        if obj.assignee:
            return obj.assignee.get_full_name() or obj.assignee.username
        return 'Unassigned'

    def get_created_by_name(self, obj):
        if obj.created_by:
            return obj.created_by.get_full_name() or obj.created_by.username
        return 'Unknown'

    def get_update_count(self, obj):
        return obj.updates.count()


class IncidentDetailSerializer(serializers.ModelSerializer):
    """Full serializer for incident detail view, includes timeline."""

    assignee_name = serializers.SerializerMethodField()
    created_by_name = serializers.SerializerMethodField()
    updates = IncidentUpdateSerializer(many=True, read_only=True)
    has_postmortem = serializers.SerializerMethodField()

    class Meta:
        model = Incident
        fields = [
            'id', 'incident_id', 'title', 'description', 'severity', 'status',
            'assignee', 'assignee_name', 'created_by', 'created_by_name',
            'created_at', 'updated_at', 'acknowledged_at', 'resolved_at',
            'tags', 'affected_services', 'updates', 'has_postmortem',
        ]
        read_only_fields = ['id', 'incident_id', 'created_by', 'created_at']

    def get_assignee_name(self, obj):
        if obj.assignee:
            return obj.assignee.get_full_name() or obj.assignee.username
        return 'Unassigned'

    def get_created_by_name(self, obj):
        if obj.created_by:
            return obj.created_by.get_full_name() or obj.created_by.username
        return 'Unknown'

    def get_has_postmortem(self, obj):
        return hasattr(obj, 'postmortem') and obj.postmortem is not None


class IncidentCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating new incidents."""

    class Meta:
        model = Incident
        fields = [
            'title', 'description', 'severity', 'assignee',
            'tags', 'affected_services',
        ]

    def create(self, validated_data):
        validated_data['created_by'] = self.context['request'].user
        return super().create(validated_data)


class IncidentStatusUpdateSerializer(serializers.Serializer):
    """Serializer for status transition actions (acknowledge, resolve, etc.)."""

    message = serializers.CharField(required=False, default='')

    def validate(self, attrs):
        incident = self.context.get('incident')
        new_status = self.context.get('new_status')

        if incident and new_status and not incident.can_transition_to(new_status):
            raise serializers.ValidationError(
                f'Cannot transition from {incident.status} to {new_status}. '
                f'Valid transitions: {incident.VALID_TRANSITIONS.get(incident.status, [])}'
            )
        return attrs


class PostMortemSerializer(serializers.ModelSerializer):
    """Serializer for post-mortem reports including XAI insights."""

    incident_id = serializers.CharField(source='incident.incident_id', read_only=True)
    incident_title = serializers.CharField(source='incident.title', read_only=True)
    generated_by_name = serializers.SerializerMethodField()

    class Meta:
        model = PostMortem
        fields = [
            'id', 'incident', 'incident_id', 'incident_title',
            'summary', 'root_cause', 'impact', 'timeline_data',
            'action_items', 'anomalies', 'xai_confidence', 'log_highlights',
            'created_at', 'updated_at', 'generated_by', 'generated_by_name',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'generated_by']

    def get_generated_by_name(self, obj):
        if obj.generated_by:
            return obj.generated_by.get_full_name() or obj.generated_by.username
        return 'System'


class OnCallScheduleSerializer(serializers.ModelSerializer):
    """Serializer for on-call schedules."""

    user_name = serializers.SerializerMethodField()

    class Meta:
        model = OnCallSchedule
        fields = ['id', 'user', 'user_name', 'start_time', 'end_time', 'is_active']

    def get_user_name(self, obj):
        return obj.user.get_full_name() or obj.user.username


class EscalationPolicySerializer(serializers.ModelSerializer):
    """Serializer for escalation policies."""

    class Meta:
        model = EscalationPolicy
        fields = ['id', 'name', 'severity', 'timeout_minutes', 'notify_oncall', 'notify_admins']
