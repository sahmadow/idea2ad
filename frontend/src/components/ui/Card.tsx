import React from 'react';
import { cn } from '../../lib/cn';

interface CardProps extends React.HTMLAttributes<HTMLDivElement> {
    variant?: 'default' | 'elevated' | 'highlighted';
    showGrid?: boolean;
}

export function Card({ className, variant = 'default', showGrid = false, children, ...props }: CardProps) {
    return (
        <div
            className={cn(
                'relative bg-white dark:bg-brand-dark border overflow-hidden transition-colors',
                {
                    'border-gray-200 dark:border-white/10 hover:border-gray-300 dark:hover:border-white/20': variant === 'default',
                    'border-gray-200 dark:border-white/10 hover:border-gray-300 dark:hover:border-white/20 shadow-lg shadow-gray-200/50 dark:shadow-black/20': variant === 'elevated',
                    'border-brand-lime/30 hover:border-brand-lime/50': variant === 'highlighted',
                },
                showGrid && 'before:content-[""] before:absolute before:inset-0 before:bg-grid-pattern before:opacity-[0.05] before:pointer-events-none',
                className
            )}
            {...props}
        >
            {children}
        </div>
    );
}

export function CardHeader({ className, children, ...props }: React.HTMLAttributes<HTMLDivElement>) {
    return <div className={cn('p-6', className)} {...props}>{children}</div>;
}

export function CardContent({ className, children, ...props }: React.HTMLAttributes<HTMLDivElement>) {
    return <div className={cn('p-6 pt-0', className)} {...props}>{children}</div>;
}
