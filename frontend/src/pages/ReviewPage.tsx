import { useState, useEffect, useRef } from 'react';
import { useNavigate, Navigate } from 'react-router-dom';
import { motion } from 'framer-motion';
import { ArrowLeft, Loader2, Package, Users, AlertTriangle, Swords, Globe, Mail, Check } from 'lucide-react';
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
  const [productSummary, setProductSummary] = useState(pc?.product_summary || '');
  const [targetAudience, setTargetAudience] = useState(pc?.target_audience || '');
  const [mainPainPoint, setMainPainPoint] = useState(pc?.main_pain_point || '');
  const [messagingUnaware, setMessagingUnaware] = useState(pc?.messaging_unaware || '');
  const [messagingAware, setMessagingAware] = useState(pc?.messaging_aware || '');
  const [competitors, setCompetitors] = useState<{ name: string; weakness: string }[]>(pc?.competitors?.map(c => ({ ...c })) || []);

  // Email gate state (skip for authenticated users)
  const isAuthenticated = ctx.auth.isAuthenticated;
  const [email, setEmail] = useState(() => {
    try { return localStorage.getItem('idea2ad_lead_email') || ''; } catch { return ''; }
  });
  const [consentTerms, setConsentTerms] = useState(false);
  const [consentMarketing, setConsentMarketing] = useState(false);

  const isValidEmail = /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email);
  const canGenerate = isAuthenticated || (isValidEmail && consentTerms);

  // Sync editable fields when prepared campaign changes (e.g. re-analyze)
  const [prevPc, setPrevPc] = useState<typeof pc>(null);
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
    // Persist email for back-nav pre-fill
    if (email) {
      try { localStorage.setItem('idea2ad_lead_email', email); } catch { /* */ }
    }

    await ctx.startGeneration({
      language,
      product_summary: productSummary,
      target_audience: targetAudience,
      main_pain_point: mainPainPoint,
      messaging_unaware: messagingUnaware,
      messaging_aware: messagingAware,
      competitors: competitors.length > 0 ? competitors : undefined,
      // Email gate fields (skipped for authenticated users)
      ...(!isAuthenticated && {
        email,
        consent_terms: consentTerms,
        consent_marketing: consentMarketing,
      }),
    });
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
        <div className="max-w-4xl mx-auto flex items-center justify-between">
          <button
            onClick={() => navigate(ctx.generationMode === 'scratch' ? '/choose' : '/upload')}
            className="flex items-center gap-2 text-sm text-gray-400 hover:text-white transition-colors font-mono"
          >
            <ArrowLeft className="w-4 h-4" />
            Back
          </button>
          <div className="text-xs font-mono text-gray-500">
            {ctx.generationMode === 'replica' ? 'Step 4 of 4' : 'Step 3 of 3'}
          </div>
        </div>
      </div>

      <div className="max-w-4xl mx-auto px-6 py-6 space-y-4">
        <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }}>

          {/* Title row: logo + product + title */}
          <div className="flex items-center gap-4 mb-2">
            {pc.brand_logo_url ? (
              <img
                src={pc.brand_logo_url}
                alt="Brand logo"
                className="max-h-10 max-w-[100px] w-auto h-auto object-contain shrink-0"
              />
            ) : (
              <div className="w-10 h-10 bg-brand-gray border border-white/10 flex items-center justify-center shrink-0">
                <Package className="w-5 h-5 text-gray-500" />
              </div>
            )}
            <div className="min-w-0">
              <h1 className="text-2xl font-display font-bold leading-tight">Your Messaging Strategy</h1>
              <div className="flex items-center gap-2 mt-0.5">
                <span className="text-sm text-gray-400 font-mono truncate">{pc.product_name}</span>
                <span className="text-[10px] font-mono text-gray-600">{pc.business_type}</span>
              </div>
            </div>
          </div>

          {/* Campaign strategy box */}
          <div className="border border-white/10 bg-brand-gray/30 p-5 space-y-4">

            {/* Language selector */}
            <section className="space-y-1">
              <label className="text-[11px] font-mono text-gray-400 flex items-center gap-1">
                <Globe className="w-3 h-3 text-brand-lime" />
                Ad Language
              </label>
              <select
                value={language}
                onChange={(e) => setLanguage(e.target.value)}
                className="w-full max-w-xs bg-brand-gray border border-white/10 px-2.5 py-1.5 text-white text-xs font-mono focus:outline-none focus:border-brand-lime transition-colors appearance-none cursor-pointer"
              >
                {LANGUAGES.map((lang) => (
                  <option key={lang.code} value={lang.code}>
                    {lang.name} ({lang.code.toUpperCase()})
                  </option>
                ))}
              </select>
            </section>

            {/* Row 1: Product Summary + Target Audience */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
              <section className="space-y-1">
                <label className="text-[11px] font-mono text-gray-400 flex items-center gap-1">
                  <Package className="w-3 h-3 text-brand-lime" />
                  Product Summary
                </label>
                <div className="w-full bg-brand-gray/50 border border-white/5 px-2.5 py-2 text-gray-500 text-xs font-mono min-h-[3.5rem]">
                  {productSummary || <span className="italic text-gray-600">Not provided</span>}
                </div>
              </section>

              <section className="space-y-1">
                <label className="text-[11px] font-mono text-gray-400 flex items-center gap-1">
                  <Users className="w-3 h-3 text-brand-lime" />
                  Target Audience
                </label>
                <div className="w-full bg-brand-gray/50 border border-white/5 px-2.5 py-2 text-gray-500 text-xs font-mono min-h-[3.5rem]">
                  {targetAudience || <span className="italic text-gray-600">Not provided</span>}
                </div>
              </section>
            </div>

            {/* Row 2: Pain Point + Messaging */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
              <section className="space-y-1">
                <label className="text-[11px] font-mono text-gray-400 flex items-center gap-1">
                  <AlertTriangle className="w-3 h-3 text-brand-lime" />
                  Main Pain Point
                </label>
                <div className="w-full bg-brand-gray/50 border border-white/5 px-2.5 py-2 text-gray-500 text-xs font-mono min-h-[3.5rem]">
                  {mainPainPoint || <span className="italic text-gray-600">Not provided</span>}
                </div>
              </section>

              <section className="space-y-1">
                <label className="text-[11px] font-mono text-gray-400 flex items-center gap-1">
                  <Swords className="w-3 h-3 text-brand-lime" />
                  Competitive Landscape
                </label>
                <div className="w-full bg-brand-gray/50 border border-white/5 px-2.5 py-2 text-gray-500 text-xs font-mono min-h-[3.5rem]">
                  {competitors.length > 0
                    ? competitors.map(c => c.name).join(', ')
                    : <span className="italic text-gray-600">No competitors detected</span>
                  }
                </div>
              </section>
            </div>

            {/* Row 3: Messaging Strategy side by side */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
              <section className="space-y-1">
                <label className="text-[11px] font-mono flex items-center gap-1">
                  <span className="px-1.5 py-0.5 text-[9px] font-mono uppercase tracking-wider bg-violet-500/20 text-violet-400 border border-violet-500/30">
                    Problem-Unaware
                  </span>
                </label>
                <div className="w-full bg-brand-gray/50 border border-white/5 px-2.5 py-2 text-gray-500 text-xs font-mono min-h-[3.5rem]">
                  {messagingUnaware || <span className="italic text-gray-600">Not provided</span>}
                </div>
              </section>

              <section className="space-y-1">
                <label className="text-[11px] font-mono flex items-center gap-1">
                  <span className="px-1.5 py-0.5 text-[9px] font-mono uppercase tracking-wider bg-emerald-500/20 text-emerald-400 border border-emerald-500/30">
                    Problem-Aware
                  </span>
                </label>
                <div className="w-full bg-brand-gray/50 border border-white/5 px-2.5 py-2 text-gray-500 text-xs font-mono min-h-[3.5rem]">
                  {messagingAware || <span className="italic text-gray-600">Not provided</span>}
                </div>
              </section>
            </div>
          </div>

          {/* Email Gate (skip for authenticated users) */}
          {!isAuthenticated && (
            <section className="space-y-3 pt-3 border-t border-white/10">
              <h3 className="text-xs font-mono text-gray-300 flex items-center gap-1.5">
                <Mail className="w-3.5 h-3.5 text-brand-lime" />
                Your Email
              </h3>

              <input
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="you@company.com"
                className="w-full bg-brand-gray border border-white/10 px-4 py-3 text-white text-sm font-mono focus:outline-none focus:border-brand-lime transition-colors placeholder:text-gray-600"
              />

              {/* Terms of Service — required */}
              <label className="flex items-start gap-3 cursor-pointer group">
                <div
                  className={`mt-0.5 w-5 h-5 border flex-shrink-0 flex items-center justify-center transition-colors ${
                    consentTerms
                      ? 'bg-brand-lime border-brand-lime'
                      : 'border-white/20 group-hover:border-white/40'
                  }`}
                  onClick={() => setConsentTerms(!consentTerms)}
                  role="checkbox"
                  aria-checked={consentTerms}
                  tabIndex={0}
                  onKeyDown={(e) => e.key === ' ' && setConsentTerms(!consentTerms)}
                >
                  {consentTerms && <Check className="w-3.5 h-3.5 text-brand-dark" />}
                </div>
                <span className="text-xs font-mono text-gray-400 leading-relaxed">
                  I agree to the{' '}
                  <a href="/terms" target="_blank" className="text-brand-lime hover:underline">
                    Terms of Service
                  </a>{' '}
                  and acknowledge the{' '}
                  <a href="/privacy" target="_blank" className="text-brand-lime hover:underline">
                    Privacy Policy
                  </a>
                  .{' '}
                  <span className="text-gray-600">(Required)</span>
                </span>
              </label>

              {/* Marketing consent — optional */}
              <label className="flex items-start gap-3 cursor-pointer group">
                <div
                  className={`mt-0.5 w-5 h-5 border flex-shrink-0 flex items-center justify-center transition-colors ${
                    consentMarketing
                      ? 'bg-brand-lime border-brand-lime'
                      : 'border-white/20 group-hover:border-white/40'
                  }`}
                  onClick={() => setConsentMarketing(!consentMarketing)}
                  role="checkbox"
                  aria-checked={consentMarketing}
                  tabIndex={0}
                  onKeyDown={(e) => e.key === ' ' && setConsentMarketing(!consentMarketing)}
                >
                  {consentMarketing && <Check className="w-3.5 h-3.5 text-brand-dark" />}
                </div>
                <span className="text-xs font-mono text-gray-400 leading-relaxed">
                  I agree to receive emails from Journeylauncher LLC about product updates, new features,
                  and offers. I can unsubscribe anytime.{' '}
                  <span className="text-gray-600">(Optional)</span>
                </span>
              </label>
            </section>
          )}

          {/* Error */}
          {ctx.error && (
            <ErrorBanner message={ctx.error} onDismiss={() => ctx.setError(null)} />
          )}

          {/* Confirm */}
          <div className="pt-4">
            <Button
              variant="primary"
              size="lg"
              className="w-full"
              onClick={handleConfirm}
              disabled={ctx.isGenerating || !canGenerate}
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
            {!isAuthenticated && !canGenerate && (
              <p className="text-xs font-mono text-gray-600 text-center mt-2">
                Enter your email and accept the Terms of Service to continue
              </p>
            )}
          </div>

        </motion.div>
      </div>
    </div>
  );
}
