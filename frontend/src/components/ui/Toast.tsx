import React, { useEffect } from 'react';
import { ToastItem } from '@/store/uiStore';
import { CheckCircle2, AlertTriangle, AlertOctagon, Info, X } from 'lucide-react';

interface ToastProps {
  toast: ToastItem;
  onDismiss: (id: string) => void;
}

export const Toast: React.FC<ToastProps> = ({ toast, onDismiss }) => {
  useEffect(() => {
    if (!toast.duration) return;
    const timer = setTimeout(() => {
      onDismiss(toast.id);
    }, toast.duration);
    return () => clearTimeout(timer);
  }, [toast, onDismiss]);

  const typeStyles = {
    success: {
      border: 'border-emerald-500/40',
      bg: 'bg-slate-900/90 shadow-emerald-500/10',
      icon: <CheckCircle2 className="w-5 h-5 text-emerald-400 shrink-0" />,
      progress: 'bg-emerald-500',
    },
    warning: {
      border: 'border-amber-500/40',
      bg: 'bg-slate-900/90 shadow-amber-500/10',
      icon: <AlertTriangle className="w-5 h-5 text-amber-400 shrink-0" />,
      progress: 'bg-amber-500',
    },
    error: {
      border: 'border-rose-500/40',
      bg: 'bg-slate-900/90 shadow-rose-500/10',
      icon: <AlertOctagon className="w-5 h-5 text-rose-400 shrink-0" />,
      progress: 'bg-rose-500',
    },
    info: {
      border: 'border-cyan-500/40',
      bg: 'bg-slate-900/90 shadow-cyan-500/10',
      icon: <Info className="w-5 h-5 text-cyan-400 shrink-0" />,
      progress: 'bg-cyan-500',
    },
  };

  const style = typeStyles[toast.type];

  return (
    <div
      className={`relative overflow-hidden rounded-xl border backdrop-blur-md p-4 shadow-xl transition-all duration-300 transform translate-y-0 opacity-100 flex items-start gap-3 w-80 sm:w-96 text-slate-100 ${style.border} ${style.bg}`}
      role="alert"
    >
      {style.icon}
      <div className="flex-1 min-w-0 pr-2">
        <h4 className="text-sm font-semibold text-slate-100">{toast.title}</h4>
        {toast.message && (
          <p className="text-xs text-slate-300 mt-0.5 break-words">{toast.message}</p>
        )}
      </div>
      <button
        onClick={() => onDismiss(toast.id)}
        className="text-slate-400 hover:text-slate-200 p-1 rounded-lg hover:bg-slate-800/60 transition-colors"
        aria-label="Dismiss toast"
      >
        <X className="w-4 h-4" />
      </button>

      {/* Optional animation progress indicator */}
      {toast.duration && (
        <div
          className={`absolute bottom-0 left-0 h-0.5 ${style.progress} opacity-60 animate-[progress_linear]`}
          style={{
            animationDuration: `${toast.duration}ms`,
            width: '100%',
          }}
        />
      )}
    </div>
  );
};
