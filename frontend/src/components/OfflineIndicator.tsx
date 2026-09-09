import React, { useState, useEffect } from 'react';
import { Wifi, WifiOff, RefreshCw, CheckCircle2, AlertCircle } from 'lucide-react';
import { OfflineSyncService } from '../services/offlineSync';

export const OfflineIndicator: React.FC = () => {
  const [isOnline, setIsOnline] = useState<boolean>(navigator.onLine);
  const [queuedCount, setQueuedCount] = useState<number>(0);
  const [isSyncing, setIsSyncing] = useState<boolean>(false);
  const [syncMessage, setSyncMessage] = useState<string | null>(null);

  const checkQueue = async () => {
    const count = await OfflineSyncService.getQueuedCount();
    setQueuedCount(count);
  };

  useEffect(() => {
    checkQueue();

    const handleOnline = () => {
      setIsOnline(true);
      triggerSync();
    };

    const handleOffline = () => {
      setIsOnline(false);
      checkQueue();
    };

    window.addEventListener('online', handleOnline);
    window.addEventListener('offline', handleOffline);

    // Periodic check for local queue
    const interval = setInterval(checkQueue, 6000);

    return () => {
      window.removeEventListener('online', handleOnline);
      window.removeEventListener('offline', handleOffline);
      clearInterval(interval);
    };
  }, []);

  const triggerSync = async () => {
    if (!navigator.onLine || isSyncing) return;
    setIsSyncing(true);
    setSyncMessage('Syncing offline reports with server...');

    try {
      const res = await OfflineSyncService.syncPendingReports();
      if (res.syncedCount > 0) {
        setSyncMessage(`Successfully synced ${res.syncedCount} offline reports (+${res.totalPoints} pts)!`);
        setTimeout(() => setSyncMessage(null), 4000);
      } else {
        setSyncMessage(null);
      }
      checkQueue();
    } catch (err) {
      setSyncMessage('Sync attempt failed. Will retry automatically when connected.');
      setTimeout(() => setSyncMessage(null), 4000);
    } finally {
      setIsSyncing(false);
    }
  };

  // If online and nothing is queued, render subtle connectivity badge or return null
  if (isOnline && queuedCount === 0 && !syncMessage) {
    return null;
  }

  return (
    <div className="fixed top-20 right-6 z-40 flex flex-col items-end gap-2 animate-in slide-in-from-top-2 duration-300">
      {syncMessage && (
        <div className="px-3.5 py-2 bg-emerald-700 text-white rounded-xl shadow-lg text-xs font-semibold flex items-center gap-2">
          <CheckCircle2 className="w-4 h-4 text-emerald-300" />
          <span>{syncMessage}</span>
        </div>
      )}

      <div
        className={`px-4 py-2.5 rounded-2xl shadow-xl border flex items-center gap-3 backdrop-blur-md transition-all ${
          !isOnline
            ? 'bg-amber-900/90 text-amber-100 border-amber-600/50'
            : 'bg-slate-900/90 text-slate-100 border-slate-700'
        }`}
      >
        <div className="flex items-center gap-2">
          {!isOnline ? (
            <WifiOff className="w-4 h-4 text-amber-400 animate-pulse" />
          ) : (
            <Wifi className="w-4 h-4 text-emerald-400" />
          )}

          <div>
            <div className="text-xs font-bold leading-tight">
              {!isOnline ? 'Offline Mode Active' : 'Online Connected'}
            </div>
            <div className="text-[10px] text-amber-200/80">
              {queuedCount > 0
                ? `${queuedCount} report${queuedCount > 1 ? 's' : ''} queued in IndexedDB`
                : 'Local cache ready'}
            </div>
          </div>
        </div>

        {isOnline && queuedCount > 0 && (
          <button
            onClick={triggerSync}
            disabled={isSyncing}
            className="ml-2 px-3 py-1 bg-emerald-600 hover:bg-emerald-500 text-white rounded-lg text-xs font-bold transition-all flex items-center gap-1.5 shadow-sm"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${isSyncing ? 'animate-spin' : ''}`} />
            {isSyncing ? 'Syncing...' : 'Sync Now'}
          </button>
        )}
      </div>
    </div>
  );
};
