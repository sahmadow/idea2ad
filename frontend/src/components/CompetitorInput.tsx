/**
 * Competitor Input - allows users to add competitor names/URLs
 */
import { useState } from 'react';
import { Plus, X, Users } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';

interface CompetitorInputProps {
  competitors: string[];
  onCompetitorsChange: (competitors: string[]) => void;
  maxCompetitors?: number;
}

export function CompetitorInput({
  competitors,
  onCompetitorsChange,
  maxCompetitors = 5,
}: CompetitorInputProps) {
  const [inputValue, setInputValue] = useState('');

  const addCompetitor = () => {
    const value = inputValue.trim();
    if (!value) return;
    if (competitors.length >= maxCompetitors) return;
    if (competitors.some(c => c.toLowerCase() === value.toLowerCase())) return;

    onCompetitorsChange([...competitors, value]);
    setInputValue('');
  };

  const removeCompetitor = (index: number) => {
    onCompetitorsChange(competitors.filter((_, i) => i !== index));
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter') {
      e.preventDefault();
      addCompetitor();
    }
  };

  return (
    <div className="space-y-3">
      <div className="flex items-center gap-2 text-xs text-gray-500 font-mono">
        <Users className="w-3.5 h-3.5" />
        <span>Competitor Intel (optional) - add up to {maxCompetitors}</span>
      </div>

      {/* Tag list */}
      <AnimatePresence>
        {competitors.length > 0 && (
          <motion.div
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: 'auto' }}
            exit={{ opacity: 0, height: 0 }}
            className="flex flex-wrap gap-2"
          >
            {competitors.map((comp, i) => (
              <motion.div
                key={comp}
                initial={{ opacity: 0, scale: 0.8 }}
                animate={{ opacity: 1, scale: 1 }}
                exit={{ opacity: 0, scale: 0.8 }}
                className="flex items-center gap-1.5 px-3 py-1.5 bg-brand-gray border border-white/10 text-sm font-mono text-white"
              >
                <span className="truncate max-w-[160px]">{comp}</span>
                <button
                  type="button"
                  onClick={() => removeCompetitor(i)}
                  className="p-0.5 hover:bg-white/10 transition-colors"
                  aria-label={`Remove ${comp}`}
                >
                  <X className="w-3 h-3 text-gray-400" />
                </button>
              </motion.div>
            ))}
          </motion.div>
        )}
      </AnimatePresence>

      {/* Input */}
      {competitors.length < maxCompetitors && (
        <div className="flex gap-2">
          <input
            type="text"
            value={inputValue}
            onChange={(e) => setInputValue(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="Competitor name or URL..."
            aria-label="Add competitor"
            className="flex-1 h-10 bg-brand-gray border border-white/10 px-4 text-white focus:outline-none focus:border-brand-lime font-mono text-sm placeholder:text-gray-600 transition-colors"
          />
          <button
            type="button"
            onClick={addCompetitor}
            disabled={!inputValue.trim()}
            className="h-10 px-3 bg-brand-gray border border-white/10 text-gray-400 hover:text-white hover:border-brand-lime disabled:opacity-50 disabled:hover:text-gray-400 disabled:hover:border-white/10 transition-colors"
            aria-label="Add competitor"
          >
            <Plus className="w-4 h-4" />
          </button>
        </div>
      )}
    </div>
  );
}
