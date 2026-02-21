import { Navigate, useNavigate } from 'react-router-dom';
import { lazy, Suspense } from 'react';
import { useAppContext } from '../context/AppContext';
import { Skeleton } from '../components/ui/Skeleton';

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

export default function PublishPage() {
  const ctx = useAppContext();
  const navigate = useNavigate();

  if (!ctx.result || !ctx.selectedAd) return <Navigate to="/" replace />;

  return (
    <Suspense fallback={<ViewSkeleton />}>
      <PublishView
        campaignData={ctx.result}
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
