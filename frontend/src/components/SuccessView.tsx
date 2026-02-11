/**
 * Success View -- post-publish confirmation
 */
import { useEffect } from 'react';
import { CheckCircle, ExternalLink, RotateCcw, Copy, Check } from 'lucide-react';
import { motion } from 'framer-motion';
import { toast } from 'sonner';
import confetti from 'canvas-confetti';
import { Button } from './ui/Button';
import { Card } from './ui/Card';
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
  useEffect(() => {
    // Fire confetti
    confetti({
      particleCount: 100,
      spread: 70,
      origin: { y: 0.6 },
      colors: ['#38BDF8', '#0EA5E9', '#ffffff'],
    });
  }, []);

  const getAdsManagerUrl = () => {
    if (result.campaign_id) {
      return `https://www.facebook.com/adsmanager/manage/campaigns?campaign_ids=${result.campaign_id}`;
    }
    return 'https://www.facebook.com/adsmanager';
  };

  const ids = [
    { label: 'Campaign ID', value: result.campaign_id },
    { label: 'Ad Set ID', value: result.ad_set_id },
    { label: 'Ad ID', value: result.ad_id },
  ].filter(item => item.value);

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
            <p className="text-gray-400 mb-8">
              Your campaign has been created and is ready to review in Meta Ads Manager.
            </p>

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

            {/* Status Note */}
            <div className="p-4 bg-status-warning/10 border border-status-warning/30 mb-8 text-left">
              <p className="text-sm text-status-warning">
                Your campaign was created in <span className="font-bold">PAUSED</span> status.
                Visit Meta Ads Manager to review and activate it.
              </p>
            </div>

            {/* Next Steps */}
            <div className="text-left mb-8">
              <h3 className="text-sm font-mono font-bold text-gray-400 uppercase tracking-wide mb-3">Next Steps</h3>
              <ul className="space-y-2">
                {[
                  'Review ad creative in Ads Manager',
                  'Set your target audience refinements',
                  'Activate the campaign when ready',
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
              <a href={getAdsManagerUrl()} target="_blank" rel="noopener noreferrer" className="block">
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
