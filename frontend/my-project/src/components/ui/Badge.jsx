/**
 * Severity and status badge component.
 */
import React from 'react';
import { classNames, getSeverityClasses, getSeverityLabel, getStatusClasses, getStatusLabel } from '../../utils/helpers';

export function Badge({ type = 'severity', value, size = 'sm', pulse = false, className = '' }) {
  const isSeverity = type === 'severity';
  const classes = isSeverity ? getSeverityClasses(value) : getStatusClasses(value);
  const label = isSeverity ? getSeverityLabel(value) : getStatusLabel(value);

  const sizeClasses = {
    xs: 'text-[10px] px-1.5 py-0.5',
    sm: 'text-xs px-2 py-0.5',
    md: 'text-sm px-2.5 py-1',
  };

  return (
    <span
      className={classNames(
        'inline-flex items-center font-semibold rounded-full border',
        'transition-all duration-200',
        classes,
        sizeClasses[size],
        pulse && 'animate-pulse',
        className,
      )}
    >
      {pulse && (
        <span className="relative flex h-2 w-2 mr-1.5">
          <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-current opacity-75" />
          <span className="relative inline-flex rounded-full h-2 w-2 bg-current" />
        </span>
      )}
      {label}
    </span>
  );
}
