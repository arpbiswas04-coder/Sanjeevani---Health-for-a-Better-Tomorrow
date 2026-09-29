// IndexedDB and Local Storage offline synchronization manager for Sanjeevani Grid

export interface QueuedSyncAction {
  id: string;
  endpoint: string;
  method: 'POST' | 'PUT' | 'PATCH' | 'DELETE';
  payload: Record<string, unknown>;
  timestamp: string;
}

const SYNC_QUEUE_KEY = 'sanjeevani_offline_sync_queue';

export const offlineStorage = {
  // Get all pending sync requests
  getQueue(): QueuedSyncAction[] {
    try {
      const data = localStorage.getItem(SYNC_QUEUE_KEY);
      return data ? JSON.parse(data) : [];
    } catch {
      return [];
    }
  },

  // Enqueue action when network is down
  enqueue(action: Omit<QueuedSyncAction, 'id' | 'timestamp'>): QueuedSyncAction {
    const queue = this.getQueue();
    const newAction: QueuedSyncAction = {
      ...action,
      id: Math.random().toString(36).substring(2, 9),
      timestamp: new Date().toISOString(),
    };
    queue.push(newAction);
    localStorage.setItem(SYNC_QUEUE_KEY, JSON.stringify(queue));
    return newAction;
  },

  // Clear queue after sync
  clearQueue(): void {
    localStorage.removeItem(SYNC_QUEUE_KEY);
  },

  // Cache facility and inventory data for offline field usage
  cacheOfflineData<T>(key: string, data: T): void {
    localStorage.setItem(`sanjeevani_cache_${key}`, JSON.stringify(data));
  },

  getCachedData<T>(key: string): T | null {
    try {
      const item = localStorage.getItem(`sanjeevani_cache_${key}`);
      return item ? JSON.parse(item) : null;
    } catch {
      return null;
    }
  },
};
