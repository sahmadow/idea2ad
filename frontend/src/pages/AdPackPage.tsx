import { Navigate, useNavigate } from 'react-router-dom';
import { useAppContext } from '../context/AppContext';
import { AdPackView } from '../components/AdPackView';
import type { Ad } from '../api';

export default function AdPackPage() {
  const ctx = useAppContext();
  const navigate = useNavigate();

  if (!ctx.adPack) return <Navigate to="/" replace />;

  const handleBack = () => {
    if (ctx.adPack) {
      ctx.setConfirmOpen(true);
      return;
    }
    navigate('/');
  };

  const handlePublish = (ad: Ad) => {
    ctx.setSelectedAd(ad);
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
