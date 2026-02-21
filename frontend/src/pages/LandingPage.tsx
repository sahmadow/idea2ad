import { useNavigate } from 'react-router-dom';
import { LandingView } from '../components/LandingView';
import { useAppContext } from '../context/AppContext';

export default function LandingPage() {
  const ctx = useAppContext();
  const navigate = useNavigate();

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!ctx.input.trim()) return;
    // Navigate to upload page (step 2)
    navigate('/upload');
  };

  const handleDashboardClick = () => {
    if (!ctx.auth.isAuthenticated) {
      ctx.setAuthModalOpen(true);
      return;
    }
    navigate('/dashboard');
  };

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
