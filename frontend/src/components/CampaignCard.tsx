import { ExternalLink, Trash2, Eye, Calendar, DollarSign } from 'lucide-react';
import { Card } from './ui/Card';
import { StatusBadge } from './ui/StatusBadge';
import { Button } from './ui/Button';
import type { Campaign } from '../types/campaign';
import type { CampaignStatus } from '../types/campaign';

interface CampaignCardProps {
  campaign: Campaign;
  onView: (id: string) => void;
  onDelete: (id: string) => void;
}

function formatDate(dateStr: string): string {
  const date = new Date(dateStr);
  return date.toLocaleDateString('en-US', {
    month: 'short',
    day: 'numeric',
    year: 'numeric',
  });
}

export function CampaignCard({ campaign, onView, onDelete }: CampaignCardProps) {
  return (
    <Card className="group hover:border-white/20 transition-all">
      <div className="p-5">
        {/* Header: name + status */}
        <div className="flex items-start justify-between gap-3 mb-3">
          <h3 className="font-display font-bold text-white truncate text-lg leading-tight">
            {campaign.name}
          </h3>
          <StatusBadge status={campaign.status as CampaignStatus} className="shrink-0" />
        </div>

        {/* URL */}
        {campaign.project_url && (
          <p className="text-xs font-mono text-gray-500 truncate mb-4">
            {campaign.project_url}
          </p>
        )}

        {/* Meta info row */}
        <div className="flex items-center gap-4 text-xs text-gray-400 font-mono mb-4">
          <span className="flex items-center gap-1.5">
            <Calendar className="w-3.5 h-3.5" />
            {formatDate(campaign.created_at)}
          </span>
          <span className="flex items-center gap-1.5">
            <DollarSign className="w-3.5 h-3.5" />
            ${campaign.budget_daily}/day
          </span>
        </div>

        {/* Published meta IDs */}
        {campaign.meta_campaign_id && (
          <div className="mb-4 p-2 bg-green-500/5 border border-green-500/10">
            <p className="text-xs font-mono text-green-400/70">
              Meta Campaign: {campaign.meta_campaign_id}
            </p>
          </div>
        )}

        {/* Actions */}
        <div className="flex items-center gap-2 pt-3 border-t border-white/5">
          <Button
            variant="secondary"
            size="sm"
            onClick={() => onView(campaign.id)}
            className="flex-1"
          >
            <Eye className="w-3.5 h-3.5 mr-1.5" />
            View
          </Button>
          {campaign.meta_campaign_id && (
            <a
              href={`https://www.facebook.com/adsmanager/manage/campaigns?act=${campaign.meta_campaign_id}`}
              target="_blank"
              rel="noopener noreferrer"
              className="inline-flex items-center justify-center h-9 px-3 text-sm font-mono font-medium uppercase tracking-wide bg-brand-gray text-white hover:bg-brand-lime hover:text-brand-dark transition-colors"
            >
              <ExternalLink className="w-3.5 h-3.5" />
            </a>
          )}
          <button
            onClick={() => onDelete(campaign.id)}
            className="inline-flex items-center justify-center h-9 px-3 text-gray-500 hover:text-red-400 hover:bg-red-400/10 transition-colors"
            aria-label="Delete campaign"
          >
            <Trash2 className="w-3.5 h-3.5" />
          </button>
        </div>
      </div>
    </Card>
  );
}
