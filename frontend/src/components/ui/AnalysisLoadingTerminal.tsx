/**
 * Analysis Loading — Terminal Console
 * Spinner + stage dots + Terminal with log lines.
 * Fires onComplete after all terminal steps finish.
 */
import { useState, useEffect } from 'react';
import { Terminal } from './Terminal';

const ANALYSIS_STAGES = [
  'Scraping Page',
  'Extracting Data',
  'Finding Competitors',
  'Building Profile',
];

const TERMINAL_STEPS = [
  { text: '> Connecting to landing page...', delay: 400 },
  { text: '> Scraping page content (12 sections found)', delay: 1200 },
  { text: '> Extracting brand colors & fonts...', delay: 2200 },
  { text: '> Identifying product category...', delay: 3200 },
  { text: '> Detecting competitors in market...', delay: 4200 },
  { text: '> Building audience profile...', delay: 5200 },
  { text: '> READY. Preparing your workspace.', delay: 6200 },
];

// Stage dots advance at these timestamps
const STAGE_DELAYS = [1000, 2800, 4500, 5800];

interface Props {
  productLabel?: string;
  onCancel?: () => void;
  onComplete?: () => void;
}

export function AnalysisLoadingTerminal({ productLabel, onCancel, onComplete }: Props) {
  const [stage, setStage] = useState(0);

  useEffect(() => {
    const ids = STAGE_DELAYS.map((delay, i) =>
      setTimeout(() => setStage(i + 1), delay)
    );
    return () => ids.forEach(clearTimeout);
  }, []);

  return (
    <div className="min-h-screen bg-brand-dark text-white flex flex-col items-center justify-center px-6">
      <div className="text-center space-y-8 max-w-md w-full">
        {/* Spinner */}
        <div className="w-16 h-16 border-2 border-brand-lime/30 border-t-brand-lime rounded-full animate-spin mx-auto" />

        {/* Title */}
        <div>
          <h2 className="text-2xl font-display font-bold mb-2">Analyzing Your Product</h2>
          {productLabel && (
            <p className="text-gray-400 font-mono text-sm">{productLabel}</p>
          )}
        </div>

        {/* Stage dots */}
        <div className="flex justify-center gap-3">
          {ANALYSIS_STAGES.map((s, i) => (
            <div key={s} className="flex items-center gap-2">
              <div className={`w-2 h-2 ${i <= stage ? 'bg-brand-lime' : 'bg-white/20'} transition-colors`} />
              <span className={`text-xs font-mono ${i <= stage ? 'text-white' : 'text-gray-600'} hidden sm:inline transition-colors`}>
                {s}
              </span>
            </div>
          ))}
        </div>

        {/* Terminal */}
        <Terminal steps={TERMINAL_STEPS} onComplete={onComplete} />

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
