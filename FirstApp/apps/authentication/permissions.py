"""
DRF permission classes for Role-Based Access Control.
"""
from rest_framework.permissions import BasePermission


class IsAdmin(BasePermission):
    """Allow access only to users with the ADMIN role."""

    def has_permission(self, request, view):
        return (
            request.user
            and request.user.is_authenticated
            and request.user.role == 'ADMIN'
        )


class IsResponder(BasePermission):
    """Allow access to ADMIN and RESPONDER roles."""

    def has_permission(self, request, view):
        return (
            request.user
            and request.user.is_authenticated
            and request.user.role in ('ADMIN', 'RESPONDER')
        )


class IsViewer(BasePermission):
    """Allow access to any authenticated user (all roles can view)."""

    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated


class IsAdminOrResponder(BasePermission):
    """
    Allow full CRUD to ADMIN/RESPONDER roles.
    VIEWER gets read-only access.
    """

    def has_permission(self, request, view):
        if not (request.user and request.user.is_authenticated):
            return False
        # Safe methods (GET, HEAD, OPTIONS) are allowed for all authenticated users
        if request.method in ('GET', 'HEAD', 'OPTIONS'):
            return True
        # Write methods require ADMIN or RESPONDER role
        return request.user.role in ('ADMIN', 'RESPONDER')
