/**
 * Analysis Loading — Option 2: Orbit Scanner
 * Pulsing concentric rings with data chips flying out as analysis discovers data.
 */
import { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';

interface DataChip {
  id: string;
  label: string;
  value: string;
  color: string;
}

const DISCOVERY_SEQUENCE: { chip: DataChip; delay: number; status: string }[] = [
  {
    chip: { id: 'brand', label: 'Brand', value: '#FF9900', color: 'border-orange-500/40 bg-orange-500/10' },
    delay: 2000,
    status: 'Scraping landing page...',
  },
  {
    chip: { id: 'category', label: 'Category', value: 'Audiobooks', color: 'border-blue-500/40 bg-blue-500/10' },
    delay: 4000,
    status: 'Extracting product data...',
  },
  {
    chip: { id: 'audience', label: 'Audience', value: 'Book lovers, 25-55', color: 'border-emerald-500/40 bg-emerald-500/10' },
    delay: 6500,
    status: 'Profiling target audience...',
  },
  {
    chip: { id: 'pain', label: 'Pain Point', value: 'No time to read', color: 'border-red-500/40 bg-red-500/10' },
    delay: 8500,
    status: 'Analyzing customer pain points...',
  },
  {
    chip: { id: 'competitor', label: 'Competitor', value: 'Spotify, Scribd', color: 'border-violet-500/40 bg-violet-500/10' },
    delay: 10500,
    status: 'Detecting competitors...',
  },
  {
    chip: { id: 'messaging', label: 'Messaging', value: 'Listen anywhere', color: 'border-brand-lime/40 bg-brand-lime/10' },
    delay: 12500,
    status: 'Crafting messaging strategy...',
  },
];

interface Props {
  productLabel?: string;
  onCancel?: () => void;
}

export function AnalysisLoadingOrbit({ productLabel, onCancel }: Props) {
  const [chips, setChips] = useState<DataChip[]>([]);
  const [status, setStatus] = useState('Connecting...');
  const [progress, setProgress] = useState(5);

  useEffect(() => {
    const ids: ReturnType<typeof setTimeout>[] = [];

    DISCOVERY_SEQUENCE.forEach(({ chip, delay, status: s }, i) => {
      ids.push(setTimeout(() => {
        setChips(prev => [...prev, chip]);
        setStatus(s);
        setProgress(Math.min(95, ((i + 1) / DISCOVERY_SEQUENCE.length) * 100));
      }, delay));
    });

    return () => ids.forEach(clearTimeout);
  }, []);

  // Chip grid positions (2 columns)
  const chipPositions = [
    'col-start-1', 'col-start-2',
    'col-start-1', 'col-start-2',
    'col-start-1', 'col-start-2',
  ];

  return (
    <div className="min-h-screen bg-brand-dark text-white flex flex-col items-center justify-center px-6">
      <div className="text-center space-y-8 max-w-md w-full">
        {/* Title */}
        <div>
          <h2 className="text-2xl font-display font-bold mb-2">Analyzing Your Product</h2>
          {productLabel && (
            <p className="text-gray-400 font-mono text-sm">{productLabel}</p>
          )}
        </div>

        {/* Orbit scanner */}
        <div className="relative w-48 h-48 mx-auto">
          {/* Ring 3 (outer) */}
          <motion.div
            className="absolute inset-0 border border-white/5 rounded-full"
            animate={{ scale: [1, 1.05, 1], opacity: [0.3, 0.6, 0.3] }}
            transition={{ duration: 3, repeat: Infinity, ease: 'easeInOut' }}
          />
          {/* Ring 2 */}
          <motion.div
            className="absolute inset-6 border border-white/10 rounded-full"
            animate={{ scale: [1, 1.08, 1], opacity: [0.4, 0.8, 0.4] }}
            transition={{ duration: 2.5, repeat: Infinity, ease: 'easeInOut', delay: 0.3 }}
          />
          {/* Ring 1 (inner) */}
          <motion.div
            className="absolute inset-12 border border-brand-lime/20 rounded-full"
            animate={{ scale: [1, 1.1, 1], opacity: [0.5, 1, 0.5] }}
            transition={{ duration: 2, repeat: Infinity, ease: 'easeInOut', delay: 0.6 }}
          />
          {/* Center dot */}
          <motion.div
            className="absolute inset-0 flex items-center justify-center"
            animate={{ scale: [1, 1.2, 1] }}
            transition={{ duration: 1.5, repeat: Infinity, ease: 'easeInOut' }}
          >
            <div className="w-4 h-4 bg-brand-lime rounded-full shadow-[0_0_20px_rgba(56,189,248,0.5)]" />
          </motion.div>
          {/* Rotating scan line */}
          <motion.div
            className="absolute inset-0"
            animate={{ rotate: 360 }}
            transition={{ duration: 4, repeat: Infinity, ease: 'linear' }}
          >
            <div className="absolute top-1/2 left-1/2 w-1/2 h-px bg-gradient-to-r from-brand-lime/60 to-transparent origin-left" />
          </motion.div>
        </div>

        {/* Data chips grid */}
        <div className="grid grid-cols-2 gap-2 min-h-[120px]">
          <AnimatePresence>
            {chips.map((chip, i) => (
              <motion.div
                key={chip.id}
                initial={{ opacity: 0, scale: 0.5, y: -20 }}
                animate={{ opacity: 1, scale: 1, y: 0 }}
                transition={{ type: 'spring', stiffness: 300, damping: 20 }}
                className={`${chipPositions[i]} border ${chip.color} px-3 py-2 text-left`}
              >
                <div className="text-[10px] font-mono text-gray-500 uppercase tracking-wider">{chip.label}</div>
                <div className="text-xs font-mono text-white truncate">{chip.value}</div>
              </motion.div>
            ))}
          </AnimatePresence>
        </div>

        {/* Status + progress */}
        <div className="space-y-3">
          <motion.p
            key={status}
            initial={{ opacity: 0, y: 5 }}
            animate={{ opacity: 1, y: 0 }}
            className="text-sm font-mono text-gray-400"
          >
            {status}
          </motion.p>
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
