import React from 'react';
import { RiskLevel } from '@/types';

interface BadgeProps {
  level?: RiskLevel | 'info' | 'success';
  children: React.ReactNode;
}

export const Badge: React.FC<BadgeProps> = ({ level = 'info', children }) => {
  const styles: Record<string, string> = {
    low: 'bg-emerald-500/10 text-emerald-400 border-emerald-500/30',
    moderate: 'bg-amber-500/10 text-amber-400 border-amber-500/30',
    high: 'bg-orange-500/10 text-orange-400 border-orange-500/30',
    critical: 'bg-rose-500/10 text-rose-400 border-rose-500/30',
    info: 'bg-blue-500/10 text-blue-400 border-blue-500/30',
    success: 'bg-emerald-500/10 text-emerald-400 border-emerald-500/30',
  };

  return (
    <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium border ${styles[level] || styles.info}`}>
      {children}
    </span>
  );
};
