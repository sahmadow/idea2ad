import { useState, useCallback } from 'react';
import {
  ArrowLeft,
  ArrowRight,
  Download,
  Target,
  DollarSign,
  Clock,
  Sparkles,
  Grid3X3,
  X,
  Check,
  Pencil,
  ChevronDown,
  Eye,
  ImageIcon,
  Loader2,
} from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';
import { toast } from 'sonner';
import { Button } from './ui/Button';
import { Card } from './ui/Card';
import { MetaAdPreview } from './ui/MetaAdPreview';
import { TemplateEditor } from './TemplateEditor';
import { updateAdPack, renderPackImages } from '../api/adpack';
import type { AdPack, AdCreative, AdStrategy } from '../types/adpack';
import type { Ad } from '../api';

interface AdPackViewProps {
  adPack: AdPack;
  onAdPackChange: (pack: AdPack) => void;
  onBack: () => void;
  onPublish?: (ad: Ad) => void;
}

type FilterStrategy = 'all' | AdStrategy;

const staggerContainer = {
  hidden: {},
  visible: { transition: { staggerChildren: 0.08 } },
};

const fadeInUp = {
  hidden: { opacity: 0, y: 16 },
  visible: { opacity: 1, y: 0, transition: { duration: 0.25 } },
};

function StrategyBadge({ strategy }: { strategy: AdStrategy }) {
  return (
    <span
      className={
        strategy === 'product_aware'
          ? 'px-2 py-0.5 text-[10px] font-mono uppercase tracking-wider bg-emerald-500/20 text-emerald-400 border border-emerald-500/30'
          : 'px-2 py-0.5 text-[10px] font-mono uppercase tracking-wider bg-violet-500/20 text-violet-400 border border-violet-500/30'
      }
    >
      {strategy === 'product_aware' ? 'Product Aware' : 'Product Unaware'}
    </span>
  );
}

function CreativeCard({
  creative,
  pageName,
  websiteUrl,
  onExpand,
  onEditTemplate,
}: {
  creative: AdCreative;
  pageName: string;
  websiteUrl: string;
  onExpand: () => void;
  onEditTemplate?: () => void;
}) {
  // Convert AdCreative to Ad shape for MetaAdPreview
  const ad: Ad = {
    id: parseInt(creative.id, 16) || 1,
    imageUrl: creative.image_url,
    primaryText: creative.primary_text,
    headline: creative.headline,
    description: creative.description,
  };

  return (
    <div className="relative group">
      <div className="flex items-center gap-1.5">
        <StrategyBadge strategy={creative.strategy} />
        <span className="px-2 py-0.5 text-[10px] font-mono uppercase tracking-wider bg-gray-500/20 text-gray-400 border border-gray-500/30">
          {creative.aspect_ratio}
        </span>
      </div>
      <div className="mt-2">
        <MetaAdPreview
          ad={ad}
          pageName={pageName}
          websiteUrl={websiteUrl}
          onSelect={onExpand}
        />
      </div>
      <div className="absolute bottom-16 right-3 z-10 flex gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
        {onEditTemplate && creative.format === 'static' && (
          <button
            onClick={onEditTemplate}
            className="bg-white/10 hover:bg-white/20 backdrop-blur-sm text-white p-2"
            aria-label="Edit template"
          >
            <Pencil className="w-4 h-4" />
          </button>
        )}
        <button
          onClick={onExpand}
          className="bg-white/10 hover:bg-white/20 backdrop-blur-sm text-white p-2"
          aria-label="Expand creative"
        >
          <Eye className="w-4 h-4" />
        </button>
      </div>
    </div>
  );
}

function InlineEditField({
  label,
  value,
  onSave,
  multiline = false,
}: {
  label: string;
  value: string;
  onSave: (newValue: string) => void;
  multiline?: boolean;
}) {
  const [editing, setEditing] = useState(false);
  const [draft, setDraft] = useState(value);

  const handleSave = () => {
    if (draft.trim() !== value) {
      onSave(draft.trim());
    }
    setEditing(false);
  };

  const handleCancel = () => {
    setDraft(value);
    setEditing(false);
  };

  if (!editing) {
    return (
      <div className="group">
        <div className="text-xs text-gray-500 uppercase tracking-wide mb-1">{label}</div>
        <div
          className="flex items-start gap-2 cursor-pointer hover:bg-white/5 p-2 -m-2 transition-colors"
          onClick={() => setEditing(true)}
          role="button"
          tabIndex={0}
          onKeyDown={(e) => { if (e.key === 'Enter') setEditing(true); }}
        >
          <p className="text-sm text-gray-300 flex-1 whitespace-pre-line">{value}</p>
          <Pencil className="w-3 h-3 text-gray-600 group-hover:text-gray-400 shrink-0 mt-0.5" />
        </div>
      </div>
    );
  }

  return (
    <div>
      <div className="text-xs text-gray-500 uppercase tracking-wide mb-1">{label}</div>
      {multiline ? (
        <textarea
          value={draft}
          onChange={(e) => setDraft(e.target.value)}
          className="w-full bg-brand-gray border border-white/20 text-white text-sm p-2 focus:border-brand-lime focus:outline-none resize-y min-h-[80px]"
          rows={4}
          autoFocus
        />
      ) : (
        <input
          type="text"
          value={draft}
          onChange={(e) => setDraft(e.target.value)}
          className="w-full bg-brand-gray border border-white/20 text-white text-sm p-2 focus:border-brand-lime focus:outline-none"
          autoFocus
        />
      )}
      <div className="flex gap-2 mt-2">
        <button
          onClick={handleSave}
          className="inline-flex items-center gap-1 px-3 py-1 bg-brand-lime text-brand-dark text-xs font-mono uppercase"
        >
          <Check className="w-3 h-3" /> Save
        </button>
        <button
          onClick={handleCancel}
          className="inline-flex items-center gap-1 px-3 py-1 bg-white/10 text-gray-300 text-xs font-mono uppercase hover:bg-white/20"
        >
          <X className="w-3 h-3" /> Cancel
        </button>
      </div>
    </div>
  );
}

function ExpandedCreativeView({
  creative,
  onClose,
  onSave,
  onPublish,
  pageName,
  websiteUrl,
}: {
  creative: AdCreative;
  onClose: () => void;
  onSave: (field: string, value: string) => void;
  onPublish?: () => void;
  pageName: string;
  websiteUrl: string;
}) {
  const ad: Ad = {
    id: parseInt(creative.id, 16) || 1,
    imageUrl: creative.image_url,
    primaryText: creative.primary_text,
    headline: creative.headline,
    description: creative.description,
  };

  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 0 }}
      className="fixed inset-0 z-50 bg-black/80 backdrop-blur-sm flex items-center justify-center p-4 overflow-y-auto"
      onClick={onClose}
    >
      <motion.div
        initial={{ scale: 0.95, opacity: 0 }}
        animate={{ scale: 1, opacity: 1 }}
        exit={{ scale: 0.95, opacity: 0 }}
        className="bg-brand-dark border border-white/10 max-w-4xl w-full my-8 overflow-hidden"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Header */}
        <div className="flex items-center justify-between p-4 border-b border-white/10">
          <div className="flex items-center gap-3">
            <h3 className="text-lg font-display font-bold text-white">Creative Details</h3>
            <StrategyBadge strategy={creative.strategy} />
          </div>
          <button onClick={onClose} className="text-gray-400 hover:text-white p-1">
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Content */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-0">
          {/* Preview */}
          <div className="p-6 flex items-start justify-center bg-brand-gray/30">
            <div className="max-w-sm w-full">
              <MetaAdPreview
                ad={ad}
                pageName={pageName}
                websiteUrl={websiteUrl}
              />
            </div>
          </div>

          {/* Editable fields */}
          <div className="p-6 space-y-6">
            <InlineEditField
              label="Primary Text"
              value={creative.primary_text}
              onSave={(val) => onSave('primary_text', val)}
              multiline
            />
            <InlineEditField
              label="Headline"
              value={creative.headline}
              onSave={(val) => onSave('headline', val)}
            />
            <InlineEditField
              label="Description"
              value={creative.description}
              onSave={(val) => onSave('description', val)}
            />

            {creative.image_brief && (
              <div>
                <div className="text-xs text-gray-500 uppercase tracking-wide mb-1">Creative Type</div>
                <p className="text-sm text-gray-400 capitalize">
                  {creative.image_brief.creative_type || creative.image_brief.approach}
                </p>
              </div>
            )}

            {onPublish && (
              <div className="pt-4 border-t border-white/10">
                <Button variant="primary" onClick={onPublish} className="w-full">
                  Select for Publishing
                  <ArrowRight className="w-4 h-4 ml-2" />
                </Button>
              </div>
            )}
          </div>
        </div>
      </motion.div>
    </motion.div>
  );
}

function TargetingSummary({ adPack }: { adPack: AdPack }) {
  const [expanded, setExpanded] = useState(false);
  const { targeting } = adPack;

  return (
    <Card>
      <button
        onClick={() => setExpanded(!expanded)}
        className="w-full text-left p-6"
      >
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 bg-brand-gray border border-white/10 flex items-center justify-center text-brand-lime">
              <Target className="w-5 h-5" />
            </div>
            <div>
              <h3 className="text-lg font-bold font-display text-white">Smart Broad Targeting</h3>
              <p className="text-xs text-gray-500 font-mono uppercase">
                {targeting.rationale.methodology}
              </p>
            </div>
          </div>
          <ChevronDown
            className={`w-5 h-5 text-gray-400 transition-transform ${expanded ? 'rotate-180' : ''}`}
          />
        </div>

        {/* Summary row */}
        <div className="flex flex-wrap gap-4 mt-4 text-sm">
          <div>
            <span className="text-gray-500">Age:</span>{' '}
            <span className="text-white">{targeting.age_min} - {targeting.age_max}</span>
          </div>
          <div>
            <span className="text-gray-500">Geo:</span>{' '}
            <span className="text-white">{targeting.geo_locations.join(', ')}</span>
          </div>
          <div>
            <span className="text-gray-500">Gender:</span>{' '}
            <span className="text-white capitalize">{targeting.genders.join(', ')}</span>
          </div>
        </div>
      </button>

      {/* Expanded rationale */}
      <AnimatePresence>
        {expanded && (
          <motion.div
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: 'auto', opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            className="overflow-hidden"
          >
            <div className="px-6 pb-6 space-y-3 border-t border-white/5 pt-4">
              <div className="p-3 bg-brand-gray/50 border border-white/5">
                <div className="text-xs text-gray-500 uppercase mb-1">Age Range Rationale</div>
                <p className="text-sm text-gray-300">{targeting.rationale.age_range_reason}</p>
              </div>
              <div className="p-3 bg-brand-gray/50 border border-white/5">
                <div className="text-xs text-gray-500 uppercase mb-1">Geographic Rationale</div>
                <p className="text-sm text-gray-300">{targeting.rationale.geo_reason}</p>
              </div>
              {targeting.rationale.exclusion_reason && (
                <div className="p-3 bg-brand-gray/50 border border-white/5">
                  <div className="text-xs text-gray-500 uppercase mb-1">Exclusion Strategy</div>
                  <p className="text-sm text-gray-300">{targeting.rationale.exclusion_reason}</p>
                </div>
              )}
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </Card>
  );
}

function BudgetControls({
  adPack,
  onUpdate,
}: {
  adPack: AdPack;
  onUpdate: (field: 'budget_daily' | 'duration_days', value: number) => void;
}) {
  const totalBudget = adPack.budget_daily * adPack.duration_days;

  return (
    <Card>
      <div className="p-6">
        <div className="flex items-center gap-3 mb-6">
          <div className="w-10 h-10 bg-brand-gray border border-white/10 flex items-center justify-center text-brand-lime">
            <DollarSign className="w-5 h-5" />
          </div>
          <h3 className="text-lg font-bold font-display text-white">Budget & Duration</h3>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-3 gap-6">
          {/* Daily Budget */}
          <div>
            <label className="text-xs text-gray-500 uppercase tracking-wide block mb-2">
              Daily Budget
            </label>
            <div className="relative">
              <span className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400 text-sm">$</span>
              <input
                type="number"
                value={adPack.budget_daily}
                onChange={(e) => {
                  const val = parseFloat(e.target.value);
                  if (!isNaN(val) && val >= 1) onUpdate('budget_daily', val);
                }}
                min={1}
                step={1}
                className="w-full bg-brand-gray border border-white/20 text-white text-sm p-2 pl-7 focus:border-brand-lime focus:outline-none"
              />
            </div>
          </div>

          {/* Duration */}
          <div>
            <label className="text-xs text-gray-500 uppercase tracking-wide block mb-2">
              Duration (Days)
            </label>
            <div className="relative">
              <Clock className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400 w-4 h-4" />
              <input
                type="number"
                value={adPack.duration_days}
                onChange={(e) => {
                  const val = parseInt(e.target.value);
                  if (!isNaN(val) && val >= 1) onUpdate('duration_days', val);
                }}
                min={1}
                step={1}
                className="w-full bg-brand-gray border border-white/20 text-white text-sm p-2 pl-9 focus:border-brand-lime focus:outline-none"
              />
            </div>
          </div>

          {/* Total */}
          <div>
            <label className="text-xs text-gray-500 uppercase tracking-wide block mb-2">
              Total Budget
            </label>
            <div className="bg-brand-gray border border-brand-lime/30 p-2 text-center">
              <span className="text-brand-lime text-lg font-bold font-mono">
                ${totalBudget.toFixed(2)}
              </span>
            </div>
          </div>
        </div>

        {/* Campaign structure info */}
        <div className="mt-4 pt-4 border-t border-white/5 flex flex-wrap gap-4 text-xs text-gray-500">
          <span>1 Campaign</span>
          <span>1 Ad Set</span>
          <span>{adPack.creatives.length} Ads</span>
          <span className="text-gray-600">|</span>
          <span>{adPack.campaign_structure.campaign_name}</span>
        </div>
      </div>
    </Card>
  );
}

export function AdPackView({ adPack, onAdPackChange, onBack, onPublish }: AdPackViewProps) {
  const [filterStrategy, setFilterStrategy] = useState<FilterStrategy>('all');
  const [expandedCreative, setExpandedCreative] = useState<AdCreative | null>(null);
  const [editingCreative, setEditingCreative] = useState<AdCreative | null>(null);
  const [rendering, setRendering] = useState(false);

  let pageName = 'Your Page';
  try {
    pageName = new URL(adPack.project_url).hostname.replace('www.', '');
  } catch {
    // fallback for empty urls
  }

  const filteredCreatives =
    filterStrategy === 'all'
      ? adPack.creatives
      : adPack.creatives.filter((c) => c.strategy === filterStrategy);

  const productAwareCount = adPack.creatives.filter((c) => c.strategy === 'product_aware').length;
  const productUnawareCount = adPack.creatives.filter((c) => c.strategy === 'product_unaware').length;

  const handleCreativeSave = useCallback(
    async (creativeId: string, field: string, value: string) => {
      try {
        const updated = await updateAdPack(adPack.id, {
          creative_id: creativeId,
          [field]: value,
        });
        onAdPackChange(updated);
        toast.success('Creative updated');
      } catch (err) {
        toast.error(err instanceof Error ? err.message : 'Failed to update');
      }
    },
    [adPack.id, onAdPackChange]
  );

  const handleBudgetUpdate = useCallback(
    async (field: 'budget_daily' | 'duration_days', value: number) => {
      try {
        const updated = await updateAdPack(adPack.id, { [field]: value });
        onAdPackChange(updated);
      } catch (err) {
        toast.error(err instanceof Error ? err.message : 'Failed to update budget');
      }
    },
    [adPack.id, onAdPackChange]
  );

  const handleExportJson = () => {
    const dataStr = JSON.stringify(adPack, null, 2);
    const dataBlob = new Blob([dataStr], { type: 'application/json' });
    const url = URL.createObjectURL(dataBlob);
    const link = document.createElement('a');
    link.href = url;
    link.download = `adpack-${adPack.id}-${new Date().toISOString().split('T')[0]}.json`;
    link.click();
    URL.revokeObjectURL(url);
  };

  const handleRenderImages = useCallback(async () => {
    setRendering(true);
    try {
      const renders = await renderPackImages(adPack.id);
      const urlMap = new Map(renders.map((r) => [r.ad_type_id, r.image_url]));
      const updatedCreatives = adPack.creatives.map((c) => {
        const imageUrl = urlMap.get(c.ad_type_id);
        if (imageUrl) {
          return { ...c, image_url: imageUrl };
        }
        return c;
      });
      onAdPackChange({ ...adPack, creatives: updatedCreatives });
      toast.success(`Rendered ${renders.length} images`);
    } catch (err) {
      toast.error(err instanceof Error ? err.message : 'Render failed');
    } finally {
      setRendering(false);
    }
  }, [adPack, onAdPackChange]);

  const handlePublishCreative = (creative: AdCreative) => {
    if (!onPublish) return;
    const ad: Ad = {
      id: parseInt(creative.id, 16) || 1,
      imageUrl: creative.image_url,
      primaryText: creative.primary_text,
      headline: creative.headline,
      description: creative.description,
    };
    onPublish(ad);
  };

  return (
    <div className="min-h-screen bg-brand-dark text-white py-12">
      <div className="max-w-7xl mx-auto px-6">
        {/* Header */}
        <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 mb-12">
          <button
            onClick={onBack}
            className="flex items-center gap-2 text-gray-400 hover:text-white transition-colors"
          >
            <ArrowLeft className="w-5 h-5" />
            <span className="font-mono text-sm">Back</span>
          </button>
          <div className="flex items-center gap-3">
            <Button variant="outline" size="sm" onClick={handleRenderImages} disabled={rendering}>
              {rendering ? <Loader2 className="w-4 h-4 mr-2 animate-spin" /> : <ImageIcon className="w-4 h-4 mr-2" />}
              {rendering ? 'Rendering...' : 'Render Images'}
            </Button>
            <Button variant="outline" size="sm" onClick={handleExportJson}>
              <Download className="w-4 h-4 mr-2" />
              Export
            </Button>
          </div>
        </div>

        {/* Title */}
        <div className="text-center mb-12">
          <div className="inline-flex items-center gap-2 px-3 py-1 bg-brand-gray border border-white/10 text-xs font-mono text-brand-lime uppercase tracking-wider mb-4">
            <Grid3X3 className="w-3 h-3" />
            Ad Pack
          </div>
          <h1 className="text-3xl sm:text-4xl font-display font-bold mb-2">
            {adPack.campaign_structure.campaign_name}
          </h1>
          <p className="text-gray-400">
            {adPack.creatives.length} creatives &middot; ${adPack.budget_daily}/day &middot;{' '}
            {adPack.duration_days} day{adPack.duration_days !== 1 ? 's' : ''}
          </p>
        </div>

        {/* Targeting + Budget Row */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-12">
          <TargetingSummary adPack={adPack} />
          <BudgetControls adPack={adPack} onUpdate={handleBudgetUpdate} />
        </div>

        {/* Creative Grid */}
        <div className="mb-12">
          <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 mb-8">
            <div>
              <h2 className="text-2xl font-display font-bold">Creatives</h2>
              <p className="text-gray-400 text-sm mt-1">Click any creative to expand and edit</p>
            </div>

            {/* Strategy filter */}
            <div className="flex items-center gap-2">
              <button
                onClick={() => setFilterStrategy('all')}
                className={`px-3 py-1.5 text-xs font-mono uppercase transition-colors ${
                  filterStrategy === 'all'
                    ? 'bg-brand-lime text-brand-dark'
                    : 'bg-brand-gray text-gray-400 hover:text-white border border-white/10'
                }`}
              >
                All ({adPack.creatives.length})
              </button>
              <button
                onClick={() => setFilterStrategy('product_aware')}
                className={`px-3 py-1.5 text-xs font-mono uppercase transition-colors ${
                  filterStrategy === 'product_aware'
                    ? 'bg-emerald-500/20 text-emerald-400 border border-emerald-500/30'
                    : 'bg-brand-gray text-gray-400 hover:text-white border border-white/10'
                }`}
              >
                Aware ({productAwareCount})
              </button>
              <button
                onClick={() => setFilterStrategy('product_unaware')}
                className={`px-3 py-1.5 text-xs font-mono uppercase transition-colors ${
                  filterStrategy === 'product_unaware'
                    ? 'bg-violet-500/20 text-violet-400 border border-violet-500/30'
                    : 'bg-brand-gray text-gray-400 hover:text-white border border-white/10'
                }`}
              >
                Unaware ({productUnawareCount})
              </button>
            </div>
          </div>

          <motion.div
            className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-8 justify-items-center"
            variants={staggerContainer}
            initial="hidden"
            animate="visible"
            key={filterStrategy}
          >
            {filteredCreatives.map((creative) => (
              <motion.div key={creative.id} variants={fadeInUp}>
                <CreativeCard
                  creative={creative}
                  pageName={pageName}
                  websiteUrl={adPack.project_url}
                  onExpand={() => setExpandedCreative(creative)}
                  onEditTemplate={() => setEditingCreative(creative)}
                />
              </motion.div>
            ))}
          </motion.div>

          {filteredCreatives.length === 0 && (
            <div className="text-center py-16 text-gray-500">
              <Sparkles className="w-8 h-8 mx-auto mb-3 opacity-50" />
              <p className="font-mono text-sm">No creatives match this filter</p>
            </div>
          )}
        </div>

        {/* Bottom stats */}
        <div className="mt-8 pt-8 border-t border-white/10 text-center text-sm text-gray-500">
          <span className="font-mono">
            {adPack.creatives.length} creatives &middot; {productAwareCount} product aware &middot;{' '}
            {productUnawareCount} product unaware &middot; Total budget: $
            {(adPack.budget_daily * adPack.duration_days).toFixed(2)}
          </span>
        </div>
      </div>

      {/* Template Editor Modal */}
      {editingCreative && (
        <TemplateEditor
          adTypeId={editingCreative.ad_type_id}
          initialAspectRatio={editingCreative.aspect_ratio || '1:1'}
          onSave={() => {
            setEditingCreative(null);
            toast.success('Template saved — re-render to update creative');
          }}
          onClose={() => setEditingCreative(null)}
        />
      )}

      {/* Expanded Creative Modal */}
      <AnimatePresence>
        {expandedCreative && (
          <ExpandedCreativeView
            creative={expandedCreative}
            pageName={pageName}
            websiteUrl={adPack.project_url}
            onClose={() => setExpandedCreative(null)}
            onSave={(field, value) => {
              handleCreativeSave(expandedCreative.id, field, value);
              // Update local expanded creative
              setExpandedCreative((prev) =>
                prev ? { ...prev, [field]: value } : null
              );
            }}
            onPublish={
              onPublish
                ? () => {
                    handlePublishCreative(expandedCreative);
                    setExpandedCreative(null);
                  }
                : undefined
            }
          />
        )}
      </AnimatePresence>
    </div>
  );
}
