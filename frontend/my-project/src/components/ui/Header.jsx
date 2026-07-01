/**
 * Top header component with search and actions.
 */
import React from 'react';
import { classNames } from '../../utils/helpers';

export function Header({ title, subtitle, isConnected, children }) {
  return (
    <header className="h-16 border-b border-white/5 bg-slate-900/30 backdrop-blur-xl flex items-center justify-between px-4 sm:px-6 lg:px-8">
      <div className="flex items-center gap-3">
        <h1 className="text-xl font-bold text-white tracking-tight">{title}</h1>
        {subtitle && (
          <span className="text-sm text-slate-500 hidden sm:inline">{subtitle}</span>
        )}
        {/* Live connection indicator */}
        {typeof isConnected === 'boolean' && (
          <div className="flex items-center gap-1.5 ml-2">
            <span className={classNames(
              'relative flex h-2 w-2',
            )}>
              {isConnected && (
                <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75" />
              )}
              <span className={classNames(
                'relative inline-flex rounded-full h-2 w-2',
                isConnected ? 'bg-emerald-400' : 'bg-slate-600',
              )} />
            </span>
            <span className={classNames(
              'text-xs font-medium',
              isConnected ? 'text-emerald-400' : 'text-slate-600',
            )}>
              {isConnected ? 'Live' : 'Offline'}
            </span>
          </div>
        )}
      </div>

      <div className="flex items-center gap-3">
        {children}
      </div>
    </header>
  );
}
