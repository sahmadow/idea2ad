import { Navigate, useNavigate } from 'react-router-dom';
import { lazy, Suspense } from 'react';
import { useAppContext } from '../context/AppContext';
import { Skeleton } from '../components/ui/Skeleton';

const SuccessView = lazy(() => import('../components/SuccessView').then(m => ({ default: m.SuccessView })));

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

export default function SuccessPage() {
  const ctx = useAppContext();
  const navigate = useNavigate();

  if (!ctx.publishResult) return <Navigate to="/" replace />;

  return (
    <Suspense fallback={<ViewSkeleton />}>
      <SuccessView
        result={ctx.publishResult}
        onNewCampaign={() => {
          ctx.setUrl('');
          ctx.resetSession();
          navigate('/');
        }}
      />
    </Suspense>
  );
}
