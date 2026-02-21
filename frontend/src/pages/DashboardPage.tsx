import { useNavigate } from 'react-router-dom';
import { useAppContext } from '../context/AppContext';
import { DashboardView } from '../components/DashboardView';

export default function DashboardPage() {
  const ctx = useAppContext();
  const navigate = useNavigate();

  return (
    <DashboardView
      campaigns={ctx.campaignsHook.campaigns}
      isLoading={ctx.campaignsHook.isLoading}
      error={ctx.campaignsHook.error}
      userName={ctx.auth.user?.name || ctx.auth.user?.email || null}
      onFetchCampaigns={ctx.campaignsHook.fetchCampaigns}
      onViewCampaign={(id) => navigate(`/campaigns/${id}`)}
      onDeleteCampaign={ctx.campaignsHook.removeCampaign}
      onNewCampaign={() => { ctx.resetSession(); navigate('/'); }}
      onLogoClick={() => { ctx.resetSession(); navigate('/'); }}
      onDashboardClick={() => navigate('/dashboard')}
      onLogout={async () => { await ctx.handleLogout(); navigate('/'); }}
      onDismissError={ctx.campaignsHook.clearError}
    />
  );
}
