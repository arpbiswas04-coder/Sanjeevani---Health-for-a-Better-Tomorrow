import React from 'react';
import { Activity } from 'lucide-react';

interface LoadingScreenProps {
  message?: string;
  subtext?: string;
}

export const LoadingScreen: React.FC<LoadingScreenProps> = ({
  message = 'Initializing Health Resource Mesh...',
  subtext = 'Synchronizing real-time telemetry from edge nodes',
}) => {
  return (
    <div className="min-h-[60vh] flex flex-col items-center justify-center p-6 text-center animate-in fade-in duration-300">
      <div className="relative flex items-center justify-center">
        {/* Pulse rings */}
        <div className="absolute w-24 h-24 rounded-full bg-emerald-500/10 animate-ping" />
        <div className="absolute w-16 h-16 rounded-full bg-teal-500/20 animate-pulse" />
        
        {/* Central Icon */}
        <div className="relative p-4 bg-slate-900 border border-emerald-500/40 rounded-2xl shadow-xl shadow-emerald-500/10 text-emerald-400">
          <Activity className="w-8 h-8 animate-pulse" />
        </div>
      </div>

      <h3 className="mt-6 text-base font-semibold text-slate-100">{message}</h3>
      <p className="mt-1 text-xs text-slate-400 max-w-sm">{subtext}</p>
    </div>
  );
};
