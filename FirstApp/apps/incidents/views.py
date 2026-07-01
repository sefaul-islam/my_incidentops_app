"""
DRF ViewSets for incident management with lifecycle actions.
"""
from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from django.utils import timezone
from django.shortcuts import get_object_or_404

from apps.authentication.permissions import IsAdminOrResponder, IsAdmin

from .models import (
    Incident, IncidentUpdate, PostMortem,
    OnCallSchedule, EscalationPolicy,
)
from .serializers import (
    IncidentListSerializer, IncidentDetailSerializer,
    IncidentCreateSerializer, IncidentStatusUpdateSerializer,
    IncidentUpdateSerializer, PostMortemSerializer,
    OnCallScheduleSerializer, EscalationPolicySerializer,
)


class IncidentViewSet(viewsets.ModelViewSet):
    """
    CRUD + lifecycle actions for incidents.

    list:   GET    /api/incidents/
    create: POST   /api/incidents/
    detail: GET    /api/incidents/{id}/
    update: PATCH  /api/incidents/{id}/
    delete: DELETE /api/incidents/{id}/

    Custom actions:
        POST /api/incidents/{id}/acknowledge/
        POST /api/incidents/{id}/investigate/
        POST /api/incidents/{id}/mitigate/
        POST /api/incidents/{id}/resolve/
        POST /api/incidents/{id}/comment/
        POST /api/incidents/{id}/generate_postmortem/
    """

    queryset = Incident.objects.select_related('assignee', 'created_by').all()
    permission_classes = [IsAdminOrResponder]

    def get_serializer_class(self):
        if self.action == 'list':
            return IncidentListSerializer
        if self.action == 'create':
            return IncidentCreateSerializer
        return IncidentDetailSerializer

    def get_queryset(self):
        qs = super().get_queryset()
        # Optional filters
        severity = self.request.query_params.get('severity')
        incident_status = self.request.query_params.get('status')
        assignee = self.request.query_params.get('assignee')

        if severity:
            qs = qs.filter(severity=severity)
        if incident_status:
            qs = qs.filter(status=incident_status)
        if assignee:
            qs = qs.filter(assignee_id=assignee)
        return qs

    def _transition_status(self, request, pk, new_status):
        """Helper to handle status transitions with timeline logging."""
        incident = self.get_object()
        serializer = IncidentStatusUpdateSerializer(
            data=request.data,
            context={'incident': incident, 'new_status': new_status},
        )
        serializer.is_valid(raise_exception=True)

        old_status = incident.status
        incident.status = new_status

        if new_status == 'ACKNOWLEDGED':
            incident.acknowledged_at = timezone.now()
        elif new_status == 'RESOLVED':
            incident.resolved_at = timezone.now()

        incident.save()

        # Create timeline entry
        IncidentUpdate.objects.create(
            incident=incident,
            author=request.user,
            update_type='STATUS_CHANGE',
            message=serializer.validated_data.get('message', f'Status changed to {new_status}'),
            old_status=old_status,
            new_status=new_status,
        )

        return Response(IncidentDetailSerializer(incident).data)

    @action(detail=True, methods=['post'])
    def acknowledge(self, request, pk=None):
        """POST /api/incidents/{id}/acknowledge/ — Acknowledge an incident."""
        return self._transition_status(request, pk, 'ACKNOWLEDGED')

    @action(detail=True, methods=['post'])
    def investigate(self, request, pk=None):
        """POST /api/incidents/{id}/investigate/ — Move to investigating."""
        return self._transition_status(request, pk, 'INVESTIGATING')

    @action(detail=True, methods=['post'])
    def mitigate(self, request, pk=None):
        """POST /api/incidents/{id}/mitigate/ — Move to mitigating."""
        return self._transition_status(request, pk, 'MITIGATING')

    @action(detail=True, methods=['post'])
    def resolve(self, request, pk=None):
        """POST /api/incidents/{id}/resolve/ — Resolve the incident."""
        return self._transition_status(request, pk, 'RESOLVED')

    @action(detail=True, methods=['post'])
    def comment(self, request, pk=None):
        """POST /api/incidents/{id}/comment/ — Add a timeline comment."""
        incident = self.get_object()
        message = request.data.get('message', '')
        if not message:
            return Response(
                {'error': 'Message is required.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        update = IncidentUpdate.objects.create(
            incident=incident,
            author=request.user,
            update_type='COMMENT',
            message=message,
        )

        return Response(
            IncidentUpdateSerializer(update).data,
            status=status.HTTP_201_CREATED,
        )

    @action(detail=True, methods=['post', 'get'])
    def generate_postmortem(self, request, pk=None):
        """
        POST /api/incidents/{id}/generate_postmortem/ — Generate XAI post-mortem.
        GET  /api/incidents/{id}/generate_postmortem/ — Retrieve existing post-mortem.
        """
        incident = self.get_object()

        if request.method == 'GET':
            try:
                postmortem = incident.postmortem
                return Response(PostMortemSerializer(postmortem).data)
            except PostMortem.DoesNotExist:
                return Response(
                    {'error': 'No post-mortem exists for this incident.'},
                    status=status.HTTP_404_NOT_FOUND,
                )

        # POST — Generate new post-mortem
        if incident.status not in ('RESOLVED', 'POST_MORTEM'):
            return Response(
                {'error': 'Incident must be resolved before generating a post-mortem.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Import XAI module and generate
        from .xai.report_generator import generate_postmortem_report
        postmortem = generate_postmortem_report(incident, request.user)

        # Update incident status
        if incident.status == 'RESOLVED':
            incident.status = 'POST_MORTEM'
            incident.save()

        return Response(
            PostMortemSerializer(postmortem).data,
            status=status.HTTP_201_CREATED,
        )


class IncidentUpdateViewSet(viewsets.ReadOnlyModelViewSet):
    """Read-only viewset for incident timeline entries."""

    serializer_class = IncidentUpdateSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return IncidentUpdate.objects.filter(
            incident_id=self.kwargs.get('incident_pk'),
        ).select_related('author')


class PostMortemViewSet(viewsets.ReadOnlyModelViewSet):
    """Read-only viewset for post-mortem reports."""

    queryset = PostMortem.objects.select_related('incident', 'generated_by').all()
    serializer_class = PostMortemSerializer
    permission_classes = [permissions.IsAuthenticated]


class OnCallScheduleViewSet(viewsets.ModelViewSet):
    """CRUD for on-call schedules. Admin-only for write operations."""

    queryset = OnCallSchedule.objects.select_related('user').all()
    serializer_class = OnCallScheduleSerializer
    permission_classes = [IsAdminOrResponder]


class EscalationPolicyViewSet(viewsets.ModelViewSet):
    """CRUD for escalation policies. Admin-only."""

    queryset = EscalationPolicy.objects.all()
    serializer_class = EscalationPolicySerializer
    permission_classes = [IsAdmin]
