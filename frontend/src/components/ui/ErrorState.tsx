import React from 'react';
import { AlertOctagon, RefreshCw } from 'lucide-react';

interface ErrorStateProps {
  title?: string;
  message?: string;
  onRetry?: () => void;
  error?: Error | null;
}

export const ErrorState: React.FC<ErrorStateProps> = ({
  title = 'Telemetry Synchronization Error',
  message = 'Failed to establish connection with the central command backend.',
  onRetry,
  error,
}) => {
  return (
    <div className="min-h-[50vh] flex flex-col items-center justify-center p-6 text-center">
      <div className="p-4 bg-rose-500/10 border border-rose-500/20 rounded-2xl text-rose-400 mb-4 shadow-lg shadow-rose-500/5">
        <AlertOctagon className="w-8 h-8" />
      </div>

      <h3 className="text-lg font-bold text-slate-100">{title}</h3>
      <p className="mt-1.5 text-xs text-slate-400 max-w-md">{message}</p>

      {error && (
        <div className="mt-3 p-3 bg-slate-900 border border-slate-800 rounded-lg text-left max-w-md w-full">
          <code className="text-[11px] font-mono text-rose-300 break-words block">
            {error.message || String(error)}
          </code>
        </div>
      )}

      {onRetry && (
        <button
          onClick={onRetry}
          className="mt-5 inline-flex items-center gap-2 px-4 py-2 bg-slate-800 hover:bg-slate-700 text-slate-100 text-xs font-semibold rounded-xl border border-slate-700 hover:border-slate-600 transition-all shadow-sm"
        >
          <RefreshCw className="w-3.5 h-3.5" />
          <span>Retry Connection</span>
        </button>
      )}
    </div>
  );
};
