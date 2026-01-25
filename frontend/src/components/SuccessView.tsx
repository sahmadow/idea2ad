/**
 * Success View
 * Displayed after successfully publishing a campaign to Meta
 */
import { CheckCircle, ExternalLink, RotateCcw } from 'lucide-react';
import { Button } from './ui/Button';
import { Card } from './ui/Card';
import type { PublishCampaignResponse } from '../types/facebook';

interface SuccessViewProps {
  result: PublishCampaignResponse;
  onNewCampaign: () => void;
}

export function SuccessView({ result, onNewCampaign }: SuccessViewProps) {
  // Extract ad account ID from result for Ads Manager link
  // The campaign_id typically comes back as just the numeric ID
  const getAdsManagerUrl = () => {
    if (result.campaign_id) {
      return `https://www.facebook.com/adsmanager/manage/campaigns?campaign_ids=${result.campaign_id}`;
    }
    return 'https://www.facebook.com/adsmanager';
  };

  return (
    <div className="min-h-screen bg-brand-dark text-white flex items-center justify-center py-12">
      <div className="max-w-lg w-full mx-auto px-6">
        <Card className="border-green-500/30">
          <div className="p-8 text-center">
            {/* Success Icon */}
            <div className="w-20 h-20 mx-auto mb-6 rounded-full bg-green-500/20 flex items-center justify-center">
              <CheckCircle className="w-12 h-12 text-green-500" />
            </div>

            {/* Title */}
            <h1 className="text-3xl font-display font-bold mb-2">Campaign Published!</h1>
            <p className="text-gray-400 mb-8">
              Your campaign has been created and is ready to review in Meta Ads Manager.
            </p>

            {/* Campaign IDs */}
            <div className="space-y-3 mb-8 text-left">
              {result.campaign_id && (
                <div className="flex items-center justify-between p-3 bg-brand-gray rounded border border-white/10">
                  <span className="text-sm text-gray-400">Campaign ID</span>
                  <span className="font-mono text-sm text-white">{result.campaign_id}</span>
                </div>
              )}
              {result.ad_set_id && (
                <div className="flex items-center justify-between p-3 bg-brand-gray rounded border border-white/10">
                  <span className="text-sm text-gray-400">Ad Set ID</span>
                  <span className="font-mono text-sm text-white">{result.ad_set_id}</span>
                </div>
              )}
              {result.ad_id && (
                <div className="flex items-center justify-between p-3 bg-brand-gray rounded border border-white/10">
                  <span className="text-sm text-gray-400">Ad ID</span>
                  <span className="font-mono text-sm text-white">{result.ad_id}</span>
                </div>
              )}
            </div>

            {/* Status Note */}
            <div className="p-4 bg-yellow-500/10 border border-yellow-500/30 rounded mb-8">
              <p className="text-sm text-yellow-400">
                Your campaign was created in <span className="font-bold">PAUSED</span> status.
                Visit Meta Ads Manager to review and activate it.
              </p>
            </div>

            {/* Actions */}
            <div className="space-y-3">
              <a
                href={getAdsManagerUrl()}
                target="_blank"
                rel="noopener noreferrer"
                className="block"
              >
                <Button variant="primary" className="w-full">
                  Open Meta Ads Manager
                  <ExternalLink className="w-4 h-4 ml-2" />
                </Button>
              </a>

              <Button
                variant="outline"
                onClick={onNewCampaign}
                className="w-full"
              >
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
