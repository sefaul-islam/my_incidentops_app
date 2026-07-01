"""
Custom User model with Role-Based Access Control (RBAC).

Roles:
  - ADMIN: Full platform access including user/team management.
  - RESPONDER: Can create, acknowledge, update, and resolve incidents.
  - VIEWER: Read-only access to incidents and analytics.
"""
from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    """Custom user extending Django's AbstractUser with a role field."""

    class Role(models.TextChoices):
        ADMIN = 'ADMIN', 'Admin'
        RESPONDER = 'RESPONDER', 'Responder'
        VIEWER = 'VIEWER', 'Viewer'

    email = models.EmailField(unique=True)
    role = models.CharField(
        max_length=20,
        choices=Role.choices,
        default=Role.VIEWER,
        help_text='Determines the user\'s permission level in the platform.',
    )
    avatar_url = models.URLField(blank=True, default='')
    phone_number = models.CharField(max_length=20, blank=True, default='')
    is_on_call = models.BooleanField(default=False)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username']

    class Meta:
        ordering = ['-date_joined']

    def __str__(self):
        return f'{self.get_full_name() or self.username} ({self.role})'

    @property
    def is_admin_role(self):
        return self.role == self.Role.ADMIN

    @property
    def is_responder_role(self):
        return self.role in (self.Role.ADMIN, self.Role.RESPONDER)

    @property
    def is_viewer_role(self):
        return True  # All roles can view
