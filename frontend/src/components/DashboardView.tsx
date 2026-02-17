import { useEffect, useState } from 'react';
import { Plus, LayoutDashboard, Filter, Loader2 } from 'lucide-react';
import { motion } from 'framer-motion';
import { Navbar } from './layout/Navbar';
import { Button } from './ui/Button';
import { CampaignCard } from './CampaignCard';
import { ConfirmDialog } from './ui/ConfirmDialog';
import { ErrorBanner } from './ui/ErrorBanner';
import type { Campaign } from '../types/campaign';

interface DashboardViewProps {
  campaigns: Campaign[];
  isLoading: boolean;
  error: string | null;
  userName: string | null;
  onFetchCampaigns: (status?: string) => Promise<void>;
  onViewCampaign: (id: string) => void;
  onDeleteCampaign: (id: string) => Promise<void>;
  onNewCampaign: () => void;
  onLogoClick: () => void;
  onDashboardClick: () => void;
  onLogout: () => Promise<void>;
  onDismissError: () => void;
}

const STATUS_FILTERS: { value: string; label: string }[] = [
  { value: '', label: 'All' },
  { value: 'ANALYZED', label: 'Analyzed' },
  { value: 'DRAFT', label: 'Draft' },
  { value: 'READY', label: 'Ready' },
  { value: 'PUBLISHED', label: 'Published' },
  { value: 'ACTIVE', label: 'Active' },
  { value: 'PAUSED', label: 'Paused' },
];

export function DashboardView({
  campaigns,
  isLoading,
  error,
  userName,
  onFetchCampaigns,
  onViewCampaign,
  onDeleteCampaign,
  onNewCampaign,
  onLogoClick,
  onDashboardClick,
  onLogout,
  onDismissError,
}: DashboardViewProps) {
  const [statusFilter, setStatusFilter] = useState('');
  const [deleteTarget, setDeleteTarget] = useState<string | null>(null);
  const [isDeleting, setIsDeleting] = useState(false);

  useEffect(() => {
    onFetchCampaigns(statusFilter || undefined);
  }, [statusFilter, onFetchCampaigns]);

  const handleDelete = async () => {
    if (!deleteTarget) return;
    setIsDeleting(true);
    await onDeleteCampaign(deleteTarget);
    setIsDeleting(false);
    setDeleteTarget(null);
  };

  return (
    <div className="min-h-screen bg-brand-dark text-white">
      <Navbar
        onLogoClick={onLogoClick}
        userName={userName}
        onDashboardClick={onDashboardClick}
        onLogout={onLogout}
      />

      <div className="max-w-7xl mx-auto px-6 pt-24 pb-16">
        {/* Header */}
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 mb-8">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 bg-brand-gray border border-white/10 flex items-center justify-center text-brand-lime">
              <LayoutDashboard className="w-5 h-5" />
            </div>
            <div>
              <h1 className="text-2xl font-display font-bold">My Campaigns</h1>
              <p className="text-sm text-gray-500 font-mono">
                {campaigns.length} campaign{campaigns.length !== 1 ? 's' : ''}
              </p>
            </div>
          </div>
          <Button variant="primary" size="sm" onClick={onNewCampaign}>
            <Plus className="w-4 h-4 mr-1.5" />
            New Campaign
          </Button>
        </div>

        {/* Filters */}
        <div className="flex items-center gap-2 mb-6 overflow-x-auto pb-2">
          <Filter className="w-4 h-4 text-gray-500 shrink-0" />
          {STATUS_FILTERS.map((filter) => (
            <button
              key={filter.value}
              onClick={() => setStatusFilter(filter.value)}
              className={`px-3 py-1.5 text-xs font-mono uppercase tracking-wider border transition-colors whitespace-nowrap ${
                statusFilter === filter.value
                  ? 'border-brand-lime text-brand-lime bg-brand-lime/10'
                  : 'border-white/10 text-gray-400 hover:border-white/20 hover:text-white'
              }`}
            >
              {filter.label}
            </button>
          ))}
        </div>

        {/* Error */}
        {error && (
          <ErrorBanner message={error} onDismiss={onDismissError} className="mb-6" />
        )}

        {/* Loading */}
        {isLoading && campaigns.length === 0 && (
          <div className="flex items-center justify-center py-20">
            <Loader2 className="w-8 h-8 text-brand-lime animate-spin" />
          </div>
        )}

        {/* Empty state */}
        {!isLoading && campaigns.length === 0 && (
          <motion.div
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            className="text-center py-20 border border-dashed border-white/10"
          >
            <div className="w-16 h-16 bg-brand-gray border border-white/10 flex items-center justify-center mx-auto mb-4 text-gray-500">
              <LayoutDashboard className="w-8 h-8" />
            </div>
            <h3 className="text-lg font-display font-bold text-white mb-2">No campaigns yet</h3>
            <p className="text-sm text-gray-400 mb-6 max-w-sm mx-auto">
              {statusFilter
                ? 'No campaigns match this filter. Try a different status or clear the filter.'
                : 'Create your first ad campaign to get started.'}
            </p>
            {!statusFilter && (
              <Button variant="primary" size="sm" onClick={onNewCampaign}>
                <Plus className="w-4 h-4 mr-1.5" />
                Create Campaign
              </Button>
            )}
          </motion.div>
        )}

        {/* Campaign grid */}
        {campaigns.length > 0 && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            className="grid sm:grid-cols-2 lg:grid-cols-3 gap-4"
          >
            {campaigns.map((campaign, i) => (
              <motion.div
                key={campaign.id}
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: i * 0.05 }}
              >
                <CampaignCard
                  campaign={campaign}
                  onView={onViewCampaign}
                  onDelete={(id) => setDeleteTarget(id)}
                />
              </motion.div>
            ))}
          </motion.div>
        )}
      </div>

      {/* Delete confirmation */}
      <ConfirmDialog
        open={!!deleteTarget}
        title="Delete campaign?"
        message="This campaign will be permanently removed. This action cannot be undone."
        confirmLabel={isDeleting ? 'Deleting...' : 'Delete'}
        cancelLabel="Cancel"
        onConfirm={handleDelete}
        onCancel={() => setDeleteTarget(null)}
      />
    </div>
  );
}
