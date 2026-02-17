/**
 * Competitor Insights - displays competitor intelligence results
 */
import { useState } from 'react';
import { ChevronDown, TrendingUp, Target, Zap, Users, BarChart3, Lightbulb } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';
import { Card } from './ui/Card';
import type { CompetitorIntelligence, GapRecommendation } from '../api';

interface CompetitorInsightsProps {
  data: CompetitorIntelligence;
}

function DistributionBar({ label, value }: { label: string; value: number }) {
  return (
    <div className="flex items-center gap-3">
      <span className="text-xs text-gray-400 font-mono w-28 truncate" title={label}>
        {label}
      </span>
      <div className="flex-1 h-2 bg-white/5">
        <div
          className="h-full bg-brand-lime transition-all"
          style={{ width: `${Math.min(value, 100)}%` }}
        />
      </div>
      <span className="text-xs text-gray-400 font-mono w-12 text-right">{value}%</span>
    </div>
  );
}

function RecommendationCard({ rec }: { rec: GapRecommendation }) {
  const priorityColor =
    rec.priority === 'high'
      ? 'text-status-success border-status-success/30 bg-status-success/5'
      : rec.priority === 'medium'
        ? 'text-brand-lime border-brand-lime/30 bg-brand-lime/5'
        : 'text-gray-400 border-white/10 bg-white/5';

  const typeIcon =
    rec.type === 'hook' || rec.type === 'angle' ? (
      <Target className="w-3.5 h-3.5" />
    ) : rec.type === 'combo' ? (
      <Zap className="w-3.5 h-3.5" />
    ) : rec.type === 'copy_direction' ? (
      <Lightbulb className="w-3.5 h-3.5" />
    ) : (
      <TrendingUp className="w-3.5 h-3.5" />
    );

  return (
    <div className={`p-3 border ${priorityColor}`}>
      <div className="flex items-start gap-2">
        <span className="mt-0.5 shrink-0">{typeIcon}</span>
        <div className="min-w-0">
          <p className="text-sm text-white font-medium">{rec.action}</p>
          {rec.rationale && (
            <p className="text-xs text-gray-400 mt-1">{rec.rationale}</p>
          )}
          {rec.sample && (
            <p className="text-xs text-brand-lime font-mono mt-1.5 italic">
              &ldquo;{rec.sample}&rdquo;
            </p>
          )}
        </div>
        <span className="shrink-0 text-[10px] font-mono uppercase tracking-wide px-1.5 py-0.5 border border-current opacity-70">
          {rec.priority}
        </span>
      </div>
    </div>
  );
}

export function CompetitorInsights({ data }: CompetitorInsightsProps) {
  const [expandedSection, setExpandedSection] = useState<string | null>('recommendations');

  const toggleSection = (section: string) => {
    setExpandedSection(expandedSection === section ? null : section);
  };

  const hasData = data.total_ads_analyzed > 0;

  return (
    <div className="space-y-6">
      {/* Header Stats */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
        {[
          { label: 'Competitors', value: data.competitors.length, icon: Users },
          { label: 'Ads Analyzed', value: data.total_ads_analyzed, icon: BarChart3 },
          { label: 'Profitable Ads', value: data.profitable_ads_count, icon: TrendingUp },
          { label: 'Confidence', value: `${data.confidence_score}/10`, icon: Target },
        ].map(({ label, value, icon: Icon }) => (
          <Card key={label}>
            <div className="p-4 text-center">
              <Icon className="w-4 h-4 text-brand-lime mx-auto mb-2" />
              <div className="text-xl font-bold text-white font-display">{value}</div>
              <div className="text-xs text-gray-500 font-mono">{label}</div>
            </div>
          </Card>
        ))}
      </div>

      {/* Competitor Profiles */}
      {data.competitors.length > 0 && (
        <CollapsibleSection
          title={`Competitor Profiles (${data.competitors.length})`}
          isOpen={expandedSection === 'profiles'}
          onToggle={() => toggleSection('profiles')}
        >
          <div className="space-y-3">
            {data.competitors.map((comp, i) => (
              <div
                key={i}
                className="p-3 bg-brand-dark border border-white/5"
              >
                <div className="flex items-center justify-between mb-2">
                  <span className="text-sm font-bold text-white">{comp.name}</span>
                  <span className="text-xs font-mono text-gray-500">
                    {comp.ad_count} ads
                  </span>
                </div>
                {comp.positioning && (
                  <p className="text-xs text-gray-400 mb-2">{comp.positioning}</p>
                )}
                {comp.claims.length > 0 && (
                  <div className="flex flex-wrap gap-1">
                    {comp.claims.slice(0, 3).map((claim, j) => (
                      <span
                        key={j}
                        className="px-2 py-0.5 bg-white/5 border border-white/10 text-[11px] text-gray-300 truncate max-w-[200px]"
                      >
                        {claim}
                      </span>
                    ))}
                  </div>
                )}
                {comp.error && (
                  <p className="text-xs text-status-warning mt-1">{comp.error}</p>
                )}
              </div>
            ))}
          </div>
        </CollapsibleSection>
      )}

      {/* Pattern Distribution */}
      {hasData && (
        <CollapsibleSection
          title="Ad Pattern Distribution"
          isOpen={expandedSection === 'patterns'}
          onToggle={() => toggleSection('patterns')}
        >
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div>
              <h4 className="text-xs font-mono text-gray-500 uppercase tracking-wide mb-3">
                Hook Types
              </h4>
              <div className="space-y-2">
                {Object.entries(data.hook_distribution)
                  .slice(0, 6)
                  .map(([label, value]) => (
                    <DistributionBar key={label} label={label} value={value} />
                  ))}
              </div>
            </div>
            <div>
              <h4 className="text-xs font-mono text-gray-500 uppercase tracking-wide mb-3">
                Emotional Angles
              </h4>
              <div className="space-y-2">
                {Object.entries(data.angle_distribution)
                  .slice(0, 6)
                  .map(([label, value]) => (
                    <DistributionBar key={label} label={label} value={value} />
                  ))}
              </div>
            </div>
            <div>
              <h4 className="text-xs font-mono text-gray-500 uppercase tracking-wide mb-3">
                CTA Styles
              </h4>
              <div className="space-y-2">
                {Object.entries(data.cta_distribution)
                  .slice(0, 6)
                  .map(([label, value]) => (
                    <DistributionBar key={label} label={label} value={value} />
                  ))}
              </div>
            </div>
            <div>
              <h4 className="text-xs font-mono text-gray-500 uppercase tracking-wide mb-3">
                Ad Formats
              </h4>
              <div className="space-y-2">
                {Object.entries(data.format_distribution)
                  .slice(0, 6)
                  .map(([label, value]) => (
                    <DistributionBar key={label} label={label} value={value} />
                  ))}
              </div>
            </div>
          </div>
        </CollapsibleSection>
      )}

      {/* Recommendations */}
      {data.recommendations.length > 0 && (
        <CollapsibleSection
          title={`Recommendations (${data.recommendations.length})`}
          isOpen={expandedSection === 'recommendations'}
          onToggle={() => toggleSection('recommendations')}
        >
          <div className="space-y-2">
            {data.recommendations.map((rec, i) => (
              <RecommendationCard key={i} rec={rec} />
            ))}
          </div>
        </CollapsibleSection>
      )}

      {/* No data state */}
      {!hasData && data.competitors.length > 0 && (
        <div className="text-center py-8 text-gray-500">
          <BarChart3 className="w-8 h-8 mx-auto mb-3 opacity-50" />
          <p className="text-sm font-mono">
            No ads found for these competitors.
            <br />
            Try different competitor names or URLs.
          </p>
        </div>
      )}
    </div>
  );
}

function CollapsibleSection({
  title,
  isOpen,
  onToggle,
  children,
}: {
  title: string;
  isOpen: boolean;
  onToggle: () => void;
  children: React.ReactNode;
}) {
  return (
    <div>
      <button
        onClick={onToggle}
        className="w-full flex items-center justify-between p-4 bg-brand-gray/50 border border-white/5 text-left hover:border-white/10 transition-colors"
      >
        <h3 className="text-sm font-mono font-bold uppercase tracking-wide text-gray-400">
          {title}
        </h3>
        <ChevronDown
          className={`w-4 h-4 text-gray-400 transition-transform ${isOpen ? 'rotate-180' : ''}`}
        />
      </button>
      <AnimatePresence>
        {isOpen && (
          <motion.div
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: 'auto' }}
            exit={{ opacity: 0, height: 0 }}
            className="border border-t-0 border-white/5 overflow-hidden"
          >
            <div className="p-4">{children}</div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}
