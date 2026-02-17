import { cn } from '../../lib/cn';
import type { CampaignStatus } from '../../types/campaign';

interface StatusBadgeProps {
  status: CampaignStatus;
  className?: string;
}

const statusConfig: Record<CampaignStatus, { label: string; className: string }> = {
  DRAFT: { label: 'Draft', className: 'bg-gray-500/20 text-gray-400 border-gray-500/30' },
  ANALYZED: { label: 'Analyzed', className: 'bg-blue-500/20 text-blue-400 border-blue-500/30' },
  GENERATING_IMAGES: { label: 'Generating', className: 'bg-yellow-500/20 text-yellow-400 border-yellow-500/30' },
  READY: { label: 'Ready', className: 'bg-brand-lime/20 text-brand-lime border-brand-lime/30' },
  PUBLISHED: { label: 'Published', className: 'bg-green-500/20 text-green-400 border-green-500/30' },
  PAUSED: { label: 'Paused', className: 'bg-orange-500/20 text-orange-400 border-orange-500/30' },
  ACTIVE: { label: 'Active', className: 'bg-green-500/20 text-green-400 border-green-500/30' },
  ARCHIVED: { label: 'Archived', className: 'bg-gray-500/20 text-gray-500 border-gray-500/20' },
};

export function StatusBadge({ status, className }: StatusBadgeProps) {
  const config = statusConfig[status] || statusConfig.DRAFT;

  return (
    <span
      className={cn(
        'inline-flex items-center px-2 py-0.5 text-xs font-mono uppercase tracking-wider border',
        config.className,
        className
      )}
    >
      {config.label}
    </span>
  );
}
