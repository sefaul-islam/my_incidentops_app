"""
URL routing for the authentication API.
"""
from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView

from . import views

app_name = 'authentication'

urlpatterns = [
    # JWT Authentication
    path('register/', views.RegisterView.as_view(), name='register'),
    path('login/', views.LoginView.as_view(), name='login'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token-refresh'),

    # User Profile
    path('me/', views.MeView.as_view(), name='me'),

    # User Management (Admin)
    path('users/', views.UserListView.as_view(), name='user-list'),
    path('users/<int:pk>/role/', views.UserRoleUpdateView.as_view(), name='user-role-update'),

    # OAuth2 Callbacks
    path('oauth/callback/', views.OAuthCallbackView.as_view(), name='oauth-callback'),
]
