import { Navigate, useNavigate } from 'react-router-dom';
import { useAppContext } from '../context/AppContext';
import { AdPackView } from '../components/AdPackView';
import type { AdCreative } from '../types/adpack';

export default function AdPackPage() {
  const ctx = useAppContext();
  const navigate = useNavigate();

  if (!ctx.adPack) return <Navigate to="/" replace />;

  const handleBack = () => {
    ctx.setConfirmOpen(true);
  };

  const handlePublish = (creative: AdCreative) => {
    ctx.setSelectedAd({
      id: 1,
      imageUrl: creative.image_url || creative.asset_url,
      primaryText: creative.primary_text,
      headline: creative.headline,
      description: creative.description,
    });
    navigate('/publish');
  };

  return (
    <AdPackView
      adPack={ctx.adPack}
      onAdPackChange={ctx.setAdPack}
      onBack={handleBack}
      onPublish={handlePublish}
    />
  );
}
