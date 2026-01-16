import { useEffect, useState } from 'react';
import { motion } from 'framer-motion';

export function Terminal() {
    const [lines, setLines] = useState<string[]>([]);

    const steps = [
        { text: '> Analyzing landing page...', delay: 500 },
        { text: '> Extracting brand colors: #1A1A1A, #D4FF31', delay: 1500 },
        { text: '> Identifying USP: "AI-Powered Ad Campaigns"', delay: 2500 },
        { text: '> Generating copy variations...', delay: 3500 },
        { text: '> DONE. Campaign ready for launch.', delay: 4500 },
    ];

    useEffect(() => {
        let timeoutIds: ReturnType<typeof setTimeout>[] = [];

        steps.forEach((step) => {
            const id = setTimeout(() => {
                setLines(prev => [...prev, step.text]);
            }, step.delay);
            timeoutIds.push(id);
        });

        return () => timeoutIds.forEach(clearTimeout);
    }, []);

    return (
        <div className="w-full max-w-lg mx-auto bg-brand-dark border border-brand-gray rounded-lg overflow-hidden shadow-2xl font-mono text-sm relative z-10">
            {/* Terminal Header */}
            <div className="bg-brand-gray px-4 py-2 flex items-center gap-2 border-b border-white/10">
                <div className="w-3 h-3 rounded-full bg-red-500" />
                <div className="w-3 h-3 rounded-full bg-yellow-500" />
                <div className="w-3 h-3 rounded-full bg-green-500" />
                <div className="ml-2 text-xs text-white/40">launchad-cli — v1.0.2</div>
            </div>

            {/* Terminal Content */}
            <div className="p-6 h-64 bg-black/50 backdrop-blur-sm flex flex-col gap-2">
                {lines.map((line, i) => (
                    <motion.div
                        key={i}
                        initial={{ opacity: 0, x: -10 }}
                        animate={{ opacity: 1, x: 0 }}
                        className={line.includes('DONE') ? 'text-brand-lime font-bold' : 'text-gray-300'}
                    >
                        {line}
                    </motion.div>
                ))}
                <motion.div
                    animate={{ opacity: [1, 0] }}
                    transition={{ repeat: Infinity, duration: 0.8 }}
                    className="w-2 h-4 bg-brand-lime inline-block align-middle"
                />
            </div>
        </div>
    );
}
