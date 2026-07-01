"""
Django Channels WebSocket consumer for real-time incident updates.
"""
import json
from channels.generic.websocket import AsyncJsonWebsocketConsumer
from channels.db import database_sync_to_async


class IncidentConsumer(AsyncJsonWebsocketConsumer):
    """
    WebSocket consumer for real-time incident feed.

    Clients connect to ws://host/ws/incidents/ and receive broadcasts
    whenever an incident is created, updated, or resolved.
    """

    GROUP_NAME = 'incidents_feed'

    async def connect(self):
        """Accept connection and join the incidents broadcast group."""
        self.user = self.scope.get('user')

        # Allow connection even for anonymous users (they'll get read-only updates)
        await self.channel_layer.group_add(
            self.GROUP_NAME,
            self.channel_name,
        )
        await self.accept()

        # Send initial connection confirmation
        await self.send_json({
            'type': 'connection_established',
            'message': 'Connected to IncidentOps real-time feed.',
        })

    async def disconnect(self, close_code):
        """Leave the broadcast group on disconnect."""
        await self.channel_layer.group_discard(
            self.GROUP_NAME,
            self.channel_name,
        )

    async def receive_json(self, content, **kwargs):
        """
        Handle incoming WebSocket messages from clients.
        Currently supports 'ping' for keep-alive.
        """
        msg_type = content.get('type', '')

        if msg_type == 'ping':
            await self.send_json({'type': 'pong'})
        elif msg_type == 'subscribe_incident':
            # Join a specific incident's channel for focused updates
            incident_id = content.get('incident_id')
            if incident_id:
                await self.channel_layer.group_add(
                    f'incident_{incident_id}',
                    self.channel_name,
                )
                await self.send_json({
                    'type': 'subscribed',
                    'incident_id': incident_id,
                })

    # ── Broadcast event handlers ──────────────────────────────

    async def incident_created(self, event):
        """Broadcast when a new incident is created."""
        await self.send_json({
            'type': 'incident_created',
            'incident': event['incident'],
        })

    async def incident_updated(self, event):
        """Broadcast when an incident is updated (status change, comment, etc.)."""
        await self.send_json({
            'type': 'incident_updated',
            'incident': event['incident'],
        })

    async def incident_comment(self, event):
        """Broadcast when a new comment is added to an incident."""
        await self.send_json({
            'type': 'incident_comment',
            'incident_id': event['incident_id'],
            'comment': event['comment'],
        })
