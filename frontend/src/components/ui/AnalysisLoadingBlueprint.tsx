/**
 * Analysis Loading — Option 3: Blueprint Builder
 * Shows an ad creative wireframe being "drawn" stroke by stroke as analysis progresses.
 */
import { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';

const STEPS = [
  { id: 'header', label: 'Scraping landing page...', delay: 0 },
  { id: 'image', label: 'Extracting visual assets...', delay: 2500 },
  { id: 'headline', label: 'Analyzing messaging...', delay: 5000 },
  { id: 'cta', label: 'Building CTA strategy...', delay: 7500 },
  { id: 'engagement', label: 'Profiling audience...', delay: 9500 },
  { id: 'done', label: 'Preparing your review...', delay: 11500 },
];

interface Props {
  title?: string;
  productLabel?: string;
  onCancel?: () => void;
}

export function AnalysisLoadingBlueprint({ title = 'Analyzing Your Product', productLabel, onCancel }: Props) {
  const [visibleParts, setVisibleParts] = useState<Set<string>>(new Set());
  const [currentStep, setCurrentStep] = useState(0);

  useEffect(() => {
    const ids: ReturnType<typeof setTimeout>[] = [];

    STEPS.forEach((step, i) => {
      ids.push(setTimeout(() => {
        setVisibleParts(prev => new Set([...prev, step.id]));
        setCurrentStep(i);
      }, step.delay));
    });

    return () => ids.forEach(clearTimeout);
  }, []);

  const progress = ((currentStep + 1) / STEPS.length) * 100;
  const show = (id: string) => visibleParts.has(id);

  const fadeIn = {
    hidden: { opacity: 0, y: 8 },
    visible: { opacity: 1, y: 0, transition: { duration: 0.5 } },
  };

  return (
    <div className="min-h-screen bg-brand-dark text-white flex flex-col items-center justify-center px-6">
      <div className="text-center space-y-8 max-w-md w-full">
        {/* Title */}
        <div>
          <h2 className="text-2xl font-display font-bold mb-2">{title}</h2>
          {productLabel && (
            <p className="text-gray-400 font-mono text-sm">{productLabel}</p>
          )}
        </div>

        {/* Blueprint ad preview */}
        <div className="relative w-72 mx-auto bg-brand-gray/30 border border-white/10 overflow-hidden">
          {/* Ad Header — Brand + Sponsored */}
          <AnimatePresence>
            {show('header') && (
              <motion.div
                variants={fadeIn}
                initial="hidden"
                animate="visible"
                className="p-3 flex items-center gap-2 border-b border-white/5"
              >
                <motion.div
                  className="w-8 h-8 rounded-full border border-brand-lime/40"
                  animate={{ borderColor: ['rgba(56,189,248,0.4)', 'rgba(56,189,248,0.8)', 'rgba(56,189,248,0.4)'] }}
                  transition={{ duration: 2, repeat: Infinity }}
                >
                  <div className="w-full h-full rounded-full bg-gradient-to-br from-brand-lime/20 to-transparent" />
                </motion.div>
                <div className="flex-1">
                  <div className="h-2.5 w-24 bg-white/20 rounded-sm" />
                  <div className="h-2 w-16 bg-white/10 rounded-sm mt-1.5" />
                </div>
              </motion.div>
            )}
          </AnimatePresence>

          {/* Primary text area */}
          <AnimatePresence>
            {show('header') && (
              <motion.div
                variants={fadeIn}
                initial="hidden"
                animate="visible"
                transition={{ delay: 0.3 }}
                className="px-3 py-2"
              >
                <div className="space-y-1.5">
                  <div className="h-2 w-full bg-white/10 rounded-sm" />
                  <div className="h-2 w-3/4 bg-white/10 rounded-sm" />
                </div>
              </motion.div>
            )}
          </AnimatePresence>

          {/* Image area — scanning shimmer */}
          <AnimatePresence>
            {show('image') && (
              <motion.div
                variants={fadeIn}
                initial="hidden"
                animate="visible"
                className="relative aspect-square bg-brand-gray/50 mx-0 overflow-hidden"
              >
                {/* Scan line sweeping down */}
                <motion.div
                  className="absolute left-0 right-0 h-px bg-brand-lime/60 shadow-[0_0_8px_rgba(56,189,248,0.4)]"
                  animate={{ top: ['0%', '100%'] }}
                  transition={{ duration: 2.5, repeat: Infinity, ease: 'linear' }}
                />
                {/* Grid pattern */}
                <svg className="absolute inset-0 w-full h-full" xmlns="http://www.w3.org/2000/svg">
                  <defs>
                    <pattern id="grid" width="20" height="20" patternUnits="userSpaceOnUse">
                      <path d="M 20 0 L 0 0 0 20" fill="none" stroke="rgba(255,255,255,0.03)" strokeWidth="0.5" />
                    </pattern>
                  </defs>
                  <rect width="100%" height="100%" fill="url(#grid)" />
                </svg>
                {/* Center icon placeholder */}
                <div className="absolute inset-0 flex items-center justify-center">
                  <motion.div
                    className="w-12 h-12 border border-white/10 rounded-sm flex items-center justify-center"
                    animate={{ opacity: [0.3, 0.6, 0.3] }}
                    transition={{ duration: 2, repeat: Infinity }}
                  >
                    <svg className="w-6 h-6 text-white/20" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1} d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z" />
                    </svg>
                  </motion.div>
                </div>
              </motion.div>
            )}
          </AnimatePresence>

          {/* Headline + CTA bar */}
          <AnimatePresence>
            {show('headline') && (
              <motion.div
                variants={fadeIn}
                initial="hidden"
                animate="visible"
                className="p-3 flex items-center justify-between border-t border-white/5 bg-white/[0.02]"
              >
                <div className="flex-1 space-y-1.5">
                  <div className="h-2 w-16 bg-white/10 rounded-sm" />
                  <motion.div
                    className="h-3 w-32 bg-white/20 rounded-sm"
                    animate={{ opacity: [0.5, 1, 0.5] }}
                    transition={{ duration: 1.5, repeat: Infinity }}
                  />
                  <div className="h-2 w-24 bg-white/10 rounded-sm" />
                </div>
                {show('cta') && (
                  <motion.div
                    initial={{ opacity: 0, scale: 0.8 }}
                    animate={{ opacity: 1, scale: 1 }}
                    className="px-4 py-1.5 border border-brand-lime/30 bg-brand-lime/10 rounded-sm"
                  >
                    <div className="h-2.5 w-14 bg-brand-lime/40 rounded-sm" />
                  </motion.div>
                )}
              </motion.div>
            )}
          </AnimatePresence>

          {/* Engagement bar */}
          <AnimatePresence>
            {show('engagement') && (
              <motion.div
                variants={fadeIn}
                initial="hidden"
                animate="visible"
                className="px-3 py-2 flex items-center justify-between border-t border-white/5"
              >
                <div className="flex gap-4">
                  {['w-10', 'w-14', 'w-8'].map((w, i) => (
                    <motion.div
                      key={i}
                      className={`h-2 ${w} bg-white/10 rounded-sm`}
                      initial={{ opacity: 0 }}
                      animate={{ opacity: 1 }}
                      transition={{ delay: i * 0.15 }}
                    />
                  ))}
                </div>
              </motion.div>
            )}
          </AnimatePresence>
        </div>

        {/* Status + progress */}
        <div className="space-y-3">
          <div className="flex items-center justify-center gap-3">
            {STEPS.slice(0, -1).map((step, i) => (
              <div key={step.id} className="flex items-center gap-1.5">
                <div className={`w-1.5 h-1.5 ${i <= currentStep ? 'bg-brand-lime' : 'bg-white/15'} transition-colors`} />
              </div>
            ))}
          </div>
          <AnimatePresence mode="wait">
            <motion.p
              key={STEPS[currentStep].label}
              initial={{ opacity: 0, y: 5 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -5 }}
              className="text-sm font-mono text-gray-400"
            >
              {STEPS[currentStep].label}
            </motion.p>
          </AnimatePresence>
          <div className="h-0.5 bg-white/5 rounded-full overflow-hidden">
            <motion.div
              className="h-full bg-brand-lime"
              animate={{ width: `${progress}%` }}
              transition={{ duration: 0.5 }}
            />
          </div>
        </div>

        {/* Cancel */}
        {onCancel && (
          <button
            onClick={onCancel}
            className="text-sm font-mono text-gray-500 hover:text-white transition-colors"
          >
            Cancel
          </button>
        )}
      </div>
    </div>
  );
}
