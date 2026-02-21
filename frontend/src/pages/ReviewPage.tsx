import { useState, useEffect, useRef } from 'react';
import { useNavigate, Navigate } from 'react-router-dom';
import { motion } from 'framer-motion';
import { ArrowLeft, Globe, Users, Calendar, DollarSign, Loader2, Package } from 'lucide-react';
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
  const [ageMin, setAgeMin] = useState(18);
  const [ageMax, setAgeMax] = useState(65);
  const [countries, setCountries] = useState('US');
  const [gender, setGender] = useState<'all' | 'male' | 'female'>('all');
  const [budgetDaily, setBudgetDaily] = useState(15);
  const [durationDays, setDurationDays] = useState(3);

  // Initialize from prepared campaign
  useEffect(() => {
    if (!pc) return;
    setProductSummary(pc.product_summary || '');
    setAgeMin(pc.targeting.age_min);
    setAgeMax(pc.targeting.age_max);
    setCountries((pc.targeting.geo_locations?.countries || ['US']).join(', '));
    setGender(
      pc.targeting.genders === null ? 'all'
        : pc.targeting.genders?.includes(1) ? 'male' : 'female'
    );
    setBudgetDaily(pc.budget_daily_cents / 100);
    setDurationDays(pc.duration_days);
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
    const countryList = countries.split(',').map(c => c.trim().toUpperCase()).filter(Boolean);
    const genderValues = gender === 'all' ? null : gender === 'male' ? [1] : [2];

    await ctx.startGeneration({
      targeting: {
        geo_locations: { countries: countryList },
        age_min: ageMin,
        age_max: ageMax,
        genders: genderValues,
        targeting_rationale: pc.targeting.targeting_rationale,
      },
      budget_daily_cents: Math.round(budgetDaily * 100),
      duration_days: durationDays,
      product_summary: productSummary,
    });
  };

  const totalBudget = budgetDaily * durationDays;

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

          {/* Targeting */}
          <section className="space-y-4 pt-6 border-t border-white/10">
            <h3 className="text-sm font-mono text-gray-300 flex items-center gap-2">
              <Users className="w-4 h-4 text-brand-lime" />
              Targeting
            </h3>

            <div className="grid grid-cols-2 gap-4">
              {/* Age Range */}
              <div className="space-y-2">
                <label className="text-xs font-mono text-gray-500">Age Min</label>
                <input
                  type="number"
                  value={ageMin}
                  onChange={(e) => setAgeMin(Number(e.target.value))}
                  min={13}
                  max={65}
                  className="w-full h-10 bg-brand-gray border border-white/10 px-3 text-white text-sm font-mono focus:outline-none focus:border-brand-lime transition-colors"
                />
              </div>
              <div className="space-y-2">
                <label className="text-xs font-mono text-gray-500">Age Max</label>
                <input
                  type="number"
                  value={ageMax}
                  onChange={(e) => setAgeMax(Number(e.target.value))}
                  min={13}
                  max={65}
                  className="w-full h-10 bg-brand-gray border border-white/10 px-3 text-white text-sm font-mono focus:outline-none focus:border-brand-lime transition-colors"
                />
              </div>
            </div>

            {/* Countries */}
            <div className="space-y-2">
              <label className="text-xs font-mono text-gray-500 flex items-center gap-1">
                <Globe className="w-3 h-3" /> Countries (comma-separated ISO codes)
              </label>
              <input
                type="text"
                value={countries}
                onChange={(e) => setCountries(e.target.value)}
                placeholder="US, CA, GB"
                className="w-full h-10 bg-brand-gray border border-white/10 px-3 text-white text-sm font-mono focus:outline-none focus:border-brand-lime transition-colors"
              />
            </div>

            {/* Gender */}
            <div className="space-y-2">
              <label className="text-xs font-mono text-gray-500">Gender</label>
              <div className="flex gap-2">
                {(['all', 'male', 'female'] as const).map((g) => (
                  <button
                    key={g}
                    type="button"
                    onClick={() => setGender(g)}
                    className={`px-4 py-2 text-xs font-mono border transition-colors ${
                      gender === g
                        ? 'bg-brand-lime text-brand-dark border-brand-lime'
                        : 'bg-brand-gray border-white/10 text-gray-400 hover:border-white/20'
                    }`}
                  >
                    {g.charAt(0).toUpperCase() + g.slice(1)}
                  </button>
                ))}
              </div>
            </div>
          </section>

          {/* Budget & Duration */}
          <section className="space-y-4 pt-6 border-t border-white/10">
            <h3 className="text-sm font-mono text-gray-300 flex items-center gap-2">
              <DollarSign className="w-4 h-4 text-brand-lime" />
              Budget & Duration
            </h3>

            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2">
                <label className="text-xs font-mono text-gray-500">Daily Budget ($)</label>
                <input
                  type="number"
                  value={budgetDaily}
                  onChange={(e) => setBudgetDaily(Number(e.target.value))}
                  min={1}
                  step={1}
                  className="w-full h-10 bg-brand-gray border border-white/10 px-3 text-white text-sm font-mono focus:outline-none focus:border-brand-lime transition-colors"
                />
              </div>
              <div className="space-y-2">
                <label className="text-xs font-mono text-gray-500 flex items-center gap-1">
                  <Calendar className="w-3 h-3" /> Duration (days)
                </label>
                <input
                  type="number"
                  value={durationDays}
                  onChange={(e) => setDurationDays(Number(e.target.value))}
                  min={1}
                  max={90}
                  className="w-full h-10 bg-brand-gray border border-white/10 px-3 text-white text-sm font-mono focus:outline-none focus:border-brand-lime transition-colors"
                />
              </div>
            </div>

            <div className="flex items-center justify-between p-3 bg-brand-gray border border-white/10">
              <span className="text-xs font-mono text-gray-400">Total Budget</span>
              <span className="text-lg font-display font-bold text-brand-lime">${totalBudget.toFixed(0)}</span>
            </div>
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
