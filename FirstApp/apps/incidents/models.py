"""
Core models for the Incident Management system.

Incident lifecycle:
    DECLARED → ACKNOWLEDGED → INVESTIGATING → MITIGATING → RESOLVED → POST_MORTEM
"""
import uuid
from django.conf import settings
from django.db import models
from django.utils import timezone


class Incident(models.Model):
    """Primary incident record tracking the full lifecycle."""

    class Severity(models.TextChoices):
        SEV1 = 'SEV1', 'Sev-1 (Critical)'
        SEV2 = 'SEV2', 'Sev-2 (High)'
        SEV3 = 'SEV3', 'Sev-3 (Medium)'
        SEV4 = 'SEV4', 'Sev-4 (Low)'

    class Status(models.TextChoices):
        DECLARED = 'DECLARED', 'Declared'
        ACKNOWLEDGED = 'ACKNOWLEDGED', 'Acknowledged'
        INVESTIGATING = 'INVESTIGATING', 'Investigating'
        MITIGATING = 'MITIGATING', 'Mitigating'
        RESOLVED = 'RESOLVED', 'Resolved'
        POST_MORTEM = 'POST_MORTEM', 'Post-Mortem'

    # Valid status transitions
    VALID_TRANSITIONS = {
        'DECLARED': ['ACKNOWLEDGED', 'INVESTIGATING'],
        'ACKNOWLEDGED': ['INVESTIGATING', 'MITIGATING'],
        'INVESTIGATING': ['MITIGATING', 'RESOLVED'],
        'MITIGATING': ['RESOLVED'],
        'RESOLVED': ['POST_MORTEM', 'INVESTIGATING'],  # Allow reopening
        'POST_MORTEM': [],
    }

    incident_id = models.CharField(
        max_length=20,
        unique=True,
        editable=False,
        help_text='Human-readable incident ID (e.g., INC-1042)',
    )
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True, default='')
    severity = models.CharField(max_length=4, choices=Severity.choices, default=Severity.SEV3)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.DECLARED)

    # Ownership
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='created_incidents',
    )
    assignee = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='assigned_incidents',
    )

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    acknowledged_at = models.DateTimeField(null=True, blank=True)
    resolved_at = models.DateTimeField(null=True, blank=True)

    # Metadata
    tags = models.JSONField(default=list, blank=True)
    affected_services = models.JSONField(default=list, blank=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['status', '-created_at']),
            models.Index(fields=['severity', '-created_at']),
            models.Index(fields=['assignee', 'status']),
        ]

    def __str__(self):
        return f'{self.incident_id}: {self.title}'

    def save(self, *args, **kwargs):
        if not self.incident_id:
            self.incident_id = self._generate_incident_id()
        super().save(*args, **kwargs)

    def _generate_incident_id(self):
        """Generate a sequential human-readable incident ID."""
        last = Incident.objects.order_by('-pk').first()
        next_num = (last.pk + 1) if last else 1
        return f'INC-{next_num:04d}'

    def can_transition_to(self, new_status):
        """Check if the requested status transition is valid."""
        return new_status in self.VALID_TRANSITIONS.get(self.status, [])


class IncidentUpdate(models.Model):
    """Timeline entry for an incident — tracks all status changes and comments."""

    class UpdateType(models.TextChoices):
        STATUS_CHANGE = 'STATUS_CHANGE', 'Status Change'
        COMMENT = 'COMMENT', 'Comment'
        ASSIGNMENT = 'ASSIGNMENT', 'Assignment Change'
        ESCALATION = 'ESCALATION', 'Escalation'

    incident = models.ForeignKey(
        Incident, on_delete=models.CASCADE, related_name='updates',
    )
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True,
    )
    update_type = models.CharField(
        max_length=20, choices=UpdateType.choices, default=UpdateType.COMMENT,
    )
    message = models.TextField()
    old_status = models.CharField(max_length=20, blank=True, default='')
    new_status = models.CharField(max_length=20, blank=True, default='')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.incident.incident_id} — {self.update_type} by {self.author}'


class PostMortem(models.Model):
    """Post-mortem report generated after an incident is resolved."""

    incident = models.OneToOneField(
        Incident, on_delete=models.CASCADE, related_name='postmortem',
    )
    summary = models.TextField(blank=True, default='')
    root_cause = models.TextField(blank=True, default='')
    impact = models.TextField(blank=True, default='')
    timeline_data = models.JSONField(default=list, blank=True)
    action_items = models.JSONField(default=list, blank=True)

    # XAI Insights
    anomalies = models.JSONField(
        default=list, blank=True,
        help_text='List of anomaly objects detected by the XAI analyzer.',
    )
    xai_confidence = models.FloatField(
        null=True, blank=True,
        help_text='Overall confidence score of the XAI analysis (0.0 to 1.0).',
    )
    log_highlights = models.JSONField(
        default=list, blank=True,
        help_text='Highlighted log excerpts relevant to root cause.',
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    generated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True,
    )

    def __str__(self):
        return f'Post-Mortem: {self.incident.incident_id}'


class OnCallSchedule(models.Model):
    """On-call rotation schedule for responders."""

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='oncall_schedules',
    )
    start_time = models.DateTimeField()
    end_time = models.DateTimeField()
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['-start_time']

    def __str__(self):
        return f'{self.user.email}: {self.start_time} — {self.end_time}'

    @classmethod
    def get_current_oncall(cls):
        """Return users currently on call."""
        now = timezone.now()
        return cls.objects.filter(
            start_time__lte=now, end_time__gte=now, is_active=True,
        ).select_related('user')


class EscalationPolicy(models.Model):
    """Defines escalation rules for unacknowledged incidents."""

    name = models.CharField(max_length=100)
    severity = models.CharField(max_length=4, choices=Incident.Severity.choices)
    timeout_minutes = models.PositiveIntegerField(
        default=15,
        help_text='Minutes before escalation triggers for unacknowledged incidents.',
    )
    notify_oncall = models.BooleanField(default=True)
    notify_admins = models.BooleanField(default=False)

    class Meta:
        verbose_name_plural = 'Escalation Policies'

    def __str__(self):
        return f'{self.name} ({self.severity})'
