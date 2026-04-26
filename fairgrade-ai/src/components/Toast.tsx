import React, { createContext, useContext, useState, useCallback, useEffect, useRef } from 'react';
import { CheckCircle, XCircle, AlertTriangle, Info, X } from 'lucide-react';

// ─── Types ───────────────────────────────────────────────────────────────────

type ToastType = 'success' | 'error' | 'warning' | 'info';

interface Toast {
  id: string;
  type: ToastType;
  message: string;
  duration?: number;
}

interface ToastContextValue {
  showToast: (message: string, type?: ToastType, duration?: number) => void;
}

// ─── Context ─────────────────────────────────────────────────────────────────

const ToastContext = createContext<ToastContextValue | null>(null);

// eslint-disable-next-line react-refresh/only-export-components
export function useToast(): ToastContextValue {
  const ctx = useContext(ToastContext);
  if (!ctx) throw new Error('useToast must be used inside <ToastProvider>');
  return ctx;
}

// ─── Individual Toast ─────────────────────────────────────────────────────────

const ICONS: Record<ToastType, React.ReactNode> = {
  success: <CheckCircle size={16} />,
  error: <XCircle size={16} />,
  warning: <AlertTriangle size={16} />,
  info: <Info size={16} />,
};

const COLORS: Record<ToastType, string> = {
  success: '#059669',
  error: '#ef4444',
  warning: '#f59e0b',
  info: '#7c3aed',
};

const BG_COLORS: Record<ToastType, string> = {
  success: 'rgba(5, 150, 105, 0.12)',
  error: 'rgba(239, 68, 68, 0.12)',
  warning: 'rgba(245, 158, 11, 0.12)',
  info: 'rgba(124, 58, 237, 0.12)',
};

function ToastItem({ toast, onDismiss }: { toast: Toast; onDismiss: (id: string) => void }) {
  const [visible, setVisible] = useState(false);

  useEffect(() => {
    // Trigger enter animation
    const t = setTimeout(() => setVisible(true), 10);
    return () => clearTimeout(t);
  }, []);

  const dismiss = useCallback(() => {
    setVisible(false);
    setTimeout(() => onDismiss(toast.id), 300);
  }, [toast.id, onDismiss]);

  useEffect(() => {
    const timer = setTimeout(dismiss, toast.duration ?? 4000);
    return () => clearTimeout(timer);
  }, [dismiss, toast.duration]);

  const color = COLORS[toast.type];

  return (
    <div
      role="alert"
      aria-live="assertive"
      style={{
        display: 'flex',
        alignItems: 'flex-start',
        gap: '0.6rem',
        padding: '0.75rem 1rem',
        background: 'var(--card-bg, #1e1e2e)',
        border: `1px solid ${color}44`,
        borderLeft: `3px solid ${color}`,
        borderRadius: '10px',
        boxShadow: '0 4px 24px rgba(0,0,0,0.18)',
        maxWidth: '360px',
        minWidth: '240px',
        transform: visible ? 'translateX(0)' : 'translateX(120%)',
        opacity: visible ? 1 : 0,
        transition: 'transform 0.3s cubic-bezier(0.4,0,0.2,1), opacity 0.3s ease',
        cursor: 'default',
      }}
    >
      <span style={{ color, flexShrink: 0, marginTop: '1px' }}>{ICONS[toast.type]}</span>
      <span style={{ fontSize: '0.875rem', color: 'var(--text-main, #e2e8f0)', flex: 1, lineHeight: 1.4 }}>
        {toast.message}
      </span>
      <button
        onClick={dismiss}
        aria-label="Dismiss notification"
        style={{
          background: 'none',
          border: 'none',
          padding: 0,
          cursor: 'pointer',
          color: 'var(--text-muted, #94a3b8)',
          flexShrink: 0,
          display: 'flex',
          marginTop: '1px',
        }}
      >
        <X size={14} />
      </button>
    </div>
  );
}

// ─── Provider ─────────────────────────────────────────────────────────────────

export function ToastProvider({ children }: { children: React.ReactNode }) {
  const [toasts, setToasts] = useState<Toast[]>([]);
  const counterRef = useRef(0);

  const showToast = useCallback((message: string, type: ToastType = 'info', duration?: number) => {
    const id = `toast-${++counterRef.current}`;
    setToasts(prev => [...prev, { id, type, message, duration }]);
  }, []);

  const dismiss = useCallback((id: string) => {
    setToasts(prev => prev.filter(t => t.id !== id));
  }, []);

  return (
    <ToastContext.Provider value={{ showToast }}>
      {children}
      {/* Toast stack — bottom-right */}
      <div
        aria-label="Notifications"
        style={{
          position: 'fixed',
          bottom: '1.5rem',
          right: '1.5rem',
          zIndex: 9999,
          display: 'flex',
          flexDirection: 'column',
          gap: '0.6rem',
          pointerEvents: 'none',
        }}
      >
        {toasts.map(t => (
          <div key={t.id} style={{ pointerEvents: 'auto' }}>
            <ToastItem toast={t} onDismiss={dismiss} />
          </div>
        ))}
      </div>
    </ToastContext.Provider>
  );
}
