import { useState, useEffect, useRef } from 'react';
import { useNavigate, Navigate } from 'react-router-dom';
import { motion } from 'framer-motion';
import { ArrowLeft, Loader2, Package, Users, AlertTriangle, Swords, Pencil, Trash2, Globe } from 'lucide-react';
import { Button } from '../components/ui/Button';
import { ErrorBanner } from '../components/ui/ErrorBanner';
import { AnalysisLoadingBlueprint } from '../components/ui/AnalysisLoadingBlueprint';
import { useAppContext } from '../context/AppContext';

const LANGUAGES = [
  { code: 'en', name: 'English' },
  { code: 'es', name: 'Spanish' },
  { code: 'fr', name: 'French' },
  { code: 'de', name: 'German' },
  { code: 'it', name: 'Italian' },
  { code: 'pt', name: 'Portuguese' },
  { code: 'nl', name: 'Dutch' },
  { code: 'ru', name: 'Russian' },
  { code: 'ja', name: 'Japanese' },
  { code: 'ko', name: 'Korean' },
  { code: 'zh', name: 'Chinese' },
  { code: 'ar', name: 'Arabic' },
  { code: 'hi', name: 'Hindi' },
  { code: 'tr', name: 'Turkish' },
  { code: 'pl', name: 'Polish' },
  { code: 'sv', name: 'Swedish' },
  { code: 'da', name: 'Danish' },
  { code: 'no', name: 'Norwegian' },
  { code: 'fi', name: 'Finnish' },
  { code: 'az', name: 'Azerbaijani' },
  { code: 'uk', name: 'Ukrainian' },
  { code: 'ro', name: 'Romanian' },
  { code: 'cs', name: 'Czech' },
  { code: 'el', name: 'Greek' },
  { code: 'he', name: 'Hebrew' },
  { code: 'th', name: 'Thai' },
  { code: 'vi', name: 'Vietnamese' },
  { code: 'id', name: 'Indonesian' },
  { code: 'ms', name: 'Malay' },
  { code: 'ka', name: 'Georgian' },
] as const;

export default function ReviewPage() {
  const ctx = useAppContext();
  const navigate = useNavigate();
  const wasGenerating = useRef(false);

  const pc = ctx.preparedCampaign;

  // Editable state initialized from prepared campaign
  const [language, setLanguage] = useState('en');
  const [productSummary, setProductSummary] = useState('');
  const [targetAudience, setTargetAudience] = useState('');
  const [mainPainPoint, setMainPainPoint] = useState('');
  const [messagingUnaware, setMessagingUnaware] = useState('');
  const [messagingAware, setMessagingAware] = useState('');
  const [competitors, setCompetitors] = useState<{ name: string; weakness: string }[]>([]);
  const [editingCompetitor, setEditingCompetitor] = useState<number | null>(null);

  // Sync editable fields when prepared campaign changes (React docs pattern)
  const [prevPc, setPrevPc] = useState(pc);
  if (pc && pc !== prevPc) {
    setPrevPc(pc);
    setLanguage('en');
    setProductSummary(pc.product_summary || '');
    setTargetAudience(pc.target_audience || '');
    setMainPainPoint(pc.main_pain_point || '');
    setMessagingUnaware(pc.messaging_unaware || '');
    setMessagingAware(pc.messaging_aware || '');
    setCompetitors(pc.competitors?.map(c => ({ ...c })) || []);
  }

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
      language,
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

  // Show Blueprint Builder loading screen when generating
  if (ctx.isGenerating) {
    return (
      <AnalysisLoadingBlueprint
        title="Generating Your Ads"
        productLabel={pc.product_name}
        onCancel={ctx.cancelGeneration}
      />
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
              {pc.business_type}
            </div>
          </div>

          {/* Ad Language */}
          <section className="space-y-3">
            <label className="text-sm font-mono text-gray-300 flex items-center gap-2">
              <Globe className="w-4 h-4 text-brand-lime" />
              Ad Language
            </label>
            <select
              value={language}
              onChange={(e) => setLanguage(e.target.value)}
              className="w-full bg-brand-gray border border-white/10 px-4 py-3 text-white text-sm font-mono focus:outline-none focus:border-brand-lime transition-colors appearance-none cursor-pointer"
            >
              {LANGUAGES.map((lang) => (
                <option key={lang.code} value={lang.code}>
                  {lang.name} ({lang.code.toUpperCase()})
                </option>
              ))}
            </select>
            <p className="text-xs font-mono text-gray-600">All ad copy will be generated in this language</p>
          </section>

          {/* Product Summary */}
          <section className="space-y-3 pt-6 border-t border-white/10">
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
                  Problem-Unaware Users
                </span>
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
                  Problem-Aware Users
                </span>
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
