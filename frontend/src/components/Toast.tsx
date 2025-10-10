import { useEffect } from 'react';

type ToastProps = {
  message: string;
  variant?: 'success' | 'error';
  onClose: () => void;
  timeout?: number;
};

export function Toast({ message, variant = 'success', onClose, timeout = 4000 }: ToastProps) {
  useEffect(() => {
    const timer = setTimeout(onClose, timeout);
    return () => clearTimeout(timer);
  }, [onClose, timeout]);

  return (
    <div className={`toast fade-in ${variant === 'error' ? 'error' : ''}`} role="status" aria-live="polite">
      <span>{message}</span>
    </div>
  );
}
