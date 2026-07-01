"""
Anomaly detection engine using Isolation Forest.

Uses scikit-learn's IsolationForest to detect anomalies in numerical
incident metrics such as response times, error rates, CPU usage, and memory.
"""
import logging
import numpy as np

logger = logging.getLogger(__name__)

try:
    from sklearn.ensemble import IsolationForest
    SKLEARN_AVAILABLE = True
except ImportError:
    SKLEARN_AVAILABLE = False
    logger.warning('scikit-learn not installed. XAI anomaly detection will use fallback heuristics.')


def detect_anomalies(metrics_data):
    """
    Detect anomalies in numerical metrics using Isolation Forest.

    Args:
        metrics_data: List of dicts, each containing metric name and time-series values.
            Example:
            [
                {'name': 'response_time_ms', 'values': [120, 130, 125, 890, 920, 135]},
                {'name': 'error_rate_pct', 'values': [0.1, 0.2, 0.1, 5.2, 8.1, 0.3]},
                {'name': 'cpu_usage_pct', 'values': [45, 47, 46, 92, 95, 48]},
            ]

    Returns:
        List of anomaly objects with confidence scores and explanations.
    """
    if not metrics_data:
        return []

    anomalies = []

    for metric in metrics_data:
        name = metric.get('name', 'unknown')
        values = metric.get('values', [])

        if len(values) < 4:
            continue  # Not enough data points

        values_arr = np.array(values, dtype=float).reshape(-1, 1)

        if SKLEARN_AVAILABLE:
            anomaly_results = _detect_with_isolation_forest(name, values_arr, values)
        else:
            anomaly_results = _detect_with_zscore(name, values_arr, values)

        anomalies.extend(anomaly_results)

    # Sort by confidence (highest first)
    anomalies.sort(key=lambda x: x['confidence'], reverse=True)
    return anomalies


def _detect_with_isolation_forest(name, values_arr, original_values):
    """Use scikit-learn IsolationForest for anomaly detection."""
    anomalies = []

    model = IsolationForest(
        contamination=0.15,
        random_state=42,
        n_estimators=100,
    )
    model.fit(values_arr)

    predictions = model.predict(values_arr)
    scores = model.decision_function(values_arr)

    for i, (pred, score) in enumerate(zip(predictions, scores)):
        if pred == -1:  # Anomaly detected
            # Convert decision score to a 0-1 confidence scale
            confidence = min(1.0, max(0.0, (0.5 - score) / 0.5))
            anomalies.append({
                'metric': name,
                'index': i,
                'value': float(original_values[i]),
                'confidence': round(confidence, 3),
                'score': round(float(score), 4),
                'type': 'spike' if original_values[i] > np.mean(original_values) else 'drop',
                'explanation': _generate_explanation(
                    name, original_values[i], original_values, confidence,
                ),
            })

    return anomalies


def _detect_with_zscore(name, values_arr, original_values):
    """Fallback: z-score based anomaly detection when sklearn is unavailable."""
    anomalies = []

    mean = np.mean(values_arr)
    std = np.std(values_arr)

    if std == 0:
        return anomalies

    for i, val in enumerate(original_values):
        z_score = abs((val - mean) / std)
        if z_score > 2.0:  # More than 2 standard deviations
            confidence = min(1.0, z_score / 4.0)
            anomalies.append({
                'metric': name,
                'index': i,
                'value': float(val),
                'confidence': round(confidence, 3),
                'score': round(float(-z_score), 4),
                'type': 'spike' if val > mean else 'drop',
                'explanation': _generate_explanation(
                    name, val, original_values, confidence,
                ),
            })

    return anomalies


def _generate_explanation(metric_name, anomalous_value, all_values, confidence):
    """Generate a human-readable explanation for a detected anomaly."""
    mean = np.mean(all_values)
    pct_deviation = abs((anomalous_value - mean) / mean * 100) if mean != 0 else 0

    direction = 'above' if anomalous_value > mean else 'below'
    confidence_label = (
        'High' if confidence > 0.7 else
        'Medium' if confidence > 0.4 else
        'Low'
    )

    readable_name = metric_name.replace('_', ' ').title()

    return (
        f'{confidence_label} confidence anomaly detected in {readable_name}. '
        f'Observed value {anomalous_value:.2f} is {pct_deviation:.1f}% {direction} '
        f'the baseline average of {mean:.2f}.'
    )
