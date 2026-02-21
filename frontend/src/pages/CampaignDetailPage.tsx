import { useParams, useNavigate } from 'react-router-dom';
import { useAppContext } from '../context/AppContext';
import { CampaignDetailView } from '../components/CampaignDetailView';

export default function CampaignDetailPage() {
  const { id } = useParams<{ id: string }>();
  const ctx = useAppContext();
  const navigate = useNavigate();

  if (!id) {
    navigate('/dashboard');
    return null;
  }

  return (
    <CampaignDetailView
      campaign={ctx.campaignsHook.selectedCampaign}
      isLoading={ctx.campaignsHook.isLoading}
      error={ctx.campaignsHook.error}
      campaignId={id}
      userName={ctx.auth.user?.name || ctx.auth.user?.email || null}
      onFetchCampaign={ctx.campaignsHook.fetchCampaign}
      onBack={() => navigate('/dashboard')}
      onLogoClick={() => { ctx.resetSession(); navigate('/'); }}
      onDashboardClick={() => navigate('/dashboard')}
      onLogout={async () => { await ctx.handleLogout(); navigate('/'); }}
      onDismissError={ctx.campaignsHook.clearError}
    />
  );
}
