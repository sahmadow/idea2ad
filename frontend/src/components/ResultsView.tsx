import { ArrowLeft, ArrowRight, Download, Target, Palette, Sparkles } from 'lucide-react';
import { Button } from './ui/Button';
import { Card } from './ui/Card';
import { MetaAdPreview } from './ui/MetaAdPreview';
import type { CampaignDraft, Ad } from '../api';

interface ResultsViewProps {
  result: CampaignDraft;
  selectedAd: Ad | null;
  onSelectAd: (ad: Ad) => void;
  onBack: () => void;
  onNext?: () => void;
}

export function ResultsView({ result, selectedAd, onSelectAd, onBack, onNext }: ResultsViewProps) {
  const pageName = new URL(result.project_url).hostname.replace('www.', '');

  const handleExportJson = () => {
    const dataStr = JSON.stringify(result, null, 2);
    const dataBlob = new Blob([dataStr], { type: 'application/json' });
    const url = URL.createObjectURL(dataBlob);
    const link = document.createElement('a');
    link.href = url;
    link.download = `launchad-campaign-${new Date().toISOString().split('T')[0]}.json`;
    link.click();
    URL.revokeObjectURL(url);
  };

  return (
    <div className="min-h-screen bg-brand-dark text-white py-12">
      <div className="max-w-7xl mx-auto px-6">
        {/* Header */}
        <div className="flex items-center justify-between mb-12">
          <button
            onClick={onBack}
            className="flex items-center gap-2 text-gray-400 hover:text-white transition-colors"
          >
            <ArrowLeft className="w-5 h-5" />
            <span className="font-mono text-sm">Try Another URL</span>
          </button>
          <div className="flex items-center gap-3">
            <Button variant="outline" onClick={handleExportJson}>
              <Download className="w-4 h-4 mr-2" />
              Export JSON
            </Button>
            {onNext && (
              <Button
                variant="primary"
                onClick={onNext}
                disabled={!selectedAd}
              >
                Next: Publish
                <ArrowRight className="w-4 h-4 ml-2" />
              </Button>
            )}
          </div>
        </div>

        {/* Title */}
        <div className="text-center mb-12">
          <div className="inline-flex items-center gap-2 px-3 py-1 bg-brand-gray border border-white/10 text-xs font-mono text-brand-lime uppercase tracking-wider mb-4">
            <Sparkles className="w-3 h-3" />
            Campaign Generated
          </div>
          <h1 className="text-4xl font-display font-bold mb-2">Your Ad Campaign</h1>
          <p className="text-gray-400">
            Based on <span className="text-brand-lime font-mono">{result.project_url}</span>
          </p>
        </div>

        {/* Analysis Summary Cards */}
        <div className="grid md:grid-cols-3 gap-6 mb-16">
          {/* Summary Card */}
          <Card>
            <div className="p-6">
              <div className="flex items-center gap-3 mb-4">
                <div className="w-10 h-10 bg-brand-gray border border-white/10 flex items-center justify-center text-brand-lime">
                  <Sparkles className="w-5 h-5" />
                </div>
                <h3 className="text-lg font-bold font-display">Summary</h3>
              </div>
              <p className="text-gray-400 text-sm leading-relaxed mb-4">{result.analysis.summary}</p>
              <div className="pt-4 border-t border-white/10">
                <div className="text-xs text-gray-500 uppercase tracking-wide mb-1">USP</div>
                <p className="text-brand-lime text-sm font-medium">{result.analysis.unique_selling_proposition}</p>
              </div>
            </div>
          </Card>

          {/* Targeting Card */}
          <Card>
            <div className="p-6">
              <div className="flex items-center gap-3 mb-4">
                <div className="w-10 h-10 bg-brand-gray border border-white/10 flex items-center justify-center text-brand-lime">
                  <Target className="w-5 h-5" />
                </div>
                <h3 className="text-lg font-bold font-display">Targeting</h3>
              </div>
              <div className="space-y-3 text-sm">
                <div>
                  <span className="text-gray-500">Age:</span>{' '}
                  <span className="text-white">{result.targeting.age_min} - {result.targeting.age_max}</span>
                </div>
                <div>
                  <span className="text-gray-500">Locations:</span>{' '}
                  <span className="text-white">{result.targeting.geo_locations.join(', ')}</span>
                </div>
                <div>
                  <span className="text-gray-500">Interests:</span>
                  <div className="flex flex-wrap gap-1 mt-1">
                    {result.targeting.interests.slice(0, 5).map((interest, i) => (
                      <span key={i} className="px-2 py-0.5 bg-brand-gray border border-white/10 text-xs text-gray-300 rounded">
                        {interest}
                      </span>
                    ))}
                  </div>
                </div>
              </div>
            </div>
          </Card>

          {/* Styling Card */}
          <Card>
            <div className="p-6">
              <div className="flex items-center gap-3 mb-4">
                <div className="w-10 h-10 bg-brand-gray border border-white/10 flex items-center justify-center text-brand-lime">
                  <Palette className="w-5 h-5" />
                </div>
                <h3 className="text-lg font-bold font-display">Brand Style</h3>
              </div>
              <div className="space-y-4">
                <div>
                  <div className="text-xs text-gray-500 uppercase tracking-wide mb-2">Colors</div>
                  <div className="flex gap-2">
                    {result.analysis.styling_guide.primary_colors.slice(0, 4).map((color, i) => (
                      <div
                        key={i}
                        className="w-8 h-8 rounded border border-white/20"
                        style={{ backgroundColor: color }}
                        title={color}
                      />
                    ))}
                  </div>
                </div>
                <div className="flex gap-4">
                  <div>
                    <div className="text-xs text-gray-500 uppercase tracking-wide mb-1">Style</div>
                    <span className="text-white text-sm capitalize">{result.analysis.styling_guide.design_style}</span>
                  </div>
                  <div>
                    <div className="text-xs text-gray-500 uppercase tracking-wide mb-1">Mood</div>
                    <span className="text-white text-sm capitalize">{result.analysis.styling_guide.mood}</span>
                  </div>
                </div>
              </div>
            </div>
          </Card>
        </div>

        {/* Ad Previews */}
        <div className="mb-12">
          <h2 className="text-2xl font-display font-bold text-center mb-2">Generated Ads</h2>
          <p className="text-gray-400 text-center mb-8">Click an ad to select it for launch</p>

          <div className="flex flex-wrap justify-center gap-8">
            {result.ads?.map((ad) => (
              <MetaAdPreview
                key={ad.id}
                ad={ad}
                pageName={pageName}
                websiteUrl={result.project_url}
                selected={selectedAd?.id === ad.id}
                onSelect={() => onSelectAd(ad)}
              />
            ))}
          </div>
        </div>

        {/* Pain Points */}
        <div className="max-w-2xl mx-auto">
          <h3 className="text-lg font-display font-bold text-center mb-4">Identified Pain Points</h3>
          <div className="space-y-2">
            {result.analysis.pain_points.map((point, i) => (
              <div key={i} className="flex items-start gap-3 p-3 bg-brand-gray/50 border border-white/5 rounded">
                <span className="text-brand-lime font-mono text-sm">{i + 1}.</span>
                <span className="text-gray-300 text-sm">{point}</span>
              </div>
            ))}
          </div>
        </div>

        {/* Bottom Action Bar */}
        <div className="mt-16 pt-8 border-t border-white/10">
          <div className="flex flex-col sm:flex-row items-center justify-center gap-4">
            <Button variant="outline" onClick={handleExportJson}>
              <Download className="w-4 h-4 mr-2" />
              Export JSON
            </Button>
            {onNext && (
              <Button
                variant="primary"
                onClick={onNext}
                disabled={!selectedAd}
                className="min-w-[180px]"
              >
                {selectedAd ? 'Publish to Meta' : 'Select an Ad First'}
                <ArrowRight className="w-4 h-4 ml-2" />
              </Button>
            )}
          </div>
          {!selectedAd && (
            <p className="text-center text-gray-500 text-sm mt-3">
              Click on an ad above to select it for publishing
            </p>
          )}
        </div>
      </div>
    </div>
  );
}
