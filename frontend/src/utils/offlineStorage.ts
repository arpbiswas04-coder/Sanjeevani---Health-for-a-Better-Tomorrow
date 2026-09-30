// IndexedDB and Local Storage offline synchronization manager for Sanjeevani Grid

export interface QueuedSyncAction {
  id: string;
  endpoint: string;
  method: 'POST' | 'PUT' | 'PATCH' | 'DELETE';
  payload: Record<string, unknown>;
  timestamp: string;
}

const DB_NAME = 'SanjeevaniGridDB';
const DB_VERSION = 1;
const QUEUE_STORE = 'syncQueue';
const CACHE_STORE = 'offlineCache';
const SYNC_QUEUE_KEY = 'sanjeevani_offline_sync_queue';

// Open IndexedDB with graceful fallback
function openDB(): Promise<IDBDatabase> {
  return new Promise((resolve, reject) => {
    if (typeof window === 'undefined' || !window.indexedDB) {
      reject(new Error('IndexedDB not supported in this environment'));
      return;
    }

    const request = window.indexedDB.open(DB_NAME, DB_VERSION);

    request.onupgradeneeded = (event) => {
      const db = (event.target as IDBOpenDBRequest).result;
      if (!db.objectStoreNames.contains(QUEUE_STORE)) {
        db.createObjectStore(QUEUE_STORE, { keyPath: 'id' });
      }
      if (!db.objectStoreNames.contains(CACHE_STORE)) {
        db.createObjectStore(CACHE_STORE, { keyPath: 'key' });
      }
    };

    request.onsuccess = () => resolve(request.result);
    request.onerror = () => reject(request.error);
  });
}

export const offlineStorage = {
  // Get all pending sync requests
  async getQueueAsync(): Promise<QueuedSyncAction[]> {
    try {
      const db = await openDB();
      return new Promise((resolve) => {
        const tx = db.transaction(QUEUE_STORE, 'readonly');
        const store = tx.objectStore(QUEUE_STORE);
        const req = store.getAll();
        req.onsuccess = () => resolve(req.result || []);
        req.onerror = () => resolve(this.getQueue());
      });
    } catch {
      return this.getQueue();
    }
  },

  // Synchronous get from localStorage
  getQueue(): QueuedSyncAction[] {
    try {
      const data = localStorage.getItem(SYNC_QUEUE_KEY);
      return data ? JSON.parse(data) : [];
    } catch {
      return [];
    }
  },

  // Enqueue action when network is down
  async enqueueAsync(action: Omit<QueuedSyncAction, 'id' | 'timestamp'>): Promise<QueuedSyncAction> {
    const newAction: QueuedSyncAction = {
      ...action,
      id: 'act_' + Math.random().toString(36).substring(2, 9),
      timestamp: new Date().toISOString(),
    };

    // Save to localStorage
    const queue = this.getQueue();
    queue.push(newAction);
    localStorage.setItem(SYNC_QUEUE_KEY, JSON.stringify(queue));

    // Also persist to IndexedDB
    try {
      const db = await openDB();
      const tx = db.transaction(QUEUE_STORE, 'readwrite');
      tx.objectStore(QUEUE_STORE).put(newAction);
    } catch (e) {
      console.warn('IndexedDB write fallback to localStorage', e);
    }

    window.dispatchEvent(new CustomEvent('sanjeevani_queue_updated', { detail: queue.length }));
    return newAction;
  },

  enqueue(action: Omit<QueuedSyncAction, 'id' | 'timestamp'>): QueuedSyncAction {
    const queue = this.getQueue();
    const newAction: QueuedSyncAction = {
      ...action,
      id: 'act_' + Math.random().toString(36).substring(2, 9),
      timestamp: new Date().toISOString(),
    };
    queue.push(newAction);
    localStorage.setItem(SYNC_QUEUE_KEY, JSON.stringify(queue));

    if (typeof window !== 'undefined' && window.indexedDB) {
      openDB().then((db) => {
        const tx = db.transaction(QUEUE_STORE, 'readwrite');
        tx.objectStore(QUEUE_STORE).put(newAction);
      }).catch(() => {});
    }

    window.dispatchEvent(new CustomEvent('sanjeevani_queue_updated', { detail: queue.length }));
    return newAction;
  },

  // Clear queue after sync
  async clearQueueAsync(): Promise<void> {
    localStorage.removeItem(SYNC_QUEUE_KEY);
    try {
      const db = await openDB();
      const tx = db.transaction(QUEUE_STORE, 'readwrite');
      tx.objectStore(QUEUE_STORE).clear();
    } catch (e) {
      console.warn('IndexedDB clear error', e);
    }
    window.dispatchEvent(new CustomEvent('sanjeevani_queue_updated', { detail: 0 }));
  },

  clearQueue(): void {
    localStorage.removeItem(SYNC_QUEUE_KEY);
    if (typeof window !== 'undefined' && window.indexedDB) {
      this.clearQueueAsync().catch(() => {});
    }
    window.dispatchEvent(new CustomEvent('sanjeevani_queue_updated', { detail: 0 }));
  },

  // Cache facility and inventory data for offline field usage
  async cacheOfflineDataAsync<T>(key: string, data: T): Promise<void> {
    localStorage.setItem(`sanjeevani_cache_${key}`, JSON.stringify(data));
    try {
      const db = await openDB();
      const tx = db.transaction(CACHE_STORE, 'readwrite');
      tx.objectStore(CACHE_STORE).put({ key, value: data, updated: Date.now() });
    } catch (e) {
      console.warn('IndexedDB cache put fallback', e);
    }
  },

  cacheOfflineData<T>(key: string, data: T): void {
    localStorage.setItem(`sanjeevani_cache_${key}`, JSON.stringify(data));
    this.cacheOfflineDataAsync(key, data).catch(() => {});
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
