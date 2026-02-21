import { useState, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { LandingView } from '../components/LandingView';
import { AnalysisLoadingTerminal } from '../components/ui/AnalysisLoadingTerminal';
import { useAppContext } from '../context/AppContext';

export default function LandingPage() {
  const ctx = useAppContext();
  const navigate = useNavigate();
  const [isTransitioning, setIsTransitioning] = useState(false);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!ctx.input.trim()) return;
    setIsTransitioning(true);
  };

  // Navigate only after the terminal animation finishes
  const handleAnimationComplete = useCallback(() => {
    navigate('/upload');
  }, [navigate]);

  const handleDashboardClick = () => {
    if (!ctx.auth.isAuthenticated) {
      ctx.setAuthModalOpen(true);
      return;
    }
    navigate('/dashboard');
  };

  if (isTransitioning) {
    return (
      <AnalysisLoadingTerminal
        productLabel={ctx.input.trim()}
        onCancel={() => setIsTransitioning(false)}
        onComplete={handleAnimationComplete}
      />
    );
  }

  return (
    <LandingView
      input={ctx.input}
      onInputChange={ctx.setInput}
      onSubmit={handleSubmit}
      error={ctx.error}
      onDismissError={() => ctx.setError(null)}
      userName={ctx.auth.user?.name || ctx.auth.user?.email || null}
      onSignInClick={ctx.handleSignInClick}
      onDashboardClick={handleDashboardClick}
      onLogout={ctx.handleLogout}
    />
  );
}
