"""
URL routing for the Incident Management API.
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'incidents', views.IncidentViewSet, basename='incident')
router.register(r'postmortems', views.PostMortemViewSet, basename='postmortem')
router.register(r'oncall', views.OnCallScheduleViewSet, basename='oncall')
router.register(r'escalation-policies', views.EscalationPolicyViewSet, basename='escalation-policy')

urlpatterns = [
    path('', include(router.urls)),
]
