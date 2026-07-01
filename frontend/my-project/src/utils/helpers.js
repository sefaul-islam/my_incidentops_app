/**
 * Utility functions for the IncidentOps frontend.
 */

/**
 * Merge CSS class names, filtering out falsy values.
 * @param  {...string} classes - CSS class names
 * @returns {string} Merged class string
 */
export function classNames(...classes) {
  return classes.filter(Boolean).join(' ');
}

/**
 * Format a date string to a human-readable relative time.
 * @param {string} dateString - ISO date string
 * @returns {string} Relative time (e.g., "5m ago", "2h ago")
 */
export function timeAgo(dateString) {
  const now = new Date();
  const date = new Date(dateString);
  const seconds = Math.floor((now - date) / 1000);

  if (seconds < 60) return 'just now';
  if (seconds < 3600) return `${Math.floor(seconds / 60)}m ago`;
  if (seconds < 86400) return `${Math.floor(seconds / 3600)}h ago`;
  if (seconds < 604800) return `${Math.floor(seconds / 86400)}d ago`;
  return date.toLocaleDateString();
}

/**
 * Get severity badge styling classes.
 * @param {string} severity - Severity level (SEV1, SEV2, SEV3, SEV4)
 * @returns {string} Tailwind class string
 */
export function getSeverityClasses(severity) {
  const map = {
    SEV1: 'bg-rose-500/20 text-rose-300 border-rose-500/30 ring-rose-500/20',
    SEV2: 'bg-amber-500/20 text-amber-300 border-amber-500/30 ring-amber-500/20',
    SEV3: 'bg-yellow-500/20 text-yellow-300 border-yellow-500/30 ring-yellow-500/20',
    SEV4: 'bg-slate-500/20 text-slate-300 border-slate-500/30 ring-slate-500/20',
  };
  return map[severity] || map.SEV4;
}

/**
 * Get severity display label.
 */
export function getSeverityLabel(severity) {
  const map = {
    SEV1: 'Sev-1',
    SEV2: 'Sev-2',
    SEV3: 'Sev-3',
    SEV4: 'Sev-4',
  };
  return map[severity] || severity;
}

/**
 * Get status badge styling.
 */
export function getStatusClasses(status) {
  const map = {
    DECLARED: 'bg-rose-500/20 text-rose-300 border-rose-500/30',
    ACKNOWLEDGED: 'bg-blue-500/20 text-blue-300 border-blue-500/30',
    INVESTIGATING: 'bg-violet-500/20 text-violet-300 border-violet-500/30',
    MITIGATING: 'bg-amber-500/20 text-amber-300 border-amber-500/30',
    RESOLVED: 'bg-emerald-500/20 text-emerald-300 border-emerald-500/30',
    POST_MORTEM: 'bg-slate-500/20 text-slate-300 border-slate-500/30',
  };
  return map[status] || '';
}

/**
 * Get status display label.
 */
export function getStatusLabel(status) {
  const map = {
    DECLARED: 'Declared',
    ACKNOWLEDGED: 'Acknowledged',
    INVESTIGATING: 'Investigating',
    MITIGATING: 'Mitigating',
    RESOLVED: 'Resolved',
    POST_MORTEM: 'Post-Mortem',
  };
  return map[status] || status;
}

/**
 * Format duration between two dates.
 */
export function formatDuration(start, end) {
  if (!start || !end) return '—';
  const ms = new Date(end) - new Date(start);
  const minutes = Math.floor(ms / 60000);
  if (minutes < 60) return `${minutes}m`;
  const hours = Math.floor(minutes / 60);
  if (hours < 24) return `${hours}h ${minutes % 60}m`;
  const days = Math.floor(hours / 24);
  return `${days}d ${hours % 24}h`;
}

/**
 * Get initials from a name.
 */
export function getInitials(name) {
  if (!name) return '?';
  return name
    .split(' ')
    .map(n => n[0])
    .join('')
    .toUpperCase()
    .slice(0, 2);
}
