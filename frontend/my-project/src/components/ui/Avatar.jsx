/**
 * Avatar component with fallback initials.
 */
import React from 'react';
import { classNames, getInitials } from '../../utils/helpers';

const sizeMap = {
  xs: 'w-6 h-6 text-[10px]',
  sm: 'w-8 h-8 text-xs',
  md: 'w-10 h-10 text-sm',
  lg: 'w-12 h-12 text-base',
};

const colorMap = [
  'bg-blue-500/20 text-blue-300 ring-blue-500/30',
  'bg-violet-500/20 text-violet-300 ring-violet-500/30',
  'bg-emerald-500/20 text-emerald-300 ring-emerald-500/30',
  'bg-amber-500/20 text-amber-300 ring-amber-500/30',
  'bg-rose-500/20 text-rose-300 ring-rose-500/30',
  'bg-cyan-500/20 text-cyan-300 ring-cyan-500/30',
];

function hashString(str) {
  let hash = 0;
  for (let i = 0; i < str.length; i++) {
    hash = str.charCodeAt(i) + ((hash << 5) - hash);
  }
  return Math.abs(hash);
}

export function Avatar({ name, avatarUrl, size = 'sm', className = '' }) {
  const initials = getInitials(name);
  const colorIndex = hashString(name || '') % colorMap.length;

  if (avatarUrl) {
    return (
      <img
        src={avatarUrl}
        alt={name}
        className={classNames(
          'rounded-full ring-1 ring-white/10 object-cover',
          sizeMap[size],
          className,
        )}
      />
    );
  }

  return (
    <div
      className={classNames(
        'rounded-full ring-1 flex items-center justify-center font-semibold',
        sizeMap[size],
        colorMap[colorIndex],
        className,
      )}
      title={name}
    >
      {initials}
    </div>
  );
}
