import React, { useState, useEffect } from 'react';
import { WifiOff, Wifi, RefreshCw } from 'lucide-react';
import { offlineStorage } from '@/utils/offlineStorage';

export const OfflineIndicator: React.FC = () => {
  const [isOnline, setIsOnline] = useState<boolean>(
    typeof navigator !== 'undefined' ? navigator.onLine : true
  );
  const [queueCount, setQueueCount] = useState<number>(() => offlineStorage.getQueue().length);

  useEffect(() => {
    const handleOnline = () => setIsOnline(true);
    const handleOffline = () => setIsOnline(false);
    const handleQueueUpdate = (e: any) => {
      setQueueCount(typeof e.detail === 'number' ? e.detail : offlineStorage.getQueue().length);
    };

    window.addEventListener('online', handleOnline);
    window.addEventListener('offline', handleOffline);
    window.addEventListener('sanjeevani_queue_updated', handleQueueUpdate);

    const interval = setInterval(() => {
      setQueueCount(offlineStorage.getQueue().length);
    }, 2500);

    return () => {
      window.removeEventListener('online', handleOnline);
      window.removeEventListener('offline', handleOffline);
      window.removeEventListener('sanjeevani_queue_updated', handleQueueUpdate);
      clearInterval(interval);
    };
  }, []);

  if (isOnline && queueCount === 0) return null;

  return (
    <div
      className={`fixed top-16 left-0 right-0 z-50 px-4 py-2 text-xs font-semibold flex items-center justify-between shadow-lg transition-colors ${
        !isOnline
          ? 'bg-amber-500 text-slate-950 border-b border-amber-600'
          : 'bg-emerald-600 text-white border-b border-emerald-700'
      }`}
    >
      <div className="flex items-center gap-2 max-w-7xl mx-auto w-full justify-between">
        <div className="flex items-center gap-2">
          {!isOnline ? <WifiOff className="w-4 h-4 animate-bounce" /> : <Wifi className="w-4 h-4" />}
          <span>
            {!isOnline
              ? 'Offline - backend requests are unavailable. Automatic synchronization is not connected.'
              : 'Browser network restored - backend connectivity has not been verified.'}
          </span>
        </div>

        {queueCount > 0 && (
          <div className="flex items-center gap-2">
            <span className="font-mono bg-black/20 px-2 py-0.5 rounded">
              {queueCount} actions pending upload
            </span>
            {isOnline && (
              <button
                disabled
                title="Synchronization is not implemented; queued records are preserved."
                className="px-2 py-0.5 bg-white text-slate-900 rounded font-bold hover:bg-slate-100 flex items-center gap-1 text-[11px] transition-colors"
              >
                <RefreshCw className="w-3 h-3" />
                Sync unavailable
              </button>
            )}
          </div>
        )}
      </div>
    </div>
  );
};

export default OfflineIndicator;
