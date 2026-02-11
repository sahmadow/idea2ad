import { useRef } from 'react';
import { motion } from 'framer-motion';
import { cn } from '../../lib/cn';

interface SegmentedControlProps<T extends string> {
  options: { value: T; label: string }[];
  value: T;
  onChange: (value: T) => void;
  className?: string;
}

export function SegmentedControl<T extends string>({
  options,
  value,
  onChange,
  className,
}: SegmentedControlProps<T>) {
  const containerRef = useRef<HTMLDivElement>(null);

  const handleKeyDown = (e: React.KeyboardEvent) => {
    const idx = options.findIndex(o => o.value === value);
    if (e.key === 'ArrowRight' || e.key === 'ArrowDown') {
      e.preventDefault();
      const next = (idx + 1) % options.length;
      onChange(options[next].value);
    } else if (e.key === 'ArrowLeft' || e.key === 'ArrowUp') {
      e.preventDefault();
      const prev = (idx - 1 + options.length) % options.length;
      onChange(options[prev].value);
    }
  };

  return (
    <div
      ref={containerRef}
      role="radiogroup"
      className={cn('inline-flex bg-brand-gray border border-white/10 p-1 relative', className)}
      onKeyDown={handleKeyDown}
    >
      {options.map((option) => (
        <button
          key={option.value}
          role="radio"
          aria-checked={value === option.value}
          tabIndex={value === option.value ? 0 : -1}
          onClick={() => onChange(option.value)}
          className={cn(
            'relative px-5 py-2 text-sm font-mono transition-colors z-10',
            value === option.value ? 'text-brand-dark' : 'text-gray-400 hover:text-white'
          )}
        >
          {value === option.value && (
            <motion.div
              layoutId="segment-indicator"
              className="absolute inset-0 bg-brand-lime"
              transition={{ type: 'spring', stiffness: 400, damping: 30 }}
            />
          )}
          <span className="relative z-10">{option.label}</span>
        </button>
      ))}
    </div>
  );
}
