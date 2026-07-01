"""
Post-mortem report generator that assembles the full analysis.

Orchestrates the XAI pipeline:
1. Collect incident timeline and metrics
2. Run anomaly detection on metrics
3. Parse system logs
4. Generate explainable insight cards
5. Assemble the final post-mortem report
"""
import logging
import random
from django.utils import timezone

from ..models import PostMortem, IncidentUpdate
from .analyzer import detect_anomalies
from .log_parser import parse_logs
from .explainer import generate_insight_cards

logger = logging.getLogger(__name__)


def generate_postmortem_report(incident, user):
    """
    Generate a complete post-mortem report for a resolved incident.

    Args:
        incident: Incident model instance (should be in RESOLVED status)
        user: User who triggered the generation

    Returns:
        PostMortem model instance
    """
    logger.info(f'Generating post-mortem for {incident.incident_id}')

    # ── 1. Reconstruct timeline ────────────────────────────────
    timeline_data = _build_timeline(incident)

    # ── 2. Gather metrics (simulated for dev) ──────────────────
    metrics_data = _gather_metrics(incident)

    # ── 3. Run anomaly detection ───────────────────────────────
    anomalies = detect_anomalies(metrics_data)

    # ── 4. Parse logs (simulated for dev) ──────────────────────
    log_text = _gather_logs(incident)
    log_results = parse_logs(log_text)

    # ── 5. Generate XAI insight cards ──────────────────────────
    insight_cards = generate_insight_cards(anomalies, log_results, incident)

    # ── 6. Calculate overall confidence ────────────────────────
    if insight_cards:
        xai_confidence = sum(c.get('confidence', 0) for c in insight_cards) / len(insight_cards)
    else:
        xai_confidence = 0.0

    # ── 7. Generate summary and root cause ─────────────────────
    summary = _generate_summary(incident, insight_cards, log_results)
    root_cause = _generate_root_cause(incident, insight_cards, anomalies)
    impact = _generate_impact(incident)
    action_items = _generate_action_items(insight_cards)

    # ── 8. Persist the post-mortem ─────────────────────────────
    postmortem, created = PostMortem.objects.update_or_create(
        incident=incident,
        defaults={
            'summary': summary,
            'root_cause': root_cause,
            'impact': impact,
            'timeline_data': timeline_data,
            'action_items': action_items,
            'anomalies': insight_cards,
            'xai_confidence': round(xai_confidence, 3),
            'log_highlights': log_results.get('highlights', []),
            'generated_by': user,
        },
    )

    logger.info(
        f'Post-mortem {"created" if created else "updated"} for '
        f'{incident.incident_id} (confidence: {xai_confidence:.2%})'
    )

    return postmortem


def _build_timeline(incident):
    """Reconstruct the incident timeline from IncidentUpdate records."""
    updates = IncidentUpdate.objects.filter(
        incident=incident,
    ).select_related('author').order_by('created_at')

    timeline = []
    for update in updates:
        timeline.append({
            'timestamp': update.created_at.isoformat(),
            'type': update.update_type,
            'message': update.message,
            'author': update.author.get_full_name() if update.author else 'System',
            'old_status': update.old_status,
            'new_status': update.new_status,
        })

    # Add incident creation and resolution as bookends
    timeline.insert(0, {
        'timestamp': incident.created_at.isoformat(),
        'type': 'INCIDENT_DECLARED',
        'message': f'Incident {incident.incident_id} declared: {incident.title}',
        'author': incident.created_by.get_full_name() if incident.created_by else 'Unknown',
        'old_status': '',
        'new_status': 'DECLARED',
    })

    if incident.resolved_at:
        timeline.append({
            'timestamp': incident.resolved_at.isoformat(),
            'type': 'INCIDENT_RESOLVED',
            'message': f'Incident {incident.incident_id} resolved.',
            'author': '',
            'old_status': '',
            'new_status': 'RESOLVED',
        })

    return timeline


def _gather_metrics(incident):
    """
    Gather system metrics related to the incident.

    In production, this would pull from a monitoring system (Prometheus, Datadog, etc.).
    For development, we generate realistic simulated data with injected anomalies.
    """
    import numpy as np

    duration_hours = 6
    data_points = duration_hours * 12  # 5-minute intervals

    # Generate baseline metrics with realistic patterns
    rng = np.random.RandomState(hash(incident.incident_id) % (2**31))

    # Inject anomalies at ~60% through the timeline (simulating the incident)
    anomaly_start = int(data_points * 0.55)
    anomaly_end = int(data_points * 0.75)

    metrics = []

    # Response Time
    response_times = rng.normal(120, 15, data_points).tolist()
    for i in range(anomaly_start, anomaly_end):
        response_times[i] *= rng.uniform(4, 8)
    metrics.append({'name': 'response_time_ms', 'values': response_times})

    # Error Rate
    error_rates = rng.exponential(0.2, data_points).tolist()
    for i in range(anomaly_start, anomaly_end):
        error_rates[i] = rng.uniform(5, 15)
    metrics.append({'name': 'error_rate_pct', 'values': error_rates})

    # CPU Usage
    cpu_usage = rng.normal(45, 8, data_points).tolist()
    for i in range(anomaly_start, anomaly_end):
        cpu_usage[i] = rng.uniform(85, 98)
    metrics.append({'name': 'cpu_usage_pct', 'values': cpu_usage})

    # Memory Usage
    memory_usage = rng.normal(60, 5, data_points).tolist()
    for i in range(anomaly_start, min(anomaly_end + 5, data_points)):
        memory_usage[i] = min(99, memory_usage[i] + rng.uniform(15, 30))
    metrics.append({'name': 'memory_usage_pct', 'values': memory_usage})

    return metrics


def _gather_logs(incident):
    """
    Gather system logs related to the incident.

    In production, this would pull from ELK/Splunk/CloudWatch.
    For development, we generate realistic simulated log entries.
    """
    severity_log_patterns = {
        'SEV1': [
            '2024-01-15T14:23:01Z ERROR [api-gateway] Connection pool exhausted: max connections (100) reached',
            '2024-01-15T14:23:05Z CRITICAL [api-gateway] Request timeout after 30000ms for /api/v2/orders',
            '2024-01-15T14:23:12Z ERROR [db-primary] Lock wait timeout exceeded; try restarting transaction',
            '2024-01-15T14:23:45Z FATAL [worker-3] Out of memory: Java heap space',
            '2024-01-15T14:24:01Z ERROR [api-gateway] Connection refused to downstream service payments-svc:8080',
            '2024-01-15T14:24:15Z ERROR [api-gateway] Circuit breaker OPEN for payments-svc (failures: 23/25)',
            '2024-01-15T14:25:00Z CRITICAL [load-balancer] Health check failed for api-gateway-node-2',
            '2024-01-15T14:25:30Z ERROR [cache] Redis connection reset by peer: redis-cluster-1:6379',
        ],
        'SEV2': [
            '2024-01-15T14:23:01Z ERROR [auth-service] OAuth token validation timeout after 5000ms',
            '2024-01-15T14:23:30Z ERROR [auth-service] Connection refused to identity-provider:443',
            '2024-01-15T14:24:00Z WARN [api-gateway] Elevated error rate: 5.2% (threshold: 1%)',
            '2024-01-15T14:24:15Z ERROR [db-replica] Replication lag exceeded 30 seconds',
            '2024-01-15T14:25:00Z ERROR [cdn] Cache miss rate spike to 45% (baseline: 8%)',
        ],
        'SEV3': [
            '2024-01-15T14:23:01Z WARN [monitoring] Disk usage at 85% on /var/log',
            '2024-01-15T14:23:30Z ERROR [scheduler] Cron job failed: cleanup_temp_files',
            '2024-01-15T14:24:00Z WARN [api] Rate limit approaching for client app-xyz (450/500)',
        ],
    }

    log_lines = severity_log_patterns.get(incident.severity, severity_log_patterns['SEV3'])

    # Add some normal log lines for context
    normal_lines = [
        '2024-01-15T14:20:00Z INFO [api-gateway] Request processed: GET /api/health (200, 12ms)',
        '2024-01-15T14:21:00Z INFO [api-gateway] Request processed: POST /api/v2/orders (201, 45ms)',
        '2024-01-15T14:22:00Z INFO [worker-1] Background job completed: process_webhooks (took 2.3s)',
        '2024-01-15T14:22:30Z DEBUG [cache] Cache hit ratio: 92.1%',
    ]

    all_lines = normal_lines + log_lines
    all_lines.sort()  # Sort by timestamp
    return '\n'.join(all_lines)


def _generate_summary(incident, insight_cards, log_results):
    """Generate an executive summary of the incident post-mortem."""
    card_count = len(insight_cards)
    high_conf = sum(1 for c in insight_cards if c.get('confidence', 0) > 0.6)
    categories = log_results.get('categories', {})

    duration = ''
    if incident.resolved_at and incident.created_at:
        delta = incident.resolved_at - incident.created_at
        hours = delta.total_seconds() / 3600
        if hours >= 1:
            duration = f'{hours:.1f} hours'
        else:
            duration = f'{int(delta.total_seconds() / 60)} minutes'

    summary = (
        f'Post-mortem analysis for {incident.incident_id} ({incident.get_severity_display()}). '
    )
    if duration:
        summary += f'The incident lasted {duration}. '

    summary += (
        f'The XAI analysis identified {card_count} insights, '
        f'{high_conf} with high confidence. '
    )

    if categories:
        top_category = max(categories, key=categories.get)
        summary += (
            f'The most prevalent log pattern was "{top_category}" '
            f'with {categories[top_category]} occurrences.'
        )

    return summary


def _generate_root_cause(incident, insight_cards, anomalies):
    """Generate a root cause hypothesis based on XAI insights."""
    if not insight_cards:
        return 'Insufficient data to determine root cause automatically. Manual investigation required.'

    # Use the highest-confidence insight as the primary root cause
    top_insight = insight_cards[0]

    root_cause = f'Primary hypothesis (confidence: {top_insight["confidence"]:.0%}): '
    root_cause += top_insight['description']

    if len(insight_cards) > 1:
        root_cause += '\n\nContributing factors:\n'
        for card in insight_cards[1:4]:
            root_cause += f'  • {card["title"]}: {card["description"]}\n'

    return root_cause


def _generate_impact(incident):
    """Generate an impact assessment."""
    severity_impact = {
        'SEV1': 'Critical — Service was fully unavailable or severely degraded for all users.',
        'SEV2': 'High — Significant functionality was impaired for a subset of users.',
        'SEV3': 'Medium — Minor functionality was affected with limited user impact.',
        'SEV4': 'Low — Cosmetic or minor issue with negligible user impact.',
    }

    impact = severity_impact.get(incident.severity, 'Unknown impact level.')

    affected = incident.affected_services
    if affected:
        services_str = ', '.join(affected) if isinstance(affected, list) else str(affected)
        impact += f'\n\nAffected services: {services_str}'

    return impact


def _generate_action_items(insight_cards):
    """Extract action items from XAI insight recommendations."""
    actions = []
    seen = set()

    for card in insight_cards:
        rec = card.get('recommendation', '')
        if rec and rec not in seen:
            seen.add(rec)
            actions.append({
                'title': card['title'],
                'action': rec,
                'priority': 'P1' if card.get('confidence', 0) > 0.7 else 'P2',
                'status': 'open',
            })

    return actions
