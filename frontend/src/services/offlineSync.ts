import { api } from './api';

export interface OfflineReport {
  id?: number;
  offline_id: string;
  crop_type: string;
  notes?: string;
  location?: string;
  latitude?: number;
  longitude?: number;
  image_blob: Blob;
  image_name: string;
  captured_at: string;
  sync_status: 'pending' | 'syncing' | 'failed' | 'synced';
  error_message?: string;
}

const DB_NAME = 'CropHealthOfflineDB';
const DB_VERSION = 1;
const STORE_NAME = 'offline_reports';

/**
 * Open or initialize IndexedDB instance
 */
function openDB(): Promise<IDBDatabase> {
  return new Promise((resolve, reject) => {
    const request = indexedDB.open(DB_NAME, DB_VERSION);

    request.onupgradeneeded = (event: IDBVersionChangeEvent) => {
      const db = (event.target as IDBOpenDBRequest).result;
      if (!db.objectStoreNames.contains(STORE_NAME)) {
        const store = db.createObjectStore(STORE_NAME, {
          keyPath: 'id',
          autoIncrement: true,
        });
        store.createIndex('offline_id', 'offline_id', { unique: true });
        store.createIndex('sync_status', 'sync_status', { unique: false });
      }
    };

    request.onsuccess = () => resolve(request.result);
    request.onerror = () => reject(request.error);
  });
}

/**
 * Convert Blob to Base64 data string
 */
function blobToBase64(blob: Blob): Promise<string> {
  return new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.onloadend = () => {
      const base64data = reader.result as string;
      resolve(base64data);
    };
    reader.onerror = reject;
    reader.readAsDataURL(blob);
  });
}

export const OfflineSyncService = {
  /**
   * Save a report locally into IndexedDB when offline
   */
  saveReportLocally: async (data: {
    crop_type: string;
    notes?: string;
    location?: string;
    latitude?: number;
    longitude?: number;
    image_file: File | Blob;
    image_name?: string;
  }): Promise<OfflineReport> => {
    const db = await openDB();
    const offlineItem: OfflineReport = {
      offline_id: `offline-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`,
      crop_type: data.crop_type,
      notes: data.notes,
      location: data.location,
      latitude: data.latitude,
      longitude: data.longitude,
      image_blob: data.image_file,
      image_name: (data.image_file as File).name || data.image_name || 'leaf_sample.jpg',
      captured_at: new Date().toISOString(),
      sync_status: 'pending',
    };

    return new Promise((resolve, reject) => {
      const tx = db.transaction(STORE_NAME, 'readwrite');
      const store = tx.objectStore(STORE_NAME);
      const req = store.add(offlineItem);

      req.onsuccess = (e) => {
        offlineItem.id = (e.target as IDBRequest).result;
        resolve(offlineItem);
      };
      req.onerror = () => reject(req.error);
    });
  },

  /**
   * Get all queued pending reports from IndexedDB
   */
  getPendingReports: async (): Promise<OfflineReport[]> => {
    const db = await openDB();
    return new Promise((resolve, reject) => {
      const tx = db.transaction(STORE_NAME, 'readonly');
      const store = tx.objectStore(STORE_NAME);
      const req = store.getAll();

      req.onsuccess = () => {
        const all = req.result as OfflineReport[];
        resolve(all.filter((r) => r.sync_status === 'pending' || r.sync_status === 'failed'));
      };
      req.onerror = () => reject(req.error);
    });
  },

  /**
   * Get count of queued offline reports
   */
  getQueuedCount: async (): Promise<number> => {
    try {
      const items = await OfflineSyncService.getPendingReports();
      return items.length;
    } catch {
      return 0;
    }
  },

  /**
   * Sync all pending items to backend /api/v1/sync/batch
   */
  syncPendingReports: async (): Promise<{
    syncedCount: number;
    totalPoints: number;
  }> => {
    const pending = await OfflineSyncService.getPendingReports();
    if (pending.length === 0) {
      return { syncedCount: 0, totalPoints: 0 };
    }

    // Convert blobs to base64 for JSON batch transmission
    const batchPayload = await Promise.all(
      pending.map(async (item) => {
        let b64 = '';
        if (item.image_blob) {
          try {
            b64 = await blobToBase64(item.image_blob);
          } catch (e) {
            console.warn('Could not convert blob to base64:', e);
          }
        }

        return {
          offline_id: item.offline_id,
          crop_type: item.crop_type,
          symptoms: item.notes,
          notes: item.notes,
          location: item.location,
          location_lat: item.latitude,
          location_lng: item.longitude,
          image_base64: b64,
          captured_at: item.captured_at,
        };
      })
    );

    const response = await api.post('/sync/batch', {
      client_id: 'web-pwa-client',
      device_id: 'pwa-browser-field',
      reports: batchPayload,
    });

    const data = response.data?.data;
    const syncedReports = data?.synced_reports || [];

    // Update or remove synced items in IndexedDB
    const db = await openDB();
    const tx = db.transaction(STORE_NAME, 'readwrite');
    const store = tx.objectStore(STORE_NAME);

    for (const item of pending) {
      const wasSynced = syncedReports.some((s: any) => s.offline_id === item.offline_id);
      if (wasSynced && item.id) {
        store.delete(item.id);
      }
    }

    return {
      syncedCount: data?.synced_count || 0,
      totalPoints: data?.points_awarded_total || 0,
    };
  },

  /**
   * Register online listener to auto-trigger synchronization on reconnect
   */
  registerAutoSync: (onSyncComplete?: (result: any) => void) => {
    window.addEventListener('online', async () => {
      console.log('[OfflineSync] Online connection restored. Attempting background sync...');
      try {
        const res = await OfflineSyncService.syncPendingReports();
        if (res.syncedCount > 0 && onSyncComplete) {
          onSyncComplete(res);
        }
      } catch (err) {
        console.warn('[OfflineSync] Auto-sync attempt error:', err);
      }
    });
  },
};
