"""
Log parser for extracting structured information from system logs.

Uses regex patterns to identify error patterns, frequency spikes,
and cluster recurring log messages for post-mortem analysis.
"""
import re
import logging
from collections import Counter, defaultdict

logger = logging.getLogger(__name__)

# Common log patterns
ERROR_PATTERNS = [
    (r'(?i)(error|exception|fatal|critical|panic)[\s:]+(.+)', 'error'),
    (r'(?i)(timeout|timed?\s*out)[\s:]+(.+)', 'timeout'),
    (r'(?i)(connection\s*(refused|reset|closed|failed))(.+)?', 'connection'),
    (r'(?i)(out\s*of\s*memory|oom|memory\s*exhausted)', 'memory'),
    (r'(?i)(disk\s*(full|space)|no\s*space\s*left)', 'disk'),
    (r'(?i)(permission\s*denied|access\s*denied|unauthorized|forbidden)', 'auth'),
    (r'(?i)(rate\s*limit|throttl|429)', 'rate_limit'),
    (r'(?i)(deadlock|lock\s*timeout|lock\s*wait)', 'deadlock'),
    (r'(?i)(segfault|segmentation\s*fault|sigsegv)', 'crash'),
    (r'(?i)(dns\s*(resolution|lookup)\s*fail)', 'dns'),
]

# Timestamp pattern for log line parsing
TIMESTAMP_PATTERN = re.compile(
    r'(\d{4}-\d{2}-\d{2}[T ]\d{2}:\d{2}:\d{2}(?:\.\d+)?(?:Z|[+-]\d{2}:?\d{2})?)'
)


def parse_logs(log_text):
    """
    Parse raw log text and extract structured insights.

    Args:
        log_text: Raw log text string (multi-line).

    Returns:
        Dict with:
            - errors: List of matched error entries
            - categories: Counter of error categories
            - frequency_spikes: Time periods with unusual error density
            - highlights: Top log lines to feature in post-mortem
    """
    if not log_text or not log_text.strip():
        return {
            'errors': [],
            'categories': {},
            'frequency_spikes': [],
            'highlights': [],
        }

    lines = log_text.strip().split('\n')
    errors = []
    categories = Counter()
    time_buckets = defaultdict(int)

    for line_num, line in enumerate(lines, 1):
        line = line.strip()
        if not line:
            continue

        for pattern, category in ERROR_PATTERNS:
            match = re.search(pattern, line)
            if match:
                # Extract timestamp if present
                ts_match = TIMESTAMP_PATTERN.search(line)
                timestamp = ts_match.group(1) if ts_match else None

                errors.append({
                    'line_number': line_num,
                    'line': line[:500],  # Truncate very long lines
                    'category': category,
                    'pattern_match': match.group(0)[:200],
                    'timestamp': timestamp,
                })

                categories[category] += 1

                # Bucket by minute for frequency analysis
                if timestamp:
                    bucket = timestamp[:16]  # YYYY-MM-DDTHH:MM
                    time_buckets[bucket] += 1

                break  # Only match first pattern per line

    # Detect frequency spikes
    frequency_spikes = _detect_frequency_spikes(time_buckets)

    # Select top highlights for the post-mortem
    highlights = _select_highlights(errors)

    return {
        'errors': errors,
        'categories': dict(categories),
        'frequency_spikes': frequency_spikes,
        'highlights': highlights,
    }


def _detect_frequency_spikes(time_buckets):
    """Identify time periods with unusually high error frequency."""
    if not time_buckets:
        return []

    counts = list(time_buckets.values())
    if len(counts) < 3:
        return []

    import numpy as np
    mean = np.mean(counts)
    std = np.std(counts)

    if std == 0:
        return []

    spikes = []
    for bucket, count in sorted(time_buckets.items()):
        z_score = (count - mean) / std
        if z_score > 1.5:
            spikes.append({
                'timestamp': bucket,
                'error_count': count,
                'z_score': round(z_score, 2),
                'severity': 'high' if z_score > 3 else 'medium' if z_score > 2 else 'low',
            })

    return sorted(spikes, key=lambda x: x['z_score'], reverse=True)


def _select_highlights(errors, max_highlights=10):
    """Select the most significant log lines for the post-mortem."""
    # Prioritize by category severity
    priority = {
        'crash': 10, 'memory': 9, 'deadlock': 8,
        'error': 7, 'timeout': 6, 'connection': 5,
        'disk': 4, 'auth': 3, 'rate_limit': 2, 'dns': 1,
    }

    sorted_errors = sorted(
        errors,
        key=lambda e: priority.get(e['category'], 0),
        reverse=True,
    )

    # Deduplicate similar messages
    seen = set()
    highlights = []
    for error in sorted_errors:
        # Use first 80 chars as dedup key
        key = error['line'][:80]
        if key not in seen:
            seen.add(key)
            highlights.append({
                'line_number': error['line_number'],
                'line': error['line'],
                'category': error['category'],
                'timestamp': error['timestamp'],
            })
        if len(highlights) >= max_highlights:
            break

    return highlights
