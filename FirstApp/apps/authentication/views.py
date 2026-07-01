"""
Views for authentication, JWT token management, and OAuth2 callbacks.
"""
from rest_framework import generics, permissions, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import get_user_model

from .serializers import (
    UserRegistrationSerializer,
    UserProfileSerializer,
    UserListSerializer,
    UserRoleUpdateSerializer,
    OAuthCallbackSerializer,
)
from .permissions import IsAdmin

User = get_user_model()


def get_tokens_for_user(user):
    """Generate JWT access and refresh tokens for a user."""
    refresh = RefreshToken.for_user(user)
    return {
        'refresh': str(refresh),
        'access': str(refresh.access_token),
    }


class RegisterView(generics.CreateAPIView):
    """POST /api/auth/register/ — Create a new user account."""

    queryset = User.objects.all()
    serializer_class = UserRegistrationSerializer
    permission_classes = [permissions.AllowAny]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        tokens = get_tokens_for_user(user)
        return Response(
            {
                'user': UserProfileSerializer(user).data,
                'tokens': tokens,
            },
            status=status.HTTP_201_CREATED,
        )


class LoginView(APIView):
    """POST /api/auth/login/ — Authenticate with email and password."""

    permission_classes = [permissions.AllowAny]

    def post(self, request):
        email = request.data.get('email')
        password = request.data.get('password')

        if not email or not password:
            return Response(
                {'error': 'Email and password are required.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            return Response(
                {'error': 'Invalid credentials.'},
                status=status.HTTP_401_UNAUTHORIZED,
            )

        if not user.check_password(password):
            return Response(
                {'error': 'Invalid credentials.'},
                status=status.HTTP_401_UNAUTHORIZED,
            )

        tokens = get_tokens_for_user(user)
        return Response({
            'user': UserProfileSerializer(user).data,
            'tokens': tokens,
        })


class MeView(generics.RetrieveUpdateAPIView):
    """GET/PATCH /api/auth/me/ — View or update the current user's profile."""

    serializer_class = UserProfileSerializer

    def get_object(self):
        return self.request.user


class UserListView(generics.ListAPIView):
    """GET /api/auth/users/ — List all users (for assignee dropdowns, admin panel)."""

    queryset = User.objects.all()
    serializer_class = UserListSerializer


class UserRoleUpdateView(generics.UpdateAPIView):
    """PATCH /api/auth/users/<id>/role/ — Admin-only role update."""

    queryset = User.objects.all()
    serializer_class = UserRoleUpdateSerializer
    permission_classes = [IsAdmin]


class OAuthCallbackView(APIView):
    """
    POST /api/auth/oauth/callback/ — Exchange OAuth2 authorization code for JWT tokens.

    Accepts { "code": "...", "provider": "google"|"github" }
    Validates the code with the provider, creates or retrieves the user, and returns JWT tokens.
    """

    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = OAuthCallbackSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        provider = serializer.validated_data['provider']
        code = serializer.validated_data['code']

        try:
            user_info = self._exchange_code(provider, code)
        except Exception as e:
            return Response(
                {'error': f'OAuth authentication failed: {str(e)}'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Find or create user
        user, created = User.objects.get_or_create(
            email=user_info['email'],
            defaults={
                'username': user_info.get('username', user_info['email'].split('@')[0]),
                'first_name': user_info.get('first_name', ''),
                'last_name': user_info.get('last_name', ''),
                'avatar_url': user_info.get('avatar_url', ''),
                'role': User.Role.VIEWER,
            },
        )

        if not created and user_info.get('avatar_url'):
            user.avatar_url = user_info['avatar_url']
            user.save(update_fields=['avatar_url'])

        tokens = get_tokens_for_user(user)
        return Response({
            'user': UserProfileSerializer(user).data,
            'tokens': tokens,
            'created': created,
        })

    def _exchange_code(self, provider, code):
        """Exchange authorization code with the OAuth provider for user info."""
        import requests
        from django.conf import settings

        if provider == 'google':
            # Exchange code for access token
            token_resp = requests.post(
                'https://oauth2.googleapis.com/token',
                data={
                    'code': code,
                    'client_id': settings.SOCIALACCOUNT_PROVIDERS['google']['APP']['client_id'],
                    'client_secret': settings.SOCIALACCOUNT_PROVIDERS['google']['APP']['secret'],
                    'redirect_uri': f"{settings.CORS_ALLOWED_ORIGINS[0]}/auth/callback/google",
                    'grant_type': 'authorization_code',
                },
                timeout=10,
            )
            token_resp.raise_for_status()
            access_token = token_resp.json()['access_token']

            # Get user info
            info_resp = requests.get(
                'https://www.googleapis.com/oauth2/v2/userinfo',
                headers={'Authorization': f'Bearer {access_token}'},
                timeout=10,
            )
            info_resp.raise_for_status()
            info = info_resp.json()

            return {
                'email': info['email'],
                'first_name': info.get('given_name', ''),
                'last_name': info.get('family_name', ''),
                'avatar_url': info.get('picture', ''),
                'username': info['email'].split('@')[0],
            }

        elif provider == 'github':
            from django.conf import settings as django_settings

            # Exchange code for access token
            token_resp = requests.post(
                'https://github.com/login/oauth/access_token',
                data={
                    'code': code,
                    'client_id': django_settings.SOCIALACCOUNT_PROVIDERS['github']['APP']['client_id'],
                    'client_secret': django_settings.SOCIALACCOUNT_PROVIDERS['github']['APP']['secret'],
                },
                headers={'Accept': 'application/json'},
                timeout=10,
            )
            token_resp.raise_for_status()
            access_token = token_resp.json()['access_token']

            # Get user info
            info_resp = requests.get(
                'https://api.github.com/user',
                headers={'Authorization': f'Bearer {access_token}'},
                timeout=10,
            )
            info_resp.raise_for_status()
            info = info_resp.json()

            # Get primary email
            email_resp = requests.get(
                'https://api.github.com/user/emails',
                headers={'Authorization': f'Bearer {access_token}'},
                timeout=10,
            )
            email_resp.raise_for_status()
            primary_email = next(
                (e['email'] for e in email_resp.json() if e.get('primary')),
                info.get('email', ''),
            )

            name_parts = (info.get('name') or '').split(' ', 1)
            return {
                'email': primary_email,
                'first_name': name_parts[0] if name_parts else '',
                'last_name': name_parts[1] if len(name_parts) > 1 else '',
                'avatar_url': info.get('avatar_url', ''),
                'username': info.get('login', primary_email.split('@')[0]),
            }

        raise ValueError(f'Unsupported provider: {provider}')
