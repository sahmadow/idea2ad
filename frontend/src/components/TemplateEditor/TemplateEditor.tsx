/**
 * TemplateEditor — main editor combining canvas, toolbar, panels, and gallery.
 * Supports aspect ratio tabs, variable preview toggle, and save-to-backend.
 */

import { useState, useCallback } from 'react';
import { X, Save, Eye, EyeOff, Loader2 } from 'lucide-react';
import { toast } from 'sonner';
import { Button } from '../ui/Button';
import { FabricCanvas } from './FabricCanvas';
import { Toolbar } from './Toolbar';
import { PropertiesPanel } from './PropertiesPanel';
import { LayersPanel } from './LayersPanel';
import { TemplateGallery } from './TemplateGallery';
import { useFabricCanvas } from './hooks/useFabricCanvas';

const API_URL = import.meta.env.VITE_API_URL || 'http://127.0.0.1:8000';

// Canvas sizes per aspect ratio
const SIZES: Record<string, [number, number]> = {
  '1:1': [1080, 1080],
  '9:16': [1080, 1920],
  '1.91:1': [1200, 628],
};

interface TemplateEditorProps {
  adTypeId: string;
  initialAspectRatio?: string;
  templateId?: string;
  initialCanvasJson?: object;
  onSave?: (templateId: string, canvasJson: object) => void;
  onClose: () => void;
}

type EditorView = 'editor' | 'gallery';

export function TemplateEditor({
  adTypeId,
  initialAspectRatio = '1:1',
  templateId: initialTemplateId,
  initialCanvasJson,
  onSave,
  onClose,
}: TemplateEditorProps) {
  const [activeRatio, setActiveRatio] = useState(initialAspectRatio);
  const [templateId, setTemplateId] = useState(initialTemplateId);
  const [view, setView] = useState<EditorView>(initialCanvasJson ? 'editor' : 'gallery');
  const [saving, setSaving] = useState(false);
  const [showVariables, setShowVariables] = useState(true);

  // Per-ratio canvas JSON storage
  const [ratioJsonMap, setRatioJsonMap] = useState<Record<string, object>>(() => {
    const map: Record<string, object> = {};
    if (initialCanvasJson) {
      map[initialAspectRatio] = initialCanvasJson;
    }
    return map;
  });

  const [w, h] = SIZES[activeRatio] || SIZES['1:1'];

  const handleModified = useCallback(
    (json: object) => {
      setRatioJsonMap((prev) => ({ ...prev, [activeRatio]: json }));
    },
    [activeRatio]
  );

  const {
    canvasRef,
    canvas,
    selectedObject,
    loadFromJSON,
    exportJSON,
    addText,
    addRect,
    deleteSelected,
    undo,
    redo,
    canUndo,
    canRedo,
    zoomIn,
    zoomOut,
    zoomReset,
    zoom,
  } = useFabricCanvas({ width: w, height: h, onModified: handleModified });

  // Switch aspect ratio — save current, load target
  const handleRatioChange = useCallback(
    async (ratio: string) => {
      if (ratio === activeRatio) return;
      // Save current state
      const current = exportJSON();
      if (current) {
        setRatioJsonMap((prev) => ({ ...prev, [activeRatio]: current }));
      }
      setActiveRatio(ratio);
      // Load target ratio's JSON if we have it
      const target = ratioJsonMap[ratio];
      if (target) {
        setTimeout(() => loadFromJSON(target), 50);
      }
    },
    [activeRatio, exportJSON, loadFromJSON, ratioJsonMap]
  );

  // Select template from gallery
  const handleTemplateSelect = useCallback(
    async (template: { id: string; canvas_json: object; aspect_ratio: string }) => {
      setTemplateId(template.id);
      setActiveRatio(template.aspect_ratio);
      setRatioJsonMap((prev) => ({
        ...prev,
        [template.aspect_ratio]: template.canvas_json,
      }));
      setView('editor');
      // Small delay to ensure canvas is mounted
      setTimeout(() => loadFromJSON(template.canvas_json), 100);
    },
    [loadFromJSON]
  );

  // Save template to backend
  const handleSave = useCallback(async () => {
    const json = exportJSON();
    if (!json) return;

    setSaving(true);
    try {
      if (templateId) {
        // Update existing
        const res = await fetch(`${API_URL}/v2/templates/${templateId}`, {
          method: 'PUT',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ canvas_json: json }),
        });
        if (!res.ok) throw new Error('Failed to save');
        toast.success('Template saved');
      } else {
        // Create new
        const res = await fetch(`${API_URL}/v2/templates`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            ad_type_id: adTypeId,
            aspect_ratio: activeRatio,
            name: `Custom — ${adTypeId} ${activeRatio}`,
            canvas_json: json,
          }),
        });
        if (!res.ok) throw new Error('Failed to create');
        const created = await res.json();
        setTemplateId(created.id);
        toast.success('Template created');
      }
      onSave?.(templateId || '', json);
    } catch (err) {
      toast.error('Failed to save template');
      console.error(err);
    } finally {
      setSaving(false);
    }
  }, [exportJSON, templateId, adTypeId, activeRatio, onSave]);

  const handleForceUpdate = useCallback(() => {
    // Trigger re-render for property panel sync
    canvas?.renderAll();
  }, [canvas]);

  if (view === 'gallery') {
    return (
      <div className="fixed inset-0 z-50 bg-brand-dark flex flex-col">
        {/* Header */}
        <div className="flex items-center justify-between px-6 py-4 border-b border-white/10">
          <h2 className="text-sm font-mono text-white uppercase tracking-wider">
            Select Template
          </h2>
          <button onClick={onClose} className="text-gray-400 hover:text-white">
            <X className="w-5 h-5" />
          </button>
        </div>
        <div className="flex-1 overflow-y-auto p-6">
          <TemplateGallery
            adTypeId={adTypeId}
            onSelect={handleTemplateSelect}
          />
        </div>
      </div>
    );
  }

  return (
    <div className="fixed inset-0 z-50 bg-brand-dark flex flex-col">
      {/* Header */}
      <div className="flex items-center justify-between px-4 py-2 border-b border-white/10">
        <div className="flex items-center gap-4">
          <h2 className="text-sm font-mono text-white uppercase tracking-wider">
            Template Editor
          </h2>

          {/* Aspect ratio tabs */}
          <div className="flex gap-1">
            {Object.keys(SIZES).map((ratio) => (
              <button
                key={ratio}
                onClick={() => handleRatioChange(ratio)}
                className={`px-3 py-1.5 text-xs font-mono ${
                  activeRatio === ratio
                    ? 'bg-brand-lime text-brand-dark'
                    : 'bg-white/5 text-gray-400 hover:bg-white/10'
                }`}
              >
                {ratio}
              </button>
            ))}
          </div>

          {/* Variable toggle */}
          <button
            onClick={() => setShowVariables((v) => !v)}
            className={`flex items-center gap-1.5 px-3 py-1.5 text-xs font-mono ${
              showVariables
                ? 'bg-violet-500/20 text-violet-400'
                : 'bg-white/5 text-gray-500'
            }`}
            title={showVariables ? 'Showing {{variables}}' : 'Variables hidden'}
          >
            {showVariables ? <Eye className="w-3 h-3" /> : <EyeOff className="w-3 h-3" />}
            Vars
          </button>

          {/* Gallery button */}
          <button
            onClick={() => setView('gallery')}
            className="px-3 py-1.5 text-xs font-mono bg-white/5 text-gray-400 hover:bg-white/10"
          >
            Gallery
          </button>
        </div>

        <div className="flex items-center gap-2">
          <Button
            variant="primary"
            size="sm"
            onClick={handleSave}
            loading={saving}
          >
            <Save className="w-3.5 h-3.5 mr-1.5" />
            Save
          </Button>
          <button onClick={onClose} className="text-gray-400 hover:text-white p-2">
            <X className="w-5 h-5" />
          </button>
        </div>
      </div>

      {/* Toolbar */}
      <Toolbar
        onAddText={addText}
        onAddRect={addRect}
        onDelete={deleteSelected}
        onUndo={undo}
        onRedo={redo}
        onZoomIn={zoomIn}
        onZoomOut={zoomOut}
        onZoomReset={zoomReset}
        canUndo={canUndo}
        canRedo={canRedo}
        hasSelection={!!selectedObject}
        zoom={zoom}
      />

      {/* Main area: Layers | Canvas | Properties */}
      <div className="flex-1 flex overflow-hidden">
        <LayersPanel
          canvas={canvas}
          selectedObject={selectedObject}
          onSelect={() => {}}
        />

        {/* Canvas area */}
        <div className="flex-1 flex items-center justify-center bg-[#0d0d0d] overflow-auto p-8">
          <FabricCanvas
            canvasRef={canvasRef}
            width={w}
            height={h}
            displayScale={activeRatio === '9:16' ? 0.35 : 0.5}
          />
        </div>

        <PropertiesPanel
          selectedObject={selectedObject}
          onUpdate={handleForceUpdate}
        />
      </div>
    </div>
  );
}
