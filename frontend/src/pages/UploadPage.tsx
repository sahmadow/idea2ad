import { useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import { motion } from 'framer-motion';
import { ArrowLeft, ArrowRight, Upload, X, Loader2 } from 'lucide-react';
import { Button } from '../components/ui/Button';
import { ErrorBanner } from '../components/ui/ErrorBanner';
import { CompetitorInput } from '../components/CompetitorInput';
import { useAppContext } from '../context/AppContext';

export default function UploadPage() {
  const ctx = useAppContext();
  const navigate = useNavigate();
  const fileInputRef = useRef<HTMLInputElement>(null);

  // Guard: must have input from step 1
  if (!ctx.input.trim()) {
    navigate('/', { replace: true });
    return null;
  }

  const handleAnalyze = async () => {
    await ctx.startAnalysis();
  };

  // Navigate to review when prepared campaign is ready
  if (ctx.preparedCampaign && !ctx.isAnalyzing) {
    navigate('/review', { replace: true });
    return null;
  }

  return (
    <div className="min-h-screen bg-brand-dark text-white flex flex-col">
      {/* Header */}
      <div className="border-b border-white/5 px-6 py-4">
        <div className="max-w-2xl mx-auto flex items-center justify-between">
          <button
            onClick={() => navigate('/')}
            className="flex items-center gap-2 text-sm text-gray-400 hover:text-white transition-colors font-mono"
          >
            <ArrowLeft className="w-4 h-4" />
            Back
          </button>
          <div className="text-xs font-mono text-gray-500">Step 2 of 3</div>
        </div>
      </div>

      {/* Content */}
      <div className="flex-1 flex items-center justify-center px-6 py-12">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="w-full max-w-lg space-y-8"
        >
          <div className="text-center space-y-2">
            <h2 className="text-2xl font-display font-bold">Upload & Extras</h2>
            <p className="text-gray-400 text-sm font-mono">
              Optional: add a product image and competitor URLs
            </p>
          </div>

          {/* Product Image Upload */}
          <div className="space-y-3">
            <label className="text-sm font-mono text-gray-300">Product Image (optional)</label>

            <input
              ref={fileInputRef}
              type="file"
              accept="image/jpeg,image/png,image/webp"
              onChange={ctx.handleImageSelect}
              className="hidden"
              id="upload-page-image"
            />

            {!ctx.productImagePreview ? (
              <label
                htmlFor="upload-page-image"
                className="flex flex-col items-center justify-center gap-3 w-full h-32 bg-brand-gray border border-dashed border-white/20 hover:border-brand-lime/50 cursor-pointer transition-colors"
                tabIndex={0}
                onKeyDown={(e) => {
                  if (e.key === 'Enter' || e.key === ' ') {
                    e.preventDefault();
                    fileInputRef.current?.click();
                  }
                }}
              >
                <Upload className="w-6 h-6 text-gray-400" />
                <span className="text-sm font-mono text-gray-400">Click to upload (JPEG, PNG, WebP)</span>
                <span className="text-xs font-mono text-gray-600">Max 10MB</span>
              </label>
            ) : (
              <div className="flex items-center gap-4 p-4 bg-brand-gray border border-white/10">
                <img src={ctx.productImagePreview} alt="Product preview" className="w-16 h-16 object-cover" />
                <div className="flex-1 min-w-0">
                  <p className="text-sm font-mono text-white truncate">{ctx.productImageFile?.name}</p>
                  <p className="text-xs text-gray-500 font-mono">
                    {ctx.isUploading ? 'Uploading...' : ctx.uploadedImageUrl ? 'Uploaded' : 'Ready'}
                  </p>
                </div>
                <button type="button" onClick={ctx.clearProductImage} className="p-1 hover:bg-white/10 transition-colors">
                  <X className="w-4 h-4 text-gray-400" />
                </button>
              </div>
            )}
          </div>

          {/* Competitor URLs */}
          <div className="space-y-3 pt-4 border-t border-white/10">
            <CompetitorInput
              competitors={ctx.competitors}
              onCompetitorsChange={ctx.setCompetitors}
            />
          </div>

          {/* Error */}
          {ctx.error && (
            <ErrorBanner message={ctx.error} onDismiss={() => ctx.setError(null)} />
          )}

          {/* Actions */}
          <div className="flex gap-4 pt-4">
            <Button
              variant="secondary"
              className="flex-1"
              onClick={() => navigate('/')}
            >
              <ArrowLeft className="w-4 h-4 mr-2" />
              Back
            </Button>
            <Button
              variant="primary"
              className="flex-1 group"
              onClick={handleAnalyze}
              disabled={ctx.isAnalyzing || ctx.isUploading}
            >
              {ctx.isAnalyzing ? (
                <>
                  <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                  Analyzing...
                </>
              ) : (
                <>
                  Analyze
                  <ArrowRight className="w-4 h-4 ml-2 group-hover:translate-x-1 transition-transform" />
                </>
              )}
            </Button>
          </div>

          <p className="text-xs text-gray-600 font-mono text-center">
            You can skip the image — we'll use your landing page or description instead
          </p>
        </motion.div>
      </div>
    </div>
  );
}
