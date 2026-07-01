"""
Tests for authentication and RBAC.
"""
from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework import status

User = get_user_model()


class UserModelTest(TestCase):
    """Test the custom User model."""

    def test_create_user_with_email(self):
        user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123',
            role='VIEWER',
        )
        self.assertEqual(user.email, 'test@example.com')
        self.assertEqual(user.role, 'VIEWER')
        self.assertTrue(user.check_password('testpass123'))

    def test_default_role_is_viewer(self):
        user = User.objects.create_user(
            username='testuser2',
            email='test2@example.com',
            password='testpass123',
        )
        self.assertEqual(user.role, 'VIEWER')

    def test_is_admin_role_property(self):
        admin = User.objects.create_user(
            username='admin', email='admin@example.com',
            password='pass123', role='ADMIN',
        )
        self.assertTrue(admin.is_admin_role)
        self.assertTrue(admin.is_responder_role)

    def test_is_responder_role_property(self):
        responder = User.objects.create_user(
            username='responder', email='resp@example.com',
            password='pass123', role='RESPONDER',
        )
        self.assertFalse(responder.is_admin_role)
        self.assertTrue(responder.is_responder_role)


class AuthAPITest(TestCase):
    """Test authentication API endpoints."""

    def setUp(self):
        self.client = APIClient()
        self.admin = User.objects.create_user(
            username='admin', email='admin@test.com',
            password='adminpass123', role='ADMIN',
        )
        self.responder = User.objects.create_user(
            username='responder', email='responder@test.com',
            password='responderpass123', role='RESPONDER',
        )
        self.viewer = User.objects.create_user(
            username='viewer', email='viewer@test.com',
            password='viewerpass123', role='VIEWER',
        )

    def test_register_user(self):
        response = self.client.post('/api/auth/register/', {
            'email': 'new@test.com',
            'username': 'newuser',
            'password': 'newpass12345',
            'password_confirm': 'newpass12345',
        })
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn('tokens', response.data)
        self.assertIn('access', response.data['tokens'])

    def test_login_user(self):
        response = self.client.post('/api/auth/login/', {
            'email': 'admin@test.com',
            'password': 'adminpass123',
        })
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('tokens', response.data)

    def test_login_wrong_password(self):
        response = self.client.post('/api/auth/login/', {
            'email': 'admin@test.com',
            'password': 'wrongpassword',
        })
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_me_endpoint_authenticated(self):
        self.client.force_authenticate(user=self.admin)
        response = self.client.get('/api/auth/me/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['email'], 'admin@test.com')

    def test_me_endpoint_unauthenticated(self):
        response = self.client.get('/api/auth/me/')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_admin_can_update_role(self):
        self.client.force_authenticate(user=self.admin)
        response = self.client.patch(
            f'/api/auth/users/{self.viewer.pk}/role/',
            {'role': 'RESPONDER'},
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.viewer.refresh_from_db()
        self.assertEqual(self.viewer.role, 'RESPONDER')

    def test_non_admin_cannot_update_role(self):
        self.client.force_authenticate(user=self.responder)
        response = self.client.patch(
            f'/api/auth/users/{self.viewer.pk}/role/',
            {'role': 'ADMIN'},
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
