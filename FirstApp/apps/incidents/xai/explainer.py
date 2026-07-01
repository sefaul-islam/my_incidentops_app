"""
Explainable AI (XAI) insight generator.

Produces human-readable "insight cards" for each anomaly, including:
- Confidence score
- Plain-English explanation
- Contributing feature rankings
- Recommended actions
"""
import logging

logger = logging.getLogger(__name__)


def generate_insight_cards(anomalies, log_results, incident):
    """
    Generate XAI insight cards combining anomaly detections with log analysis.

    Args:
        anomalies: List of anomaly dicts from analyzer.detect_anomalies()
        log_results: Dict from log_parser.parse_logs()
        incident: The Incident model instance

    Returns:
        List of insight card dicts ready for frontend rendering.
    """
    cards = []

    # ── Anomaly-based insights ─────────────────────────────────
    for anomaly in anomalies:
        card = {
            'type': 'anomaly',
            'title': f'Anomaly in {_readable_metric(anomaly["metric"])}',
            'confidence': anomaly['confidence'],
            'confidence_label': _confidence_label(anomaly['confidence']),
            'severity': _anomaly_severity(anomaly['confidence']),
            'description': anomaly['explanation'],
            'metric_name': anomaly['metric'],
            'observed_value': anomaly['value'],
            'anomaly_type': anomaly['type'],
            'features': _rank_contributing_features(anomaly, log_results),
            'recommendation': _generate_recommendation(anomaly, incident),
        }
        cards.append(card)

    # ── Log pattern insights ───────────────────────────────────
    if log_results and log_results.get('categories'):
        categories = log_results['categories']
        total_errors = sum(categories.values())

        for category, count in sorted(categories.items(), key=lambda x: -x[1]):
            pct = (count / total_errors * 100) if total_errors > 0 else 0
            card = {
                'type': 'log_pattern',
                'title': f'{_readable_category(category)} Pattern Detected',
                'confidence': min(1.0, count / max(total_errors * 0.5, 1)),
                'confidence_label': _confidence_label(min(1.0, count / max(total_errors * 0.5, 1))),
                'severity': 'critical' if category in ('crash', 'memory', 'deadlock') else 'warning',
                'description': (
                    f'Detected {count} occurrences of {_readable_category(category).lower()} '
                    f'events ({pct:.1f}% of all errors). '
                    f'{_category_explanation(category)}'
                ),
                'category': category,
                'occurrence_count': count,
                'percentage': round(pct, 1),
                'recommendation': _category_recommendation(category),
            }
            cards.append(card)

    # ── Frequency spike insights ───────────────────────────────
    if log_results and log_results.get('frequency_spikes'):
        for spike in log_results['frequency_spikes'][:3]:  # Top 3 spikes
            card = {
                'type': 'frequency_spike',
                'title': f'Error Frequency Spike at {spike["timestamp"]}',
                'confidence': min(1.0, spike['z_score'] / 4.0),
                'confidence_label': _confidence_label(min(1.0, spike['z_score'] / 4.0)),
                'severity': spike['severity'],
                'description': (
                    f'Error rate spiked to {spike["error_count"]} errors/min at '
                    f'{spike["timestamp"]}, which is {spike["z_score"]}x standard deviations '
                    f'above normal.'
                ),
                'timestamp': spike['timestamp'],
                'error_count': spike['error_count'],
            }
            cards.append(card)

    # Sort by confidence
    cards.sort(key=lambda c: c.get('confidence', 0), reverse=True)
    return cards


def _readable_metric(name):
    """Convert metric_name to human-readable format."""
    return name.replace('_', ' ').title()


def _readable_category(category):
    """Convert category to human-readable format."""
    mapping = {
        'error': 'Error/Exception',
        'timeout': 'Timeout',
        'connection': 'Connection Failure',
        'memory': 'Memory Exhaustion',
        'disk': 'Disk Space',
        'auth': 'Authentication/Authorization',
        'rate_limit': 'Rate Limiting',
        'deadlock': 'Deadlock',
        'crash': 'Process Crash',
        'dns': 'DNS Resolution',
    }
    return mapping.get(category, category.title())


def _confidence_label(confidence):
    """Map confidence score to a human-readable label."""
    if confidence >= 0.8:
        return 'Very High'
    elif confidence >= 0.6:
        return 'High'
    elif confidence >= 0.4:
        return 'Medium'
    elif confidence >= 0.2:
        return 'Low'
    return 'Very Low'


def _anomaly_severity(confidence):
    """Map anomaly confidence to a severity level."""
    if confidence >= 0.7:
        return 'critical'
    elif confidence >= 0.4:
        return 'warning'
    return 'info'


def _rank_contributing_features(anomaly, log_results):
    """
    Rank contributing features for an anomaly.
    Simulates feature importance ranking for explainability.
    """
    features = [
        {
            'name': anomaly['metric'],
            'importance': round(anomaly['confidence'] * 0.8, 3),
            'description': f'Primary metric showing {anomaly["type"]}',
        },
    ]

    # Check if logs correlate with the anomaly
    if log_results and log_results.get('categories'):
        for category, count in log_results['categories'].items():
            if count > 2:
                features.append({
                    'name': f'log_{category}_count',
                    'importance': round(min(0.5, count * 0.05), 3),
                    'description': f'{count} {_readable_category(category).lower()} events in logs',
                })

    features.sort(key=lambda f: f['importance'], reverse=True)
    return features[:5]  # Top 5 features


def _generate_recommendation(anomaly, incident):
    """Generate actionable recommendations based on anomaly type and metric."""
    metric = anomaly['metric'].lower()
    anomaly_type = anomaly['type']

    if 'latency' in metric or 'response_time' in metric:
        if anomaly_type == 'spike':
            return 'Investigate upstream dependencies for latency increases. Check database query performance and external API response times.'
    elif 'error_rate' in metric:
        return 'Review application logs for new exception patterns. Check recent deployments for regressions.'
    elif 'cpu' in metric:
        return 'Investigate CPU-intensive processes. Consider horizontal scaling or optimizing hot code paths.'
    elif 'memory' in metric:
        return 'Check for memory leaks in long-running processes. Review recent code changes for unbounded data structures.'
    elif 'disk' in metric:
        return 'Clean up old log files and temporary data. Consider expanding storage or implementing log rotation.'

    return 'Review system metrics and logs around the time of the anomaly to identify the root cause.'


def _category_explanation(category):
    """Provide context for a log error category."""
    explanations = {
        'error': 'General errors may indicate application bugs or unhandled edge cases.',
        'timeout': 'Timeouts suggest network issues or overloaded downstream services.',
        'connection': 'Connection failures indicate network or service availability issues.',
        'memory': 'Memory exhaustion can cause OOM kills and cascading failures.',
        'disk': 'Disk space issues can halt logging, database writes, and deployments.',
        'auth': 'Auth failures may indicate misconfigured credentials or security incidents.',
        'rate_limit': 'Rate limiting suggests traffic spikes or misconfigured API clients.',
        'deadlock': 'Deadlocks indicate concurrent access conflicts in the database.',
        'crash': 'Process crashes are critical and may indicate memory corruption or bugs.',
        'dns': 'DNS failures prevent service discovery and inter-service communication.',
    }
    return explanations.get(category, '')


def _category_recommendation(category):
    """Generate recommendations for a log error category."""
    recommendations = {
        'error': 'Add structured error handling and alerting for uncaught exceptions.',
        'timeout': 'Implement circuit breakers and increase timeout thresholds if appropriate.',
        'connection': 'Verify network connectivity and health check configurations.',
        'memory': 'Set memory limits, implement graceful degradation, and investigate leaks.',
        'disk': 'Implement log rotation, archive old data, and set disk usage alerts.',
        'auth': 'Rotate credentials, verify OAuth configurations, and audit access logs.',
        'rate_limit': 'Implement request queuing and back-off strategies.',
        'deadlock': 'Review database transaction isolation levels and locking patterns.',
        'crash': 'Analyze core dumps, implement crash recovery, and add health checks.',
        'dns': 'Configure DNS caching, add fallback resolvers, and monitor TTLs.',
    }
    return recommendations.get(category, 'Investigate and address the root cause.')
