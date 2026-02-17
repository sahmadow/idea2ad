/**
 * LayersPanel — object list with reorder, visibility, and lock controls.
 */

import { useState, useEffect } from 'react';
import { Eye, EyeOff, Lock, Unlock, ArrowUp, ArrowDown } from 'lucide-react';
import type { Canvas, FabricObject } from 'fabric';

interface LayersPanelProps {
  canvas: Canvas | null;
  selectedObject: FabricObject | null;
  onSelect: (obj: FabricObject) => void;
}

interface LayerItem {
  obj: FabricObject;
  label: string;
  visible: boolean;
  locked: boolean;
}

function getObjectLabel(obj: FabricObject): string {
  const type = obj.type || 'object';
  if (type === 'textbox' || type === 'i-text' || type === 'text') {
    const text = (obj as { text?: string }).text || '';
    const preview = text.slice(0, 20);
    return preview.length < text.length ? `${preview}...` : preview || 'Text';
  }
  if (type === 'rect') return 'Rectangle';
  if (type === 'circle') return 'Circle';
  if (type === 'image') return 'Image';
  return type.charAt(0).toUpperCase() + type.slice(1);
}

export function LayersPanel({ canvas, selectedObject, onSelect }: LayersPanelProps) {
  const [layers, setLayers] = useState<LayerItem[]>([]);
  const [, setTick] = useState(0);

  // Rebuild layer list when canvas changes
  useEffect(() => {
    if (!canvas) return;

    const refresh = () => {
      const objects = canvas.getObjects();
      setLayers(
        objects.map((obj) => ({
          obj,
          label: getObjectLabel(obj),
          visible: obj.visible !== false,
          locked: !obj.selectable,
        })).reverse() // top-most layer first
      );
    };

    refresh();
    canvas.on('object:added', refresh);
    canvas.on('object:removed', refresh);
    canvas.on('object:modified', refresh);

    return () => {
      canvas.off('object:added', refresh);
      canvas.off('object:removed', refresh);
      canvas.off('object:modified', refresh);
    };
  }, [canvas]);

  const toggleVisibility = (layer: LayerItem) => {
    layer.obj.visible = !layer.obj.visible;
    canvas?.renderAll();
    setTick((t) => t + 1);
  };

  const toggleLock = (layer: LayerItem) => {
    const locked = layer.obj.selectable;
    layer.obj.selectable = !locked;
    layer.obj.evented = !locked;
    canvas?.renderAll();
    setTick((t) => t + 1);
  };

  const moveUp = (layer: LayerItem) => {
    if (!canvas) return;
    canvas.bringObjectForward(layer.obj);
    canvas.renderAll();
    setTick((t) => t + 1);
  };

  const moveDown = (layer: LayerItem) => {
    if (!canvas) return;
    canvas.sendObjectBackwards(layer.obj);
    canvas.renderAll();
    setTick((t) => t + 1);
  };

  return (
    <div className="w-56 bg-brand-dark border-r border-white/10 flex flex-col">
      <div className="px-4 py-3 border-b border-white/10">
        <h3 className="text-xs text-gray-500 font-mono uppercase tracking-wider">
          Layers ({layers.length})
        </h3>
      </div>

      <div className="flex-1 overflow-y-auto">
        {layers.map((layer, i) => {
          const isSelected = selectedObject === layer.obj;
          return (
            <div
              key={i}
              onClick={() => {
                if (layer.obj.selectable !== false) {
                  canvas?.setActiveObject(layer.obj);
                  canvas?.renderAll();
                  onSelect(layer.obj);
                }
              }}
              className={`flex items-center gap-2 px-3 py-2 cursor-pointer border-b border-white/5 ${
                isSelected ? 'bg-brand-lime/10 border-l-2 border-l-brand-lime' : 'hover:bg-white/5'
              }`}
            >
              <span
                className={`flex-1 text-xs font-mono truncate ${
                  isSelected ? 'text-white' : 'text-gray-400'
                } ${!layer.visible ? 'opacity-40' : ''}`}
              >
                {layer.label}
              </span>

              <div className="flex items-center gap-0.5">
                <button
                  onClick={(e) => { e.stopPropagation(); moveUp(layer); }}
                  className="p-1 text-gray-600 hover:text-gray-400"
                  title="Move up"
                >
                  <ArrowUp className="w-3 h-3" />
                </button>
                <button
                  onClick={(e) => { e.stopPropagation(); moveDown(layer); }}
                  className="p-1 text-gray-600 hover:text-gray-400"
                  title="Move down"
                >
                  <ArrowDown className="w-3 h-3" />
                </button>
                <button
                  onClick={(e) => { e.stopPropagation(); toggleVisibility(layer); }}
                  className="p-1 text-gray-600 hover:text-gray-400"
                  title={layer.visible ? 'Hide' : 'Show'}
                >
                  {layer.visible ? <Eye className="w-3 h-3" /> : <EyeOff className="w-3 h-3" />}
                </button>
                <button
                  onClick={(e) => { e.stopPropagation(); toggleLock(layer); }}
                  className="p-1 text-gray-600 hover:text-gray-400"
                  title={layer.locked ? 'Unlock' : 'Lock'}
                >
                  {layer.locked ? <Lock className="w-3 h-3" /> : <Unlock className="w-3 h-3" />}
                </button>
              </div>
            </div>
          );
        })}

        {layers.length === 0 && (
          <p className="px-4 py-8 text-xs text-gray-600 text-center">
            No layers yet. Add objects using the toolbar.
          </p>
        )}
      </div>
    </div>
  );
}
