import { lazy, Suspense } from 'react';
import { Routes, Route, Navigate, useLocation, useNavigate } from 'react-router-dom';
import { AnimatePresence, motion } from 'framer-motion';
import { useAppContext } from './context/AppContext';
import { AuthModal } from './components/AuthModal';
import { ConfirmDialog } from './components/ui/ConfirmDialog';
import { Skeleton } from './components/ui/Skeleton';
import { AuthGuard } from './components/AuthGuard';
import LandingPage from './pages/LandingPage';

// Lazy-loaded pages
const UploadPage = lazy(() => import('./pages/UploadPage'));
const ReviewPage = lazy(() => import('./pages/ReviewPage'));
const AdPackPage = lazy(() => import('./pages/AdPackPage'));
const ResultsPage = lazy(() => import('./pages/ResultsPage'));
const PublishPage = lazy(() => import('./pages/PublishPage'));
const SuccessPage = lazy(() => import('./pages/SuccessPage'));
const DashboardPage = lazy(() => import('./pages/DashboardPage'));
const CampaignDetailPage = lazy(() => import('./pages/CampaignDetailPage'));
const FBAuthTest = lazy(() => import('./pages/FBAuthTest').then(m => ({ default: m.FBAuthTest })));
const ImageEditorTest = lazy(() => import('./pages/ImageEditorTest').then(m => ({ default: m.ImageEditorTest })));
const TermsPage = lazy(() => import('./pages/TermsPage'));
const PrivacyPage = lazy(() => import('./pages/PrivacyPage'));

const pageTransition = {
  initial: { opacity: 0, y: 20 },
  animate: { opacity: 1, y: 0 },
  exit: { opacity: 0, y: -10 },
  transition: { duration: 0.25 },
};

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

export function AppRoutes() {
  const location = useLocation();
  const navigate = useNavigate();
  const ctx = useAppContext();

  return (
    <main>
      <AnimatePresence mode="wait">
        <motion.div key={location.pathname} {...pageTransition}>
          <Suspense fallback={<ViewSkeleton />}>
            <Routes location={location}>
              <Route path="/" element={<LandingPage />} />
              <Route path="/upload" element={<UploadPage />} />
              <Route path="/review" element={<ReviewPage />} />
              <Route path="/adpack" element={<AdPackPage />} />
              <Route path="/results" element={<ResultsPage />} />
              <Route path="/publish" element={<PublishPage />} />
              <Route path="/success" element={<SuccessPage />} />
              <Route
                path="/dashboard"
                element={
                  <AuthGuard>
                    <DashboardPage />
                  </AuthGuard>
                }
              />
              <Route
                path="/campaigns/:id"
                element={
                  <AuthGuard>
                    <CampaignDetailPage />
                  </AuthGuard>
                }
              />
              <Route path="/terms" element={<TermsPage />} />
              <Route path="/privacy" element={<PrivacyPage />} />
              <Route path="/test/fb-auth" element={<FBAuthTest />} />
              <Route path="/test/image-editor" element={<ImageEditorTest />} />
              <Route path="*" element={<Navigate to="/" replace />} />
            </Routes>
          </Suspense>
        </motion.div>
      </AnimatePresence>

      {/* Global modals */}
      <ConfirmDialog
        open={ctx.confirmOpen}
        title="Discard results?"
        message="You'll lose the generated campaign. This can't be undone."
        confirmLabel="Discard"
        cancelLabel="Keep"
        onConfirm={() => {
          ctx.setConfirmOpen(false);
          ctx.resetSession();
          navigate('/');
        }}
        onCancel={() => ctx.setConfirmOpen(false)}
      />

      <AuthModal
        open={ctx.authModalOpen}
        onClose={() => {
          ctx.setAuthModalOpen(false);
          ctx.auth.clearError();
        }}
        onLogin={ctx.auth.login}
        onRegister={ctx.auth.register}
        error={ctx.auth.error}
        isLoading={ctx.auth.isLoading}
      />
    </main>
  );
}
