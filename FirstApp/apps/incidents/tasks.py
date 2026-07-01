"""
Celery tasks for asynchronous incident operations.
"""
import logging
from celery import shared_task
from django.conf import settings
from django.utils import timezone
from datetime import timedelta

logger = logging.getLogger(__name__)


@shared_task(name='incidents.check_escalation_timeouts')
def check_escalation_timeouts():
    """
    Periodic task that checks for unacknowledged incidents past their
    escalation timeout and triggers alerts.

    This runs every minute via Celery Beat.
    """
    from .models import Incident, IncidentUpdate, EscalationPolicy, OnCallSchedule

    timeout = getattr(settings, 'ESCALATION_TIMEOUT_MINUTES', 15)
    cutoff = timezone.now() - timedelta(minutes=timeout)

    # Find Sev-1 and Sev-2 incidents that are still DECLARED and past timeout
    stale_incidents = Incident.objects.filter(
        status='DECLARED',
        severity__in=['SEV1', 'SEV2'],
        created_at__lte=cutoff,
    )

    for incident in stale_incidents:
        logger.warning(
            f'Escalation triggered for {incident.incident_id} '
            f'({incident.severity}) — unacknowledged for >{timeout} minutes'
        )

        # Create escalation timeline entry
        IncidentUpdate.objects.create(
            incident=incident,
            author=None,  # System-generated
            update_type='ESCALATION',
            message=(
                f'⚠️ AUTO-ESCALATION: {incident.incident_id} has been unacknowledged '
                f'for over {timeout} minutes. On-call team has been notified.'
            ),
        )

        # Notify on-call responders
        send_escalation_alert.delay(incident.id)


@shared_task(name='incidents.send_escalation_alert')
def send_escalation_alert(incident_id):
    """
    Send escalation notifications to on-call responders.

    In production, this would integrate with PagerDuty/Slack/Email.
    For dev, it logs the alert.
    """
    from .models import Incident, OnCallSchedule

    try:
        incident = Incident.objects.get(id=incident_id)
    except Incident.DoesNotExist:
        logger.error(f'Incident {incident_id} not found for escalation alert.')
        return

    oncall_schedules = OnCallSchedule.get_current_oncall()

    if oncall_schedules.exists():
        for schedule in oncall_schedules:
            logger.info(
                f'📟 ALERT to {schedule.user.email}: '
                f'{incident.incident_id} — {incident.title} ({incident.severity})'
            )
            # In production: send email, Slack message, or PagerDuty trigger here
    else:
        logger.warning(
            f'No on-call responders found for escalation of {incident.incident_id}'
        )


@shared_task(name='incidents.send_alert_notification')
def send_alert_notification(user_id, incident_id, message):
    """
    Send a notification to a specific user about an incident.
    """
    from django.contrib.auth import get_user_model
    from .models import Incident

    User = get_user_model()

    try:
        user = User.objects.get(id=user_id)
        incident = Incident.objects.get(id=incident_id)
    except (User.DoesNotExist, Incident.DoesNotExist) as e:
        logger.error(f'Alert notification failed: {e}')
        return

    logger.info(
        f'🔔 Notification to {user.email}: '
        f'{incident.incident_id} — {message}'
    )


@shared_task(name='incidents.generate_postmortem_async')
def generate_postmortem_async(incident_id, user_id):
    """
    Asynchronously generate a post-mortem report for a resolved incident.
    """
    from django.contrib.auth import get_user_model
    from .models import Incident
    from .xai.report_generator import generate_postmortem_report

    User = get_user_model()

    try:
        incident = Incident.objects.get(id=incident_id)
        user = User.objects.get(id=user_id)
    except (Incident.DoesNotExist, User.DoesNotExist) as e:
        logger.error(f'Post-mortem generation failed: {e}')
        return

    postmortem = generate_postmortem_report(incident, user)
    logger.info(f'Post-mortem generated for {incident.incident_id}')
    return postmortem.id
