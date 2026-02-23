import React from 'react';
import { Loader2 } from 'lucide-react';
import { cn } from '../../lib/cn';

interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
    variant?: 'primary' | 'secondary' | 'outline' | 'ghost';
    size?: 'sm' | 'md' | 'lg';
    loading?: boolean;
}

export const Button = React.forwardRef<HTMLButtonElement, ButtonProps>(
    ({ className, variant = 'primary', size = 'md', loading = false, children, disabled, ...props }, ref) => {
        return (
            <button
                ref={ref}
                disabled={disabled || loading}
                className={cn(
                    'inline-flex items-center justify-center font-mono font-medium uppercase tracking-wide transition-colors duration-200',
                    'focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-brand-lime focus-visible:ring-offset-2 focus-visible:ring-offset-white dark:focus-visible:ring-offset-brand-dark',
                    'disabled:pointer-events-none disabled:opacity-50',
                    'rounded-none',
                    {
                        'bg-brand-lime text-brand-dark hover:bg-brand-lime-dark': variant === 'primary',
                        'bg-gray-100 text-gray-900 dark:bg-brand-gray dark:text-white hover:bg-brand-lime hover:text-brand-dark': variant === 'secondary',
                        'border border-brand-lime text-brand-lime hover:bg-brand-lime hover:text-brand-dark': variant === 'outline',
                        'text-gray-600 dark:text-brand-light hover:text-brand-lime': variant === 'ghost',
                        'h-9 px-4 text-sm': size === 'sm',
                        'h-11 px-6 text-sm': size === 'md',
                        'h-14 px-8 text-base': size === 'lg',
                    },
                    className
                )}
                {...props}
            >
                {loading && <Loader2 className="w-4 h-4 mr-2 animate-spin" />}
                {children}
            </button>
        );
    }
);

Button.displayName = 'Button';
