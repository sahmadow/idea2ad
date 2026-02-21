import { Navigate, useNavigate } from 'react-router-dom';
import { useAppContext } from '../context/AppContext';
import { ResultsView } from '../components/ResultsView';


export default function ResultsPage() {
  const ctx = useAppContext();
  const navigate = useNavigate();

  if (!ctx.result) return <Navigate to="/" replace />;

  const handleBack = () => {
    if (ctx.result) {
      ctx.setConfirmOpen(true);
      return;
    }
    navigate('/');
  };

  return (
    <ResultsView
      result={ctx.result}
      selectedAd={ctx.selectedAd}
      onSelectAd={ctx.setSelectedAd}
      onBack={handleBack}
      onNext={() => ctx.selectedAd && navigate('/publish')}
      onRegenerate={() => ctx.startGeneration({})}
      competitorData={ctx.competitorData}
      onSave={ctx.handleSaveCampaign}
      isSaving={ctx.isSaving}
      isAuthenticated={ctx.auth.isAuthenticated}
    />
  );
}
