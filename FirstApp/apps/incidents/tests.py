"""
Tests for the Incident Management API.
"""
from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework import status

from .models import Incident, IncidentUpdate

User = get_user_model()


class IncidentModelTest(TestCase):
    """Test the Incident model."""

    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser', email='test@example.com',
            password='pass123', role='RESPONDER',
        )

    def test_auto_generates_incident_id(self):
        incident = Incident.objects.create(
            title='Test incident',
            severity='SEV2',
            created_by=self.user,
        )
        self.assertTrue(incident.incident_id.startswith('INC-'))

    def test_default_status_is_declared(self):
        incident = Incident.objects.create(
            title='Test incident',
            created_by=self.user,
        )
        self.assertEqual(incident.status, 'DECLARED')

    def test_valid_status_transition(self):
        incident = Incident.objects.create(
            title='Test incident', created_by=self.user,
        )
        self.assertTrue(incident.can_transition_to('ACKNOWLEDGED'))
        self.assertFalse(incident.can_transition_to('RESOLVED'))

    def test_sequential_incident_ids(self):
        inc1 = Incident.objects.create(title='First', created_by=self.user)
        inc2 = Incident.objects.create(title='Second', created_by=self.user)
        self.assertNotEqual(inc1.incident_id, inc2.incident_id)


class IncidentAPITest(TestCase):
    """Test the Incident API endpoints."""

    def setUp(self):
        self.client = APIClient()
        self.admin = User.objects.create_user(
            username='admin', email='admin@test.com',
            password='pass123', role='ADMIN',
        )
        self.responder = User.objects.create_user(
            username='responder', email='resp@test.com',
            password='pass123', role='RESPONDER',
        )
        self.viewer = User.objects.create_user(
            username='viewer', email='viewer@test.com',
            password='pass123', role='VIEWER',
        )

    def test_create_incident_as_responder(self):
        self.client.force_authenticate(user=self.responder)
        response = self.client.post('/api/incidents/', {
            'title': 'API Gateway down',
            'severity': 'SEV1',
            'description': 'All API requests returning 503',
        })
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['severity'], 'SEV1')

    def test_viewer_cannot_create_incident(self):
        self.client.force_authenticate(user=self.viewer)
        response = self.client.post('/api/incidents/', {
            'title': 'Test incident',
            'severity': 'SEV3',
        })
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_viewer_can_list_incidents(self):
        self.client.force_authenticate(user=self.viewer)
        response = self.client.get('/api/incidents/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_acknowledge_incident(self):
        self.client.force_authenticate(user=self.responder)
        incident = Incident.objects.create(
            title='Test', severity='SEV2', created_by=self.responder,
        )
        response = self.client.post(f'/api/incidents/{incident.pk}/acknowledge/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        incident.refresh_from_db()
        self.assertEqual(incident.status, 'ACKNOWLEDGED')
        self.assertIsNotNone(incident.acknowledged_at)

    def test_full_lifecycle(self):
        self.client.force_authenticate(user=self.responder)
        incident = Incident.objects.create(
            title='Lifecycle test', severity='SEV1', created_by=self.responder,
        )

        # Acknowledge
        self.client.post(f'/api/incidents/{incident.pk}/acknowledge/')
        # Investigate
        self.client.post(f'/api/incidents/{incident.pk}/investigate/')
        # Mitigate
        self.client.post(f'/api/incidents/{incident.pk}/mitigate/')
        # Resolve
        response = self.client.post(f'/api/incidents/{incident.pk}/resolve/')

        incident.refresh_from_db()
        self.assertEqual(incident.status, 'RESOLVED')
        self.assertIsNotNone(incident.resolved_at)

        # Check timeline
        updates = IncidentUpdate.objects.filter(incident=incident)
        self.assertEqual(updates.count(), 4)

    def test_add_comment(self):
        self.client.force_authenticate(user=self.responder)
        incident = Incident.objects.create(
            title='Comment test', created_by=self.responder,
        )
        response = self.client.post(
            f'/api/incidents/{incident.pk}/comment/',
            {'message': 'Investigating the root cause.'},
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_invalid_transition(self):
        self.client.force_authenticate(user=self.responder)
        incident = Incident.objects.create(
            title='Invalid transition', created_by=self.responder,
        )
        # Try to resolve directly from DECLARED (invalid)
        response = self.client.post(f'/api/incidents/{incident.pk}/resolve/')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
