import { useEffect, useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { SkipForward } from 'lucide-react';

interface TerminalProps {
    steps?: { text: string; delay: number }[];
    onSkip?: () => void;
    onComplete?: () => void;
}

const defaultSteps = [
    { text: '> Analyzing landing page...', delay: 500 },
    { text: '> Extracting brand colors: #1A1A1A, #38BDF8', delay: 1500 },
    { text: '> Identifying USP: "AI-Powered Ad Campaigns"', delay: 2500 },
    { text: '> Generating copy variations...', delay: 3500 },
    { text: '> DONE. Campaign ready for launch.', delay: 4500 },
];

export function Terminal({ steps = defaultSteps, onSkip, onComplete }: TerminalProps) {
    const [lines, setLines] = useState<string[]>([]);
    const [showSkip, setShowSkip] = useState(false);
    const [completed, setCompleted] = useState(false);

    const progress = steps.length > 0 ? (lines.length / steps.length) * 100 : 0;

    useEffect(() => {
        const timeoutIds: ReturnType<typeof setTimeout>[] = [];

        // Show skip button after 1s
        const skipId = setTimeout(() => setShowSkip(true), 1000);
        timeoutIds.push(skipId);

        steps.forEach((step, i) => {
            const id = setTimeout(() => {
                setLines(prev => [...prev, step.text]);
                if (i === steps.length - 1) {
                    setCompleted(true);
                    onComplete?.();
                }
            }, step.delay);
            timeoutIds.push(id);
        });

        return () => timeoutIds.forEach(clearTimeout);
    // eslint-disable-next-line react-hooks/exhaustive-deps
    }, []);

    return (
        <div className="w-full max-w-lg mx-auto bg-brand-dark border border-white/10 rounded-sm overflow-hidden shadow-2xl font-mono text-sm relative z-10">
            {/* Header */}
            <div className="bg-brand-gray px-4 py-2 flex items-center gap-2 border-b border-white/10">
                <div className="w-2.5 h-2.5 bg-red-500" />
                <div className="w-2.5 h-2.5 bg-yellow-500" />
                <div className="w-2.5 h-2.5 bg-green-500" />
                <div className="ml-2 text-xs text-white/40">launchad-cli — v1.0.2</div>
                <AnimatePresence>
                    {showSkip && !completed && onSkip && (
                        <motion.button
                            initial={{ opacity: 0 }}
                            animate={{ opacity: 1 }}
                            exit={{ opacity: 0 }}
                            onClick={onSkip}
                            className="ml-auto text-xs text-white/40 hover:text-white flex items-center gap-1 transition-colors"
                        >
                            <SkipForward className="w-3 h-3" /> Skip
                        </motion.button>
                    )}
                </AnimatePresence>
            </div>

            {/* Content */}
            <div className="p-6 h-64 bg-black/50 backdrop-blur-sm flex flex-col gap-2">
                {lines.map((line, i) => (
                    <motion.div
                        key={i}
                        initial={{ opacity: 0, x: -10 }}
                        animate={{ opacity: 1, x: 0 }}
                        transition={{ duration: 0.2, delay: i * 0.05 }}
                        className={line.includes('DONE') ? 'text-brand-lime font-bold' : 'text-gray-300'}
                    >
                        {line}
                    </motion.div>
                ))}
                {!completed && (
                    <motion.div
                        animate={{ opacity: [1, 0] }}
                        transition={{ repeat: Infinity, duration: 0.8 }}
                        className="w-2 h-4 bg-brand-lime inline-block align-middle"
                    />
                )}
            </div>

            {/* Progress bar */}
            <div className="h-0.5 bg-white/5">
                <motion.div
                    className="h-full bg-brand-lime"
                    initial={{ width: 0 }}
                    animate={{ width: `${progress}%` }}
                    transition={{ duration: 0.3 }}
                />
            </div>
        </div>
    );
}
