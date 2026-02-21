import { useState, useEffect, useRef } from 'react';
import { useNavigate, Navigate } from 'react-router-dom';
import { motion } from 'framer-motion';
import { ArrowLeft, Loader2, Package, Users, AlertTriangle, Swords, Pencil, Trash2 } from 'lucide-react';
import { Button } from '../components/ui/Button';
import { Terminal } from '../components/ui/Terminal';
import { ErrorBanner } from '../components/ui/ErrorBanner';
import { useAppContext } from '../context/AppContext';

const LOADING_STAGES = [
  'Generating Copy',
  'Creating Images',
  'Rendering Videos',
  'Building Ad Pack',
];

export default function ReviewPage() {
  const ctx = useAppContext();
  const navigate = useNavigate();
  const wasGenerating = useRef(false);

  const pc = ctx.preparedCampaign;

  // Editable state initialized from prepared campaign
  const [productSummary, setProductSummary] = useState('');
  const [targetAudience, setTargetAudience] = useState('');
  const [mainPainPoint, setMainPainPoint] = useState('');
  const [messagingUnaware, setMessagingUnaware] = useState('');
  const [messagingAware, setMessagingAware] = useState('');
  const [competitors, setCompetitors] = useState<{ name: string; weakness: string }[]>([]);
  const [editingCompetitor, setEditingCompetitor] = useState<number | null>(null);

  // Initialize from prepared campaign
  useEffect(() => {
    if (!pc) return;
    setProductSummary(pc.product_summary || '');
    setTargetAudience(pc.target_audience || '');
    setMainPainPoint(pc.main_pain_point || '');
    setMessagingUnaware(pc.messaging_unaware || '');
    setMessagingAware(pc.messaging_aware || '');
    setCompetitors(pc.competitors?.map(c => ({ ...c })) || []);
  }, [pc]);

  // Track generation and navigate when done
  useEffect(() => {
    if (ctx.isGenerating) wasGenerating.current = true;
  }, [ctx.isGenerating]);

  useEffect(() => {
    if (wasGenerating.current && !ctx.isGenerating && ctx.adPack && !ctx.error) {
      wasGenerating.current = false;
      navigate('/adpack');
    }
  }, [ctx.isGenerating, ctx.adPack, ctx.error, navigate]);

  // Guard: must have prepared campaign
  if (!pc) return <Navigate to="/" replace />;

  const handleConfirm = async () => {
    await ctx.startGeneration({
      product_summary: productSummary,
      target_audience: targetAudience,
      main_pain_point: mainPainPoint,
      messaging_unaware: messagingUnaware,
      messaging_aware: messagingAware,
      competitors: competitors.length > 0 ? competitors : undefined,
    });
  };

  const handleDeleteCompetitor = (index: number) => {
    setCompetitors(prev => prev.filter((_, i) => i !== index));
    if (editingCompetitor === index) setEditingCompetitor(null);
  };

  const handleCompetitorChange = (index: number, field: 'name' | 'weakness', value: string) => {
    setCompetitors(prev => prev.map((c, i) => i === index ? { ...c, [field]: value } : c));
  };

  // Show loading screen when generating
  if (ctx.isGenerating) {
    return (
      <div className="min-h-screen bg-brand-dark text-white flex flex-col items-center justify-center px-6">
        <div className="text-center space-y-8 max-w-md w-full">
          <div className="w-16 h-16 border-2 border-brand-lime/30 border-t-brand-lime rounded-full animate-spin mx-auto" />
          <div>
            <h2 className="text-2xl font-display font-bold mb-2">Generating Your Ads</h2>
            <p className="text-gray-400 font-mono text-sm">{pc.product_name}</p>
          </div>

          <div className="flex justify-center gap-3">
            {LOADING_STAGES.map((stage, i) => (
              <div key={stage} className="flex items-center gap-2">
                <div className={`w-2 h-2 ${i <= ctx.loadingStage ? 'bg-brand-lime' : 'bg-white/20'} transition-colors`} />
                <span className={`text-xs font-mono ${i <= ctx.loadingStage ? 'text-white' : 'text-gray-600'} hidden sm:inline transition-colors`}>
                  {stage}
                </span>
              </div>
            ))}
          </div>

          <Terminal />

          <Button variant="ghost" size="sm" onClick={ctx.cancelGeneration}>
            Cancel
          </Button>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-brand-dark text-white">
      {/* Header */}
      <div className="border-b border-white/5 px-6 py-4">
        <div className="max-w-2xl mx-auto flex items-center justify-between">
          <button
            onClick={() => navigate('/upload')}
            className="flex items-center gap-2 text-sm text-gray-400 hover:text-white transition-colors font-mono"
          >
            <ArrowLeft className="w-4 h-4" />
            Back
          </button>
          <div className="text-xs font-mono text-gray-500">Step 3 of 3</div>
        </div>
      </div>

      <div className="max-w-2xl mx-auto px-6 py-12 space-y-8">
        <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }}>

          {/* Brand Logo + Product Name */}
          <div className="text-center space-y-4 mb-10">
            {pc.brand_logo_url ? (
              <div className="flex justify-center">
                <img
                  src={pc.brand_logo_url}
                  alt="Brand logo"
                  className="max-h-16 max-w-[240px] w-auto h-auto object-contain"
                />
              </div>
            ) : (
              <div className="w-16 h-16 mx-auto bg-brand-gray border border-white/10 flex items-center justify-center">
                <Package className="w-8 h-8 text-gray-500" />
              </div>
            )}
            <h2 className="text-2xl font-display font-bold">{pc.product_name}</h2>
            <div className="inline-flex items-center gap-2 px-3 py-1 bg-brand-gray border border-white/10 text-xs font-mono text-gray-400">
              {pc.business_type} &middot; {pc.language.toUpperCase()}
            </div>
          </div>

          {/* Product Summary */}
          <section className="space-y-3">
            <label className="text-sm font-mono text-gray-300 flex items-center gap-2">
              <Package className="w-4 h-4 text-brand-lime" />
              Product Summary
            </label>
            <textarea
              value={productSummary}
              onChange={(e) => setProductSummary(e.target.value)}
              rows={3}
              className="w-full bg-brand-gray border border-white/10 px-4 py-3 text-white text-sm font-mono focus:outline-none focus:border-brand-lime transition-colors resize-none"
            />
          </section>

          {/* Target Audience */}
          <section className="space-y-3 pt-6 border-t border-white/10">
            <label className="text-sm font-mono text-gray-300 flex items-center gap-2">
              <Users className="w-4 h-4 text-brand-lime" />
              Target Audience
            </label>
            <textarea
              value={targetAudience}
              onChange={(e) => setTargetAudience(e.target.value)}
              rows={2}
              placeholder="Who is this product for?"
              className="w-full bg-brand-gray border border-white/10 px-4 py-3 text-white text-sm font-mono focus:outline-none focus:border-brand-lime transition-colors resize-none"
            />
          </section>

          {/* Main Pain Point */}
          <section className="space-y-3 pt-6 border-t border-white/10">
            <label className="text-sm font-mono text-gray-300 flex items-center gap-2">
              <AlertTriangle className="w-4 h-4 text-brand-lime" />
              Main Pain Point
            </label>
            <textarea
              value={mainPainPoint}
              onChange={(e) => setMainPainPoint(e.target.value)}
              rows={2}
              placeholder="What problem does it solve or opportunity does it create?"
              className="w-full bg-brand-gray border border-white/10 px-4 py-3 text-white text-sm font-mono focus:outline-none focus:border-brand-lime transition-colors resize-none"
            />
          </section>

          {/* Messaging */}
          <section className="space-y-4 pt-6 border-t border-white/10">
            <h3 className="text-sm font-mono text-gray-300">Messaging Strategy</h3>

            <div className="space-y-3">
              <label className="text-sm font-mono text-white flex items-center gap-2">
                <span className="px-2 py-0.5 text-[10px] font-mono uppercase tracking-wider bg-violet-500/20 text-violet-400 border border-violet-500/30">
                  Unaware
                </span>
                Problem-Unaware Users
              </label>
              <textarea
                value={messagingUnaware}
                onChange={(e) => setMessagingUnaware(e.target.value)}
                rows={2}
                placeholder="How to reach users who don't know they have this problem"
                className="w-full bg-brand-gray border border-white/10 px-4 py-3 text-white text-sm font-mono focus:outline-none focus:border-violet-400 transition-colors resize-none"
              />
            </div>

            <div className="space-y-3">
              <label className="text-sm font-mono text-white flex items-center gap-2">
                <span className="px-2 py-0.5 text-[10px] font-mono uppercase tracking-wider bg-emerald-500/20 text-emerald-400 border border-emerald-500/30">
                  Aware
                </span>
                Problem-Aware Users
              </label>
              <textarea
                value={messagingAware}
                onChange={(e) => setMessagingAware(e.target.value)}
                rows={2}
                placeholder="How to reach users actively comparing solutions"
                className="w-full bg-brand-gray border border-white/10 px-4 py-3 text-white text-sm font-mono focus:outline-none focus:border-emerald-400 transition-colors resize-none"
              />
            </div>
          </section>

          {/* Competitive Landscape */}
          <section className="space-y-4 pt-6 border-t border-white/10">
            <div className="flex items-center justify-between">
              <h3 className="text-sm font-mono text-gray-300 flex items-center gap-2">
                <Swords className="w-4 h-4 text-brand-lime" />
                Competitive Landscape
              </h3>
              <span className="text-xs font-mono text-gray-600">{competitors.length}/3 detected</span>
            </div>

            {competitors.length === 0 ? (
              <p className="text-xs font-mono text-gray-600 py-4 text-center">
                No competitors auto-detected. This won't affect ad generation.
              </p>
            ) : (
              <div className="space-y-3">
                {competitors.map((comp, i) => (
                  <div key={i} className="bg-brand-gray border border-white/10 p-4">
                    {editingCompetitor === i ? (
                      <div className="space-y-3">
                        <input
                          type="text"
                          value={comp.name}
                          onChange={(e) => handleCompetitorChange(i, 'name', e.target.value)}
                          className="w-full h-9 bg-brand-dark border border-white/10 px-3 text-white text-sm font-mono focus:outline-none focus:border-brand-lime transition-colors"
                          placeholder="Competitor name"
                        />
                        <textarea
                          value={comp.weakness}
                          onChange={(e) => handleCompetitorChange(i, 'weakness', e.target.value)}
                          rows={2}
                          className="w-full bg-brand-dark border border-white/10 px-3 py-2 text-white text-sm font-mono focus:outline-none focus:border-brand-lime transition-colors resize-none"
                          placeholder="Their weakness"
                        />
                        <button
                          onClick={() => setEditingCompetitor(null)}
                          className="text-xs font-mono text-brand-lime hover:underline"
                        >
                          Done
                        </button>
                      </div>
                    ) : (
                      <div className="flex items-start justify-between gap-3">
                        <div className="flex-1 min-w-0">
                          <p className="text-sm font-mono text-white font-medium">{comp.name}</p>
                          <p className="text-xs font-mono text-gray-400 mt-1">{comp.weakness}</p>
                        </div>
                        <div className="flex items-center gap-1 shrink-0">
                          <button
                            onClick={() => setEditingCompetitor(i)}
                            className="p-1.5 hover:bg-white/10 transition-colors"
                            title="Edit"
                          >
                            <Pencil className="w-3.5 h-3.5 text-gray-400" />
                          </button>
                          <button
                            onClick={() => handleDeleteCompetitor(i)}
                            className="p-1.5 hover:bg-red-500/20 transition-colors"
                            title="Remove"
                          >
                            <Trash2 className="w-3.5 h-3.5 text-gray-400 hover:text-red-400" />
                          </button>
                        </div>
                      </div>
                    )}
                  </div>
                ))}
              </div>
            )}
          </section>

          {/* Error */}
          {ctx.error && (
            <ErrorBanner message={ctx.error} onDismiss={() => ctx.setError(null)} />
          )}

          {/* Confirm */}
          <div className="pt-8">
            <Button
              variant="primary"
              size="lg"
              className="w-full"
              onClick={handleConfirm}
              disabled={ctx.isGenerating}
            >
              {ctx.isGenerating ? (
                <>
                  <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                  Generating...
                </>
              ) : (
                'Confirm & Generate Ads'
              )}
            </Button>
          </div>

        </motion.div>
      </div>
    </div>
  );
}
