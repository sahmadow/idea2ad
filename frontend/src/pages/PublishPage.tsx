import { Navigate, useNavigate } from 'react-router-dom';
import { lazy, Suspense } from 'react';
import { useAppContext } from '../context/AppContext';
import { Skeleton } from '../components/ui/Skeleton';
import type { CampaignDraft } from '../api';

const PublishView = lazy(() => import('../components/PublishView').then(m => ({ default: m.PublishView })));

function ViewSkeleton() {
  return (
    <div className="min-h-screen bg-brand-dark flex items-center justify-center">
      <div className="space-y-4 w-full max-w-md px-6">
        <Skeleton className="h-8 w-48 mx-auto" />
        <Skeleton className="h-4 w-64 mx-auto" />
        <Skeleton className="h-64 w-full" />
      </div>
    </div>
  );
}

/** Build a CampaignDraft-compatible object from AdPack for PublishView */
function buildCampaignDataFromAdPack(ctx: ReturnType<typeof useAppContext>): CampaignDraft | null {
  const pack = ctx.adPack;
  if (!pack) return null;

  return {
    project_url: pack.project_url || '',
    analysis: {
      summary: '',
      unique_selling_proposition: '',
      pain_points: [],
      call_to_action: '',
      buyer_persona: {},
      keywords: [],
      styling_guide: {
        primary_colors: [],
        secondary_colors: [],
        font_families: [],
        design_style: '',
        mood: '',
      },
    },
    targeting: {
      age_min: pack.targeting?.age_min ?? 18,
      age_max: pack.targeting?.age_max ?? 65,
      genders: pack.targeting?.genders ?? ['all'],
      geo_locations: pack.targeting?.geo_locations ?? ['US'],
      interests: [],
    },
    suggested_creatives: [],
    image_briefs: [],
    ads: pack.creatives.map((c, i) => ({
      id: i + 1,
      imageUrl: c.image_url || c.asset_url,
      primaryText: c.primary_text,
      headline: c.headline,
      description: c.description,
    })),
    status: pack.status || 'draft',
  };
}

export default function PublishPage() {
  const ctx = useAppContext();
  const navigate = useNavigate();

  // Support both legacy result and new adPack flow
  const campaignData = ctx.result || buildCampaignDataFromAdPack(ctx);

  if (!campaignData || !ctx.selectedAd) return <Navigate to="/" replace />;

  return (
    <Suspense fallback={<ViewSkeleton />}>
      <PublishView
        campaignData={campaignData}
        selectedAd={ctx.selectedAd}
        onBack={() => navigate(ctx.adPack ? '/adpack' : '/results')}
        onSuccess={(res) => {
          ctx.setPublishResult(res);
          navigate('/success');
        }}
      />
    </Suspense>
  );
}
