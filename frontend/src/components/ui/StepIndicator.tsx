import { Check } from 'lucide-react';
import { cn } from '../../lib/cn';

interface Step {
  label: string;
}

interface StepIndicatorProps {
  steps: Step[];
  currentStep: number;
  className?: string;
}

export function StepIndicator({ steps, currentStep, className }: StepIndicatorProps) {
  return (
    <div className={cn('flex items-center justify-center gap-2', className)}>
      {steps.map((step, i) => {
        const completed = i < currentStep;
        const active = i === currentStep;

        return (
          <div key={i} className="flex items-center gap-2">
            <div className="flex items-center gap-2">
              <div
                className={cn(
                  'w-7 h-7 flex items-center justify-center text-xs font-mono border transition-colors',
                  completed && 'bg-brand-lime border-brand-lime text-brand-dark',
                  active && 'border-brand-lime text-brand-lime',
                  !completed && !active && 'border-white/20 text-gray-500'
                )}
              >
                {completed ? <Check className="w-4 h-4" /> : i + 1}
              </div>
              <span
                className={cn(
                  'text-xs font-mono hidden sm:inline',
                  active ? 'text-white' : completed ? 'text-brand-lime' : 'text-gray-500'
                )}
              >
                {step.label}
              </span>
            </div>
            {i < steps.length - 1 && (
              <div className={cn('w-8 h-px', completed ? 'bg-brand-lime' : 'bg-white/10')} />
            )}
          </div>
        );
      })}
    </div>
  );
}
