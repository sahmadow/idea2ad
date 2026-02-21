import { useEffect, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import { motion, AnimatePresence } from 'framer-motion';
import { LandingView } from '../components/LandingView';
import { Terminal } from '../components/ui/Terminal';
import { Button } from '../components/ui/Button';
import { useAppContext } from '../context/AppContext';

const LOADING_STAGES = [
  'Analyzing',
  'Generating Copy',
  'Creating Images',
  'Building Ad Pack',
];

const pageTransition = {
  initial: { opacity: 0, y: 20 },
  animate: { opacity: 1, y: 0 },
  exit: { opacity: 0, y: -10 },
  transition: { duration: 0.25 },
};

export default function LandingPage() {
  const ctx = useAppContext();
  const navigate = useNavigate();
  const wasGenerating = useRef(false);

  // Track generating state transitions
  useEffect(() => {
    if (ctx.isGenerating) {
      wasGenerating.current = true;
    }
  }, [ctx.isGenerating]);

  // Navigate to /adpack when generation finishes successfully
  useEffect(() => {
    if (wasGenerating.current && !ctx.isGenerating && ctx.adPack && !ctx.error) {
      wasGenerating.current = false;
      navigate('/adpack');
    }
  }, [ctx.isGenerating, ctx.adPack, ctx.error, navigate]);

  const handleSubmit = async (e: React.FormEvent) => {
    await ctx.startGeneration(e);
  };

  const handleDashboardClick = () => {
    if (!ctx.auth.isAuthenticated) {
      ctx.setAuthModalOpen(true);
      return;
    }
    navigate('/dashboard');
  };

  return (
    <AnimatePresence mode="wait">
      {ctx.isGenerating ? (
        <motion.div key="loading" {...pageTransition}>
          <div className="min-h-screen bg-brand-dark text-white flex flex-col items-center justify-center px-6">
            <div className="text-center space-y-8 max-w-md w-full">
              <div className="w-16 h-16 border-2 border-brand-lime/30 border-t-brand-lime rounded-full animate-spin mx-auto" />
              <div>
                <h2 className="text-2xl font-display font-bold mb-2">
                  {ctx.generationMode === 'quick' ? 'Generating Your Ad' : 'Analyzing Your Page'}
                </h2>
                <p className="text-gray-400 font-mono text-sm truncate">
                  {ctx.generationMode === 'quick' ? ctx.quickIdea.slice(0, 80) + (ctx.quickIdea.length > 80 ? '...' : '') : ctx.url}
                </p>
              </div>

              <div className="flex justify-center gap-3">
                {LOADING_STAGES.map((stage, i) => (
                  <div key={stage} className="flex items-center gap-2">
                    <div className={`w-2 h-2 ${i <= ctx.loadingStage ? 'bg-brand-lime' : 'bg-white/20'} transition-colors`} />
                    <span className={`text-xs font-mono ${i <= ctx.loadingStage ? 'text-white' : 'text-gray-600'} hidden sm:inline transition-colors`}>
                      {stage}
                    </span>
                  </div>
                ))}
              </div>

              <Terminal />

              <Button variant="ghost" size="sm" onClick={ctx.cancelGeneration}>
                Cancel
              </Button>
            </div>
          </div>
        </motion.div>
      ) : (
        <motion.div key="landing" {...pageTransition}>
          <LandingView
            url={ctx.url}
            onUrlChange={ctx.setUrl}
            quickIdea={ctx.quickIdea}
            onQuickIdeaChange={ctx.setQuickIdea}
            generationMode={ctx.generationMode}
            onGenerationModeChange={ctx.setGenerationMode}
            businessType={ctx.businessType}
            onBusinessTypeChange={ctx.setBusinessType}
            productDescription={ctx.productDescription}
            onProductDescriptionChange={ctx.setProductDescription}
            productImagePreview={ctx.productImagePreview}
            productImageFileName={ctx.productImageFile?.name || null}
            isUploading={ctx.isUploading}
            uploadedImageUrl={ctx.uploadedImageUrl}
            onImageSelect={ctx.handleImageSelect}
            editPrompt={ctx.editPrompt}
            onEditPromptChange={ctx.setEditPrompt}
            competitors={ctx.competitors}
            onCompetitorsChange={ctx.setCompetitors}
            onClearImage={ctx.clearProductImage}
            onSubmit={handleSubmit}
            error={ctx.error}
            onDismissError={() => ctx.setError(null)}
            userName={ctx.auth.user?.name || ctx.auth.user?.email || null}
            onSignInClick={ctx.handleSignInClick}
            onDashboardClick={handleDashboardClick}
            onLogout={ctx.handleLogout}
          />
        </motion.div>
      )}
    </AnimatePresence>
  );
}
