import { AlertCircle, AlertTriangle, Info, X } from 'lucide-react';
import { cn } from '../../lib/cn';

interface ErrorBannerProps {
  message: string;
  variant?: 'error' | 'warning' | 'info';
  onDismiss?: () => void;
  className?: string;
}

const icons = {
  error: AlertCircle,
  warning: AlertTriangle,
  info: Info,
};

const styles = {
  error: 'text-status-error bg-status-error/10 border-status-error/20',
  warning: 'text-status-warning bg-status-warning/10 border-status-warning/20',
  info: 'text-status-info bg-status-info/10 border-status-info/20',
};

export function ErrorBanner({ message, variant = 'error', onDismiss, className }: ErrorBannerProps) {
  const Icon = icons[variant];

  return (
    <div className={cn('flex items-center gap-3 px-4 py-3 border text-sm font-mono animate-fade-in', styles[variant], className)}>
      <Icon className="w-4 h-4 shrink-0" />
      <span className="flex-1">{message}</span>
      {onDismiss && (
        <button onClick={onDismiss} className="shrink-0 hover:opacity-70 transition-opacity">
          <X className="w-4 h-4" />
        </button>
      )}
    </div>
  );
}
