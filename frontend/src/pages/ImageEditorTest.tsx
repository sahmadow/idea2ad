import { useState, useRef } from 'react';
import { ImageOverlayEditor } from '../components/ImageOverlayEditor';
import { Upload, ArrowLeft } from 'lucide-react';

const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000';

export function ImageEditorTest() {
  const [imageUrl, setImageUrl] = useState<string | null>(null);
  const [imageFile, setImageFile] = useState<File | null>(null);
  const [renderedImage, setRenderedImage] = useState<string | null>(null);
  const fileRef = useRef<HTMLInputElement>(null);

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;
    setImageFile(file);
    setImageUrl(URL.createObjectURL(file));
    setRenderedImage(null);
  };

  const handleEditImage = async ({ description }: { description: string }): Promise<string | void> => {
    if (!imageFile) return;

    const form = new FormData();
    form.append('file', imageFile);
    form.append('prompt', description);

    const res = await fetch(`${API_BASE}/v2/playground/edit-image`, {
      method: 'POST',
      body: form,
    });

    if (!res.ok) {
      const err = await res.json();
      throw new Error(err.detail || 'Edit failed');
    }

    const data = await res.json();
    const newUrl = `data:${data.mime_type};base64,${data.image_base64}`;

    // Update the file reference for future edits
    const blob = await fetch(newUrl).then(r => r.blob());
    const newFile = new File([blob], 'edited.png', { type: 'image/png' });
    setImageFile(newFile);

    return newUrl;
  };

  const handleRender = async (params: {
    overlayText: string | null;
    overlayPosition: string;
    description: string | null;
  }) => {
    if (!imageFile) return;

    // Convert current image file to base64
    const reader = new FileReader();
    const base64 = await new Promise<string>((resolve) => {
      reader.onload = () => {
        const result = reader.result as string;
        resolve(result.split(',')[1]);
      };
      reader.readAsDataURL(imageFile);
    });

    const res = await fetch(`${API_BASE}/v2/playground/render-showcase`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        image_base64: base64,
        overlay_text: params.overlayText,
        overlay_position: params.overlayPosition,
      }),
    });

    if (!res.ok) {
      const err = await res.json();
      throw new Error(err.detail || 'Render failed');
    }

    const data = await res.json();
    setRenderedImage(`data:image/png;base64,${data.image_base64}`);
  };

  return (
    <div className="min-h-screen bg-brand-dark text-white">
      {/* Header */}
      <div className="border-b border-white/10 px-6 py-4 flex items-center gap-4">
        <a href="#/" className="text-gray-500 hover:text-gray-300">
          <ArrowLeft className="w-4 h-4" />
        </a>
        <h1 className="text-sm font-mono uppercase tracking-wider text-brand-lime">
          Image Editor Test
        </h1>
        <span className="px-2 py-0.5 text-[10px] font-mono uppercase bg-violet-500/20 text-violet-400 border border-violet-500/30">
          DEV
        </span>
      </div>

      <div className="max-w-6xl mx-auto p-6">
        {!imageUrl ? (
          /* Upload prompt */
          <div className="flex flex-col items-center justify-center py-24">
            <div
              onClick={() => fileRef.current?.click()}
              className="w-80 h-80 border-2 border-dashed border-white/20 hover:border-brand-lime/50 flex flex-col items-center justify-center gap-4 cursor-pointer transition-colors rounded-sm"
            >
              <Upload className="w-12 h-12 text-gray-600" />
              <p className="text-sm text-gray-500 text-center px-6">
                Drop an image here or click to upload
              </p>
            </div>
            <input
              ref={fileRef}
              type="file"
              accept="image/*"
              onChange={handleFileSelect}
              className="hidden"
            />
          </div>
        ) : (
          /* Editor + Preview grid */
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
            {/* Left: Editor */}
            <div>
              <ImageOverlayEditor
                imageUrl={imageUrl}
                onEditImage={handleEditImage}
                onRender={handleRender}
              />
            </div>

            {/* Right: Rendered result */}
            <div>
              <h3 className="text-sm font-mono uppercase tracking-wider text-gray-400 mb-4">
                Rendered Output
              </h3>
              {renderedImage ? (
                <div className="border border-white/10 rounded-sm overflow-hidden">
                  <img
                    src={renderedImage}
                    alt="Rendered creative"
                    className="w-full"
                  />
                </div>
              ) : (
                <div className="aspect-square border border-white/10 rounded-sm flex items-center justify-center">
                  <p className="text-sm text-gray-600 text-center px-6">
                    Click "Render Final Image" to see the output here
                  </p>
                </div>
              )}

              {/* Upload new image */}
              <button
                onClick={() => {
                  setImageUrl(null);
                  setImageFile(null);
                  setRenderedImage(null);
                }}
                className="mt-4 text-xs text-gray-500 hover:text-gray-300 font-mono uppercase tracking-wider"
              >
                Upload different image
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
