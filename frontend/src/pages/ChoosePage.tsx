import { useRef, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { motion } from 'framer-motion';
import { ArrowLeft, ImagePlus, Sparkles } from 'lucide-react';
import { ErrorBanner } from '../components/ui/ErrorBanner';
import { AnalysisLoadingOrbit } from '../components/ui/AnalysisLoadingOrbit';
import { useAppContext } from '../context/AppContext';

export default function ChoosePage() {
  const ctx = useAppContext();
  const navigate = useNavigate();
  const wasAnalyzing = useRef(false);

  // Guard: must have input from step 1
  useEffect(() => {
    if (!ctx.input.trim()) {
      navigate('/', { replace: true });
    }
  }, [ctx.input, navigate]);

  // Track when analysis starts
  useEffect(() => {
    if (ctx.isAnalyzing) wasAnalyzing.current = true;
  }, [ctx.isAnalyzing]);

  // Navigate to review when analysis completes
  useEffect(() => {
    if (wasAnalyzing.current && !ctx.isAnalyzing && ctx.preparedCampaign) {
      wasAnalyzing.current = false;
      navigate('/review', { replace: true });
    }
  }, [ctx.preparedCampaign, ctx.isAnalyzing, navigate]);

  if (!ctx.input.trim()) return null;

  // Full-screen orbit during analysis (scratch path)
  if (ctx.isAnalyzing) {
    return (
      <AnalysisLoadingOrbit
        productLabel={ctx.input.trim()}
        onCancel={ctx.cancelGeneration}
      />
    );
  }

  const truncatedInput = ctx.input.trim().length > 60
    ? ctx.input.trim().slice(0, 60) + '...'
    : ctx.input.trim();

  const handleReference = () => {
    ctx.setGenerationMode('replica');
    navigate('/upload');
  };

  const handleScratch = async () => {
    ctx.setGenerationMode('scratch');
    await ctx.startAnalysis();
  };

  return (
    <div className="min-h-screen bg-brand-dark text-white flex flex-col">
      {/* Header */}
      <div className="border-b border-white/5 px-6 py-4">
        <div className="max-w-2xl mx-auto flex items-center justify-between">
          <button
            onClick={() => navigate('/')}
            className="flex items-center gap-2 text-sm text-gray-400 hover:text-white transition-colors font-mono"
          >
            <ArrowLeft className="w-4 h-4" />
            Back
          </button>
          <div className="text-xs font-mono text-gray-500">Step 2 of 4</div>
        </div>
      </div>

      {/* Content */}
      <div className="flex-1 flex items-center justify-center px-6 py-12">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="w-full max-w-2xl space-y-8"
        >
          <div className="text-center space-y-3">
            <h2 className="text-2xl font-display font-bold">Choose Your Approach</h2>
            <p className="text-brand-lime font-mono text-sm truncate max-w-md mx-auto">
              {truncatedInput}
            </p>
          </div>

          {/* Error */}
          {ctx.error && (
            <ErrorBanner message={ctx.error} onDismiss={() => ctx.setError(null)} />
          )}

          {/* Cards */}
          <div
            className="grid md:grid-cols-2 gap-6"
            role="radiogroup"
            aria-label="Ad generation approach"
          >
            {/* Card 1: Generate from Reference */}
            <motion.button
              whileHover={{ scale: 1.02 }}
              whileTap={{ scale: 0.98 }}
              onClick={handleReference}
              role="radio"
              aria-checked={ctx.generationMode === 'replica'}
              className="relative bg-brand-dark border border-brand-lime/30 hover:border-brand-lime/50 p-6 text-left transition-colors cursor-pointer"
            >
              {/* Recommended badge */}
              <span className="absolute top-4 right-4 px-2.5 py-1 text-[10px] font-mono uppercase tracking-wider bg-status-success/20 text-status-success border border-status-success/30 rounded-full">
                Recommended
              </span>

              <div className="space-y-4">
                <div className="w-12 h-12 bg-brand-gray border border-white/10 flex items-center justify-center">
                  <ImagePlus className="w-6 h-6 text-brand-lime" />
                </div>
                <div>
                  <h3 className="font-display font-bold text-lg">Generate from Reference</h3>
                  <p className="text-gray-400 text-sm mt-1">
                    Upload a visual reference — a competitor ad, another brand's creative, or any design you'd like to replicate.
                  </p>
                </div>
                <ul className="space-y-1.5">
                  {['Style-matched to reference', 'Proven ad layouts', 'Competitive edge'].map((item) => (
                    <li key={item} className="text-xs font-mono text-gray-500 flex items-center gap-2">
                      <span className="text-brand-lime">&#10003;</span>
                      {item}
                    </li>
                  ))}
                </ul>
              </div>
            </motion.button>

            {/* Card 2: Generate from Scratch */}
            <motion.button
              whileHover={{ scale: 1.02 }}
              whileTap={{ scale: 0.98 }}
              onClick={handleScratch}
              role="radio"
              aria-checked={ctx.generationMode === 'scratch'}
              className="relative bg-brand-dark border border-white/10 hover:border-white/20 p-6 text-left transition-colors cursor-pointer"
            >
              <div className="space-y-4">
                <div className="w-12 h-12 bg-brand-gray border border-white/10 flex items-center justify-center">
                  <Sparkles className="w-6 h-6 text-brand-lime" />
                </div>
                <div>
                  <h3 className="font-display font-bold text-lg">Generate from Scratch</h3>
                  <p className="text-gray-400 text-sm mt-1">
                    No visual assets needed. Our AI creates original ad concepts based on your brand analysis.
                  </p>
                </div>
                <ul className="space-y-1.5">
                  {['Pure AI creativity', 'No uploads required', 'Quick start'].map((item) => (
                    <li key={item} className="text-xs font-mono text-gray-500 flex items-center gap-2">
                      <span className="text-brand-lime">&#10003;</span>
                      {item}
                    </li>
                  ))}
                </ul>
              </div>
            </motion.button>
          </div>
        </motion.div>
      </div>
    </div>
  );
}
