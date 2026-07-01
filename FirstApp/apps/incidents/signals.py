"""
Django signals for incident lifecycle events.
Broadcasts real-time updates via WebSocket when incidents change.
"""
from django.db.models.signals import post_save
from django.dispatch import receiver
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync

from .models import Incident, IncidentUpdate
from .serializers import IncidentListSerializer


@receiver(post_save, sender=Incident)
def broadcast_incident_change(sender, instance, created, **kwargs):
    """Push incident create/update events to the WebSocket group."""
    channel_layer = get_channel_layer()
    if not channel_layer:
        return

    serialized = IncidentListSerializer(instance).data

    event_type = 'incident_created' if created else 'incident_updated'

    async_to_sync(channel_layer.group_send)(
        'incidents_feed',
        {
            'type': event_type,
            'incident': serialized,
        },
    )


@receiver(post_save, sender=IncidentUpdate)
def broadcast_incident_update(sender, instance, created, **kwargs):
    """Push timeline update events to the incident-specific WebSocket group."""
    if not created:
        return

    channel_layer = get_channel_layer()
    if not channel_layer:
        return

    from .serializers import IncidentUpdateSerializer
    serialized = IncidentUpdateSerializer(instance).data

    # Broadcast to the specific incident's channel
    async_to_sync(channel_layer.group_send)(
        f'incident_{instance.incident.incident_id}',
        {
            'type': 'incident_comment',
            'incident_id': instance.incident.incident_id,
            'comment': serialized,
        },
    )

    # Also broadcast the updated incident to the main feed
    incident_serialized = IncidentListSerializer(instance.incident).data
    async_to_sync(channel_layer.group_send)(
        'incidents_feed',
        {
            'type': 'incident_updated',
            'incident': incident_serialized,
        },
    )
