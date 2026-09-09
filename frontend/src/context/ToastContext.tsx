import React, { createContext, useContext, useState, useCallback, useEffect } from 'react';
import { Award, Sparkles, CheckCircle2, AlertCircle, Info, X } from 'lucide-react';

export interface ToastMessage {
  id: string;
  title: string;
  description?: string;
  type?: 'points' | 'badge' | 'success' | 'info' | 'error';
  points?: number;
  badge?: string;
  duration?: number;
}

interface ToastContextType {
  toasts: ToastMessage[];
  showToast: (toast: Omit<ToastMessage, 'id'>) => void;
  showPointsToast: (points: number, reason: string, badge?: string) => void;
  dismissToast: (id: string) => void;
}

const ToastContext = createContext<ToastContextType | undefined>(undefined);

export const ToastProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [toasts, setToasts] = useState<ToastMessage[]>([]);

  const dismissToast = useCallback((id: string) => {
    setToasts((prev) => prev.filter((t) => t.id !== id));
  }, []);

  const showToast = useCallback(
    (toast: Omit<ToastMessage, 'id'>) => {
      const id = `${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;
      const duration = toast.duration ?? (toast.type === 'points' ? 4500 : 3500);

      const newToast: ToastMessage = { ...toast, id };
      setToasts((prev) => [...prev, newToast]);

      if (duration > 0) {
        setTimeout(() => {
          dismissToast(id);
        }, duration);
      }
    },
    [dismissToast]
  );

  const showPointsToast = useCallback(
    (points: number, reason: string, badge?: string) => {
      showToast({
        title: `+${points} Points Earned!`,
        description: reason,
        type: 'points',
        points,
        badge,
      });
    },
    [showToast]
  );

  // Listen for global custom events for cross-component triggers
  useEffect(() => {
    const handleCustomPointsEvent = (event: CustomEvent) => {
      const { points, reason, badge } = event.detail || {};
      if (points) {
        showPointsToast(points, reason || 'Field activity completed', badge);
      }
    };

    window.addEventListener('crophealth-points-awarded' as any, handleCustomPointsEvent as any);
    return () => {
      window.removeEventListener('crophealth-points-awarded' as any, handleCustomPointsEvent as any);
    };
  }, [showPointsToast]);

  return (
    <ToastContext.Provider value={{ toasts, showToast, showPointsToast, dismissToast }}>
      {children}
      {/* Toast Render Container */}
      <div className="fixed top-20 right-4 z-50 flex flex-col gap-3 max-w-sm w-full pointer-events-none px-2 sm:px-0">
        {toasts.map((toast) => (
          <div
            key={toast.id}
            className={`pointer-events-auto flex items-start gap-3 p-4 rounded-2xl shadow-xl border backdrop-blur-md transition-all transform animate-in slide-in-from-top-4 duration-300 ${
              toast.type === 'points'
                ? 'bg-gradient-to-r from-amber-500/95 via-amber-600/95 to-emerald-600/95 text-white border-amber-300/40 ring-2 ring-amber-400/30'
                : toast.type === 'badge'
                ? 'bg-gradient-to-r from-purple-600/95 to-indigo-600/95 text-white border-purple-300/40 ring-2 ring-purple-400/30'
                : toast.type === 'success'
                ? 'bg-emerald-800/95 text-white border-emerald-500/40'
                : toast.type === 'error'
                ? 'bg-rose-800/95 text-white border-rose-500/40'
                : 'bg-slate-800/95 text-white border-slate-600/40'
            }`}
          >
            {/* Icon */}
            <div className="flex-shrink-0 mt-0.5">
              {toast.type === 'points' && (
                <div className="w-10 h-10 rounded-xl bg-amber-400/30 border border-amber-200/50 flex items-center justify-center animate-bounce">
                  <Sparkles className="w-5 h-5 text-yellow-200" />
                </div>
              )}
              {toast.type === 'badge' && (
                <div className="w-10 h-10 rounded-xl bg-purple-400/30 border border-purple-200/50 flex items-center justify-center">
                  <Award className="w-5 h-5 text-purple-200" />
                </div>
              )}
              {toast.type === 'success' && <CheckCircle2 className="w-5 h-5 text-emerald-300" />}
              {toast.type === 'error' && <AlertCircle className="w-5 h-5 text-rose-300" />}
              {toast.type === 'info' && <Info className="w-5 h-5 text-blue-300" />}
            </div>

            {/* Content */}
            <div className="flex-1 min-w-0">
              <div className="flex items-center gap-2">
                <h4 className="font-extrabold text-sm tracking-tight text-white">{toast.title}</h4>
                {toast.points && (
                  <span className="px-2 py-0.5 bg-yellow-300 text-amber-950 font-black text-xs rounded-full shadow-sm">
                    +{toast.points} PTS
                  </span>
                )}
              </div>
              {toast.description && (
                <p className="text-xs text-white/90 mt-1 line-clamp-2 leading-relaxed font-medium">
                  {toast.description}
                </p>
              )}
              {toast.badge && (
                <span className="inline-block mt-1.5 px-2 py-0.5 bg-white/20 text-white text-[11px] font-semibold rounded-md backdrop-blur-sm">
                  {toast.badge}
                </span>
              )}
            </div>

            {/* Close */}
            <button
              onClick={() => dismissToast(toast.id)}
              className="flex-shrink-0 p-1 rounded-lg text-white/70 hover:text-white hover:bg-white/10 transition-colors"
            >
              <X className="w-4 h-4" />
            </button>
          </div>
        ))}
      </div>
    </ToastContext.Provider>
  );
};

export const useToast = () => {
  const context = useContext(ToastContext);
  if (!context) {
    throw new Error('useToast must be used within a ToastProvider');
  }
  return context;
};

// Global helper to trigger point toasts from non-component utilities
export const emitPointsAwarded = (points: number, reason: string, badge?: string) => {
  const event = new CustomEvent('crophealth-points-awarded', {
    detail: { points, reason, badge },
  });
  window.dispatchEvent(event);
};
