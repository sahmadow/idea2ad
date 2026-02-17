import { useEffect } from 'react';
import { ArrowLeft, Globe, Target, Palette, DollarSign, Calendar, Loader2 } from 'lucide-react';
import { motion } from 'framer-motion';
import { Navbar } from './layout/Navbar';
import { Button } from './ui/Button';
import { Card, CardHeader, CardContent } from './ui/Card';
import { StatusBadge } from './ui/StatusBadge';
import { ErrorBanner } from './ui/ErrorBanner';
import type { CampaignDetail, CampaignStatus } from '../types/campaign';

interface CampaignDetailViewProps {
  campaign: CampaignDetail | null;
  isLoading: boolean;
  error: string | null;
  campaignId: string;
  userName: string | null;
  onFetchCampaign: (id: string) => Promise<void>;
  onBack: () => void;
  onLogoClick: () => void;
  onDashboardClick: () => void;
  onLogout: () => Promise<void>;
  onDismissError: () => void;
}

function formatDate(dateStr: string): string {
  return new Date(dateStr).toLocaleDateString('en-US', {
    month: 'long',
    day: 'numeric',
    year: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  });
}

export function CampaignDetailView({
  campaign,
  isLoading,
  error,
  campaignId,
  userName,
  onFetchCampaign,
  onBack,
  onLogoClick,
  onDashboardClick,
  onLogout,
  onDismissError,
}: CampaignDetailViewProps) {
  useEffect(() => {
    onFetchCampaign(campaignId);
  }, [campaignId, onFetchCampaign]);

  const analysis = campaign?.analysis as Record<string, unknown> | null;
  const stylingGuide = analysis?.styling_guide as Record<string, unknown> | null;
  const buyerPersona = analysis?.buyer_persona as Record<string, unknown> | null;
  const painPoints = analysis?.pain_points as string[] | null;
  const keywords = analysis?.keywords as string[] | null;
  const primaryColors = stylingGuide?.primary_colors as string[] | null;

  return (
    <div className="min-h-screen bg-brand-dark text-white">
      <Navbar
        onLogoClick={onLogoClick}
        userName={userName}
        onDashboardClick={onDashboardClick}
        onLogout={onLogout}
      />

      <div className="max-w-5xl mx-auto px-6 pt-24 pb-16">
        {/* Back button */}
        <button
          onClick={onBack}
          className="flex items-center gap-2 text-sm text-gray-400 hover:text-brand-lime transition-colors font-mono mb-6"
        >
          <ArrowLeft className="w-4 h-4" />
          Back to Dashboard
        </button>

        {/* Error */}
        {error && (
          <ErrorBanner message={error} onDismiss={onDismissError} className="mb-6" />
        )}

        {/* Loading */}
        {isLoading && !campaign && (
          <div className="flex items-center justify-center py-20">
            <Loader2 className="w-8 h-8 text-brand-lime animate-spin" />
          </div>
        )}

        {campaign && (
          <motion.div
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            className="space-y-6"
          >
            {/* Campaign header */}
            <div className="flex flex-col sm:flex-row sm:items-start justify-between gap-4">
              <div>
                <div className="flex items-center gap-3 mb-2">
                  <h1 className="text-3xl font-display font-bold">{campaign.name}</h1>
                  <StatusBadge status={campaign.status as CampaignStatus} />
                </div>
                {campaign.project_url && (
                  <a
                    href={campaign.project_url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="flex items-center gap-1.5 text-sm font-mono text-gray-400 hover:text-brand-lime transition-colors"
                  >
                    <Globe className="w-3.5 h-3.5" />
                    {campaign.project_url}
                  </a>
                )}
              </div>
            </div>

            {/* Meta row */}
            <div className="flex flex-wrap items-center gap-4 text-sm text-gray-400 font-mono">
              <span className="flex items-center gap-1.5">
                <Calendar className="w-4 h-4" />
                Created {formatDate(campaign.created_at)}
              </span>
              <span className="flex items-center gap-1.5">
                <DollarSign className="w-4 h-4" />
                ${campaign.budget_daily}/day
              </span>
              <span className="flex items-center gap-1.5">
                <Target className="w-4 h-4" />
                {campaign.objective}
              </span>
            </div>

            {/* Published IDs */}
            {campaign.meta_campaign_id && (
              <Card variant="highlighted">
                <div className="p-4">
                  <h3 className="text-sm font-mono text-brand-lime uppercase tracking-wider mb-2">Published to Meta</h3>
                  <div className="grid sm:grid-cols-2 gap-2 text-xs font-mono text-gray-400">
                    <div>Campaign ID: <span className="text-white">{campaign.meta_campaign_id}</span></div>
                    {campaign.meta_adset_id && (
                      <div>Ad Set ID: <span className="text-white">{campaign.meta_adset_id}</span></div>
                    )}
                    {campaign.meta_ad_id && (
                      <div>Ad ID: <span className="text-white">{campaign.meta_ad_id}</span></div>
                    )}
                  </div>
                  <a
                    href={`https://www.facebook.com/adsmanager/manage/campaigns?act=${campaign.meta_campaign_id}`}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="inline-block mt-3"
                  >
                    <Button variant="outline" size="sm">
                      Open in Ads Manager
                    </Button>
                  </a>
                </div>
              </Card>
            )}

            {/* Analysis section */}
            {analysis && (
              <div className="grid md:grid-cols-2 gap-6">
                {/* Summary card */}
                <Card>
                  <CardHeader>
                    <h3 className="text-lg font-display font-bold flex items-center gap-2">
                      <Target className="w-5 h-5 text-brand-lime" />
                      Analysis
                    </h3>
                  </CardHeader>
                  <CardContent className="space-y-4">
                    {!!analysis.summary && (
                      <div>
                        <p className="text-xs font-mono text-gray-500 uppercase tracking-wider mb-1">Summary</p>
                        <p className="text-sm text-gray-300 leading-relaxed">{String(analysis.summary)}</p>
                      </div>
                    )}
                    {!!analysis.unique_selling_proposition && (
                      <div>
                        <p className="text-xs font-mono text-gray-500 uppercase tracking-wider mb-1">USP</p>
                        <p className="text-sm text-brand-lime">{String(analysis.unique_selling_proposition)}</p>
                      </div>
                    )}
                    {!!analysis.call_to_action && (
                      <div>
                        <p className="text-xs font-mono text-gray-500 uppercase tracking-wider mb-1">CTA</p>
                        <p className="text-sm text-white font-medium">{String(analysis.call_to_action)}</p>
                      </div>
                    )}
                  </CardContent>
                </Card>

                {/* Style card */}
                <Card>
                  <CardHeader>
                    <h3 className="text-lg font-display font-bold flex items-center gap-2">
                      <Palette className="w-5 h-5 text-brand-lime" />
                      Brand Style
                    </h3>
                  </CardHeader>
                  <CardContent className="space-y-4">
                    {primaryColors && primaryColors.length > 0 && (
                      <div>
                        <p className="text-xs font-mono text-gray-500 uppercase tracking-wider mb-2">Colors</p>
                        <div className="flex gap-2">
                          {primaryColors.map((color, i) => (
                            <div
                              key={i}
                              className="w-8 h-8 border border-white/10"
                              style={{ backgroundColor: color }}
                              title={color}
                            />
                          ))}
                        </div>
                      </div>
                    )}
                    {!!stylingGuide?.design_style && (
                      <div>
                        <p className="text-xs font-mono text-gray-500 uppercase tracking-wider mb-1">Design Style</p>
                        <p className="text-sm text-gray-300">{String(stylingGuide.design_style)}</p>
                      </div>
                    )}
                    {!!stylingGuide?.mood && (
                      <div>
                        <p className="text-xs font-mono text-gray-500 uppercase tracking-wider mb-1">Mood</p>
                        <p className="text-sm text-gray-300">{String(stylingGuide.mood)}</p>
                      </div>
                    )}
                  </CardContent>
                </Card>

                {/* Pain points */}
                {painPoints && painPoints.length > 0 && (
                  <Card>
                    <CardHeader>
                      <h3 className="text-lg font-display font-bold">Pain Points</h3>
                    </CardHeader>
                    <CardContent>
                      <ul className="space-y-2">
                        {painPoints.map((point, i) => (
                          <li key={i} className="text-sm text-gray-300 flex items-start gap-2">
                            <span className="w-1.5 h-1.5 bg-brand-lime mt-1.5 shrink-0" />
                            {point}
                          </li>
                        ))}
                      </ul>
                    </CardContent>
                  </Card>
                )}

                {/* Buyer persona */}
                {buyerPersona && Object.keys(buyerPersona).length > 0 && (
                  <Card>
                    <CardHeader>
                      <h3 className="text-lg font-display font-bold">Buyer Persona</h3>
                    </CardHeader>
                    <CardContent>
                      <dl className="space-y-2">
                        {Object.entries(buyerPersona).map(([key, value]) => (
                          <div key={key}>
                            <dt className="text-xs font-mono text-gray-500 uppercase tracking-wider">{key.replace(/_/g, ' ')}</dt>
                            <dd className="text-sm text-gray-300">{String(value)}</dd>
                          </div>
                        ))}
                      </dl>
                    </CardContent>
                  </Card>
                )}

                {/* Keywords */}
                {keywords && keywords.length > 0 && (
                  <Card className="md:col-span-2">
                    <CardHeader>
                      <h3 className="text-lg font-display font-bold">Keywords</h3>
                    </CardHeader>
                    <CardContent>
                      <div className="flex flex-wrap gap-2">
                        {keywords.map((keyword, i) => (
                          <span
                            key={i}
                            className="px-2 py-1 text-xs font-mono text-gray-300 bg-brand-gray border border-white/10"
                          >
                            {keyword}
                          </span>
                        ))}
                      </div>
                    </CardContent>
                  </Card>
                )}
              </div>
            )}

            {/* Creatives section */}
            {campaign.creatives.length > 0 && (
              <div>
                <h3 className="text-lg font-display font-bold mb-4">Creatives ({campaign.creatives.length})</h3>
                <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-4">
                  {campaign.creatives.map((creative, i) => {
                    const c = creative as Record<string, unknown>;
                    return (
                      <Card key={i}>
                        <div className="p-4">
                          {!!c.type && (
                            <span className="text-xs font-mono text-brand-lime uppercase tracking-wider">
                              {String(c.type)}
                            </span>
                          )}
                          {!!c.content && (
                            <p className="text-sm text-gray-300 mt-2 line-clamp-4">
                              {String(c.content)}
                            </p>
                          )}
                          {!!c.rationale && (
                            <p className="text-xs text-gray-500 mt-2 italic">
                              {String(c.rationale)}
                            </p>
                          )}
                        </div>
                      </Card>
                    );
                  })}
                </div>
              </div>
            )}

            {/* Image briefs section */}
            {campaign.image_briefs.length > 0 && (
              <div>
                <h3 className="text-lg font-display font-bold mb-4">Image Briefs ({campaign.image_briefs.length})</h3>
                <div className="grid sm:grid-cols-2 gap-4">
                  {campaign.image_briefs.map((brief, i) => {
                    const b = brief as Record<string, unknown>;
                    return (
                      <Card key={i}>
                        <div className="p-4 space-y-3">
                          {!!b.approach && (
                            <span className="text-xs font-mono text-brand-lime uppercase tracking-wider">
                              {String(b.approach)}
                            </span>
                          )}
                          {!!b.image_url && (
                            <img
                              src={String(b.image_url)}
                              alt={String(b.approach || 'Ad image')}
                              className="w-full aspect-square object-cover border border-white/10"
                            />
                          )}
                          {!!b.visual_description && (
                            <p className="text-sm text-gray-300">{String(b.visual_description)}</p>
                          )}
                          {!!b.rationale && (
                            <p className="text-xs text-gray-500 italic">{String(b.rationale)}</p>
                          )}
                        </div>
                      </Card>
                    );
                  })}
                </div>
              </div>
            )}
          </motion.div>
        )}
      </div>
    </div>
  );
}
