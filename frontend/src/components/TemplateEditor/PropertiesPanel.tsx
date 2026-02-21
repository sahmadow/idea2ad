/**
 * PropertiesPanel — edit properties of the selected Fabric.js object.
 * Shows font, color, size, position controls based on object type.
 */

import { useState, useCallback } from 'react';
import type { FabricObject, Textbox } from 'fabric';

interface PropertiesPanelProps {
  selectedObject: FabricObject | null;
  onUpdate: () => void;
}

function isTextbox(obj: FabricObject): obj is Textbox {
  return obj.type === 'textbox' || obj.type === 'i-text' || obj.type === 'text';
}

export function PropertiesPanel({ selectedObject, onUpdate }: PropertiesPanelProps) {
  const [fill, setFill] = useState('#FFFFFF');
  const [fontSize, setFontSize] = useState(32);
  const [fontFamily, setFontFamily] = useState('Inter');
  const [fontWeight, setFontWeight] = useState('normal');
  const [textAlign, setTextAlign] = useState('left');
  const [left, setLeft] = useState(0);
  const [top, setTop] = useState(0);
  const [width, setWidth] = useState(100);
  const [height, setHeight] = useState(100);

  // Sync state from selected object (React docs pattern: setState during render)
  const [prevObj, setPrevObj] = useState(selectedObject);
  if (selectedObject && selectedObject !== prevObj) {
    setPrevObj(selectedObject);
    setFill((selectedObject.fill as string) || '#FFFFFF');
    setLeft(Math.round(selectedObject.left || 0));
    setTop(Math.round(selectedObject.top || 0));
    setWidth(Math.round(selectedObject.width || 100));
    setHeight(Math.round(selectedObject.height || 100));

    if (isTextbox(selectedObject)) {
      setFontSize(selectedObject.fontSize || 32);
      setFontFamily(selectedObject.fontFamily || 'Inter');
      setFontWeight((selectedObject.fontWeight as string) || 'normal');
      setTextAlign(selectedObject.textAlign || 'left');
    }
  }

  const updateProp = useCallback(
    (prop: string, value: unknown) => {
      if (!selectedObject) return;
      selectedObject.set(prop as keyof FabricObject, value as never);
      selectedObject.canvas?.renderAll();
      onUpdate();
    },
    [selectedObject, onUpdate]
  );

  if (!selectedObject) {
    return (
      <div className="w-56 bg-brand-dark border-l border-white/10 p-4">
        <p className="text-xs text-gray-500 font-mono uppercase">No selection</p>
        <p className="text-xs text-gray-600 mt-2">Click an object on the canvas to edit its properties.</p>
      </div>
    );
  }

  return (
    <div className="w-56 bg-brand-dark border-l border-white/10 p-4 space-y-4 overflow-y-auto">
      <h3 className="text-xs text-gray-500 font-mono uppercase tracking-wider">
        Properties
      </h3>

      {/* Position */}
      <div className="space-y-2">
        <label className="text-[10px] text-gray-500 uppercase tracking-wider">Position</label>
        <div className="grid grid-cols-2 gap-2">
          <div>
            <span className="text-[10px] text-gray-600">X</span>
            <input
              type="number"
              value={left}
              onChange={(e) => {
                const v = parseInt(e.target.value) || 0;
                setLeft(v);
                updateProp('left', v);
              }}
              className="w-full bg-white/5 border border-white/10 text-white text-xs px-2 py-1 font-mono"
            />
          </div>
          <div>
            <span className="text-[10px] text-gray-600">Y</span>
            <input
              type="number"
              value={top}
              onChange={(e) => {
                const v = parseInt(e.target.value) || 0;
                setTop(v);
                updateProp('top', v);
              }}
              className="w-full bg-white/5 border border-white/10 text-white text-xs px-2 py-1 font-mono"
            />
          </div>
        </div>
      </div>

      {/* Size */}
      <div className="space-y-2">
        <label className="text-[10px] text-gray-500 uppercase tracking-wider">Size</label>
        <div className="grid grid-cols-2 gap-2">
          <div>
            <span className="text-[10px] text-gray-600">W</span>
            <input
              type="number"
              value={width}
              onChange={(e) => {
                const v = parseInt(e.target.value) || 100;
                setWidth(v);
                updateProp('width', v);
              }}
              className="w-full bg-white/5 border border-white/10 text-white text-xs px-2 py-1 font-mono"
            />
          </div>
          <div>
            <span className="text-[10px] text-gray-600">H</span>
            <input
              type="number"
              value={height}
              onChange={(e) => {
                const v = parseInt(e.target.value) || 100;
                setHeight(v);
                updateProp('height', v);
              }}
              className="w-full bg-white/5 border border-white/10 text-white text-xs px-2 py-1 font-mono"
            />
          </div>
        </div>
      </div>

      {/* Fill color */}
      <div className="space-y-2">
        <label className="text-[10px] text-gray-500 uppercase tracking-wider">Color</label>
        <div className="flex items-center gap-2">
          <input
            type="color"
            value={fill}
            onChange={(e) => {
              setFill(e.target.value);
              updateProp('fill', e.target.value);
            }}
            className="w-8 h-8 rounded-none border border-white/10 cursor-pointer"
          />
          <input
            type="text"
            value={fill}
            onChange={(e) => {
              setFill(e.target.value);
              if (e.target.value.startsWith('#') && e.target.value.length >= 4) {
                updateProp('fill', e.target.value);
              }
            }}
            className="flex-1 bg-white/5 border border-white/10 text-white text-xs px-2 py-1 font-mono"
          />
        </div>
      </div>

      {/* Text-specific props */}
      {isTextbox(selectedObject) && (
        <>
          <div className="space-y-2">
            <label className="text-[10px] text-gray-500 uppercase tracking-wider">Font</label>
            <select
              value={fontFamily}
              onChange={(e) => {
                setFontFamily(e.target.value);
                updateProp('fontFamily', e.target.value);
              }}
              className="w-full bg-white/5 border border-white/10 text-white text-xs px-2 py-1"
            >
              <option value="Inter">Inter</option>
              <option value="Arial">Arial</option>
              <option value="Georgia">Georgia</option>
              <option value="Roboto">Roboto</option>
              <option value="Montserrat">Montserrat</option>
            </select>
          </div>

          <div className="space-y-2">
            <label className="text-[10px] text-gray-500 uppercase tracking-wider">Size</label>
            <input
              type="number"
              value={fontSize}
              min={8}
              max={200}
              onChange={(e) => {
                const v = parseInt(e.target.value) || 32;
                setFontSize(v);
                updateProp('fontSize', v);
              }}
              className="w-full bg-white/5 border border-white/10 text-white text-xs px-2 py-1 font-mono"
            />
          </div>

          <div className="space-y-2">
            <label className="text-[10px] text-gray-500 uppercase tracking-wider">Weight</label>
            <div className="flex gap-1">
              {(['normal', 'bold'] as const).map((w) => (
                <button
                  key={w}
                  onClick={() => {
                    setFontWeight(w);
                    updateProp('fontWeight', w);
                  }}
                  className={`flex-1 px-2 py-1 text-xs font-mono uppercase ${
                    fontWeight === w
                      ? 'bg-brand-lime text-brand-dark'
                      : 'bg-white/5 text-gray-400 hover:bg-white/10'
                  }`}
                >
                  {w === 'bold' ? <strong>B</strong> : 'N'}
                </button>
              ))}
            </div>
          </div>

          <div className="space-y-2">
            <label className="text-[10px] text-gray-500 uppercase tracking-wider">Align</label>
            <div className="flex gap-1">
              {(['left', 'center', 'right'] as const).map((a) => (
                <button
                  key={a}
                  onClick={() => {
                    setTextAlign(a);
                    updateProp('textAlign', a);
                  }}
                  className={`flex-1 px-2 py-1 text-xs font-mono ${
                    textAlign === a
                      ? 'bg-brand-lime text-brand-dark'
                      : 'bg-white/5 text-gray-400 hover:bg-white/10'
                  }`}
                >
                  {a[0].toUpperCase()}
                </button>
              ))}
            </div>
          </div>
        </>
      )}
    </div>
  );
}
