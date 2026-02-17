/**
 * Success View -- post-publish confirmation
 */
import { useEffect, useState } from 'react';
import { CheckCircle, ExternalLink, RotateCcw, Copy, Check, Play, AlertTriangle } from 'lucide-react';
import { motion } from 'framer-motion';
import { toast } from 'sonner';
import confetti from 'canvas-confetti';
import { Button } from './ui/Button';
import { Card } from './ui/Card';
import { ErrorBanner } from './ui/ErrorBanner';
import { activateCampaign, getStoredSessionId } from '../api/facebook';
import type { PublishCampaignResponse } from '../types/facebook';

interface SuccessViewProps {
  result: PublishCampaignResponse;
  onNewCampaign: () => void;
}

function CopyButton({ text, label }: { text: string; label: string }) {
  const handleCopy = async () => {
    await navigator.clipboard.writeText(text);
    toast.success(`${label} copied`);
  };

  return (
    <button
      onClick={handleCopy}
      className="p-1 text-gray-500 hover:text-white transition-colors"
      aria-label={`Copy ${label}`}
    >
      <Copy className="w-3.5 h-3.5" />
    </button>
  );
}

export function SuccessView({ result, onNewCampaign }: SuccessViewProps) {
  const [activating, setActivating] = useState(false);
  const [campaignStatus, setCampaignStatus] = useState<'PAUSED' | 'ACTIVE'>('PAUSED');
  const [activateError, setActivateError] = useState<string | null>(null);

  useEffect(() => {
    confetti({
      particleCount: 100,
      spread: 70,
      origin: { y: 0.6 },
      colors: ['#38BDF8', '#0EA5E9', '#ffffff'],
    });
  }, []);

  const adsManagerUrl = result.ads_manager_url || (
    result.campaign_id
      ? `https://www.facebook.com/adsmanager/manage/campaigns?campaign_ids=${result.campaign_id}`
      : 'https://www.facebook.com/adsmanager'
  );

  const handleActivate = async () => {
    if (!result.campaign_id) return;
    setActivating(true);
    setActivateError(null);

    try {
      const sessionId = getStoredSessionId();
      await activateCampaign(
        { campaign_id: result.campaign_id },
        sessionId || undefined
      );
      setCampaignStatus('ACTIVE');
      toast.success('Campaign activated!');
    } catch (err) {
      setActivateError(err instanceof Error ? err.message : 'Failed to activate');
    } finally {
      setActivating(false);
    }
  };

  const ids = [
    { label: 'Campaign ID', value: result.campaign_id },
    { label: 'Ad Set ID', value: result.ad_set_id },
    ...(result.ad_ids && result.ad_ids.length > 1
      ? result.ad_ids.map((id, i) => ({ label: `Ad ${i + 1} ID`, value: id }))
      : [{ label: 'Ad ID', value: result.ad_id }]
    ),
  ].filter(item => item.value);

  const hasPartialFailure = result.ads_failed && result.ads_failed > 0;

  return (
    <div className="min-h-screen bg-brand-dark text-white flex items-center justify-center py-12">
      <div className="max-w-lg w-full mx-auto px-6">
        <Card className="border-status-success/30 animate-pulse-glow">
          <div className="p-8 text-center">
            {/* Animated check */}
            <motion.div
              initial={{ scale: 0, opacity: 0 }}
              animate={{ scale: 1, opacity: 1 }}
              transition={{ type: 'spring', stiffness: 200, damping: 15, delay: 0.2 }}
              className="w-20 h-20 mx-auto mb-6 bg-status-success/20 flex items-center justify-center"
            >
              <CheckCircle className="w-12 h-12 text-status-success" />
            </motion.div>

            <h1 className="text-3xl font-display font-bold mb-2">Campaign Published!</h1>
            <p className="text-gray-400 mb-4">
              {result.ads_created && result.ads_created > 1
                ? `${result.ads_created} ads created and ready to review in Meta Ads Manager.`
                : 'Your campaign has been created and is ready to review in Meta Ads Manager.'
              }
            </p>

            {/* Partial failure warning */}
            {hasPartialFailure && (
              <div className="flex items-start gap-2 p-3 bg-status-warning/10 border border-status-warning/30 mb-6 text-left">
                <AlertTriangle className="w-4 h-4 text-status-warning shrink-0 mt-0.5" />
                <div className="text-sm text-status-warning">
                  {result.ads_failed} ad(s) failed to create. {result.ads_created} ad(s) were published successfully.
                </div>
              </div>
            )}

            {/* Campaign IDs */}
            <div className="space-y-3 mb-8 text-left">
              {ids.map(({ label, value }) => (
                <div key={label} className="flex items-center justify-between p-3 bg-brand-gray border border-white/10">
                  <span className="text-sm text-gray-400">{label}</span>
                  <div className="flex items-center gap-2">
                    <span className="font-mono text-sm text-white truncate max-w-[180px]">{value}</span>
                    <CopyButton text={value!} label={label} />
                  </div>
                </div>
              ))}
            </div>

            {/* Campaign Status */}
            {campaignStatus === 'PAUSED' ? (
              <div className="p-4 bg-status-warning/10 border border-status-warning/30 mb-8 text-left">
                <p className="text-sm text-status-warning mb-3">
                  Your campaign was created in <span className="font-bold">PAUSED</span> status.
                  You can activate it below or review it in Ads Manager first.
                </p>
                <Button
                  variant="primary"
                  onClick={handleActivate}
                  loading={activating}
                  className="w-full"
                >
                  <Play className="w-4 h-4 mr-2" />
                  Activate Campaign
                </Button>
                {activateError && (
                  <ErrorBanner message={activateError} className="mt-3" onDismiss={() => setActivateError(null)} />
                )}
              </div>
            ) : (
              <div className="p-4 bg-status-success/10 border border-status-success/30 mb-8 text-left">
                <div className="flex items-center gap-2">
                  <CheckCircle className="w-4 h-4 text-status-success" />
                  <p className="text-sm text-status-success font-bold">Campaign is ACTIVE</p>
                </div>
                <p className="text-sm text-gray-400 mt-1">
                  Your ads are now live and will start delivering to your audience.
                </p>
              </div>
            )}

            {/* Next Steps */}
            <div className="text-left mb-8">
              <h3 className="text-sm font-mono font-bold text-gray-400 uppercase tracking-wide mb-3">Next Steps</h3>
              <ul className="space-y-2">
                {[
                  'Review ad creative in Ads Manager',
                  'Set your target audience refinements',
                  ...(campaignStatus === 'PAUSED' ? ['Activate the campaign when ready'] : ['Monitor campaign performance']),
                ].map((step, i) => (
                  <li key={i} className="flex items-center gap-2 text-sm text-gray-300">
                    <Check className="w-4 h-4 text-brand-lime shrink-0" />
                    {step}
                  </li>
                ))}
              </ul>
            </div>

            {/* Actions */}
            <div className="space-y-3">
              <a href={adsManagerUrl} target="_blank" rel="noopener noreferrer" className="block">
                <Button variant="primary" className="w-full">
                  Open Meta Ads Manager
                  <ExternalLink className="w-4 h-4 ml-2" />
                </Button>
              </a>
              <Button variant="outline" onClick={onNewCampaign} className="w-full">
                <RotateCcw className="w-4 h-4 mr-2" />
                Create New Campaign
              </Button>
            </div>
          </div>
        </Card>
      </div>
    </div>
  );
}
