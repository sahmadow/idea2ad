/**
 * TemplateGallery — browse and select seed templates per ad type.
 * Fetches templates from the API and displays them in a grid.
 */

import { useState, useEffect } from 'react';
import { Grid3X3, Loader2 } from 'lucide-react';

const API_URL = import.meta.env.VITE_API_URL || 'http://127.0.0.1:8000';

interface Template {
  id: string;
  ad_type_id: string;
  aspect_ratio: string;
  name: string;
  canvas_json: object;
  is_default: boolean;
}

interface TemplateGalleryProps {
  adTypeId?: string;
  aspectRatio?: string;
  onSelect: (template: Template) => void;
}

const AD_TYPE_LABELS: Record<string, string> = {
  product_benefits_static: 'Product Benefits',
  review_static: 'Review',
  us_vs_them_solution: 'Us vs Them (Solution)',
  organic_static_solution: 'Organic (Solution)',
  problem_statement_text: 'Problem Text',
  problem_statement_image: 'Problem Image',
  organic_static_problem: 'Organic (Problem)',
  us_vs_them_problem: 'Before/After',
};

export function TemplateGallery({ adTypeId, aspectRatio, onSelect }: TemplateGalleryProps) {
  const [templates, setTemplates] = useState<Template[]>([]);
  const [loading, setLoading] = useState(true);
  const [filterType, setFilterType] = useState(adTypeId || '');
  const [filterRatio, setFilterRatio] = useState(aspectRatio || '');

  useEffect(() => {
    async function fetchTemplates() {
      setLoading(true);
      try {
        const params = new URLSearchParams();
        if (filterType) params.set('ad_type_id', filterType);
        const url = `${API_URL}/v2/templates${params.toString() ? `?${params}` : ''}`;
        const res = await fetch(url);
        if (res.ok) {
          const data = await res.json();
          setTemplates(data);
        }
      } catch (err) {
        console.error('Failed to fetch templates:', err);
      } finally {
        setLoading(false);
      }
    }
    fetchTemplates();
  }, [filterType]);

  const filtered = templates.filter((t) => {
    if (filterRatio && t.aspect_ratio !== filterRatio) return false;
    return true;
  });

  // Group by ad type
  const grouped = filtered.reduce<Record<string, Template[]>>((acc, t) => {
    const key = t.ad_type_id;
    if (!acc[key]) acc[key] = [];
    acc[key].push(t);
    return acc;
  }, {});

  if (loading) {
    return (
      <div className="flex items-center justify-center py-12">
        <Loader2 className="w-6 h-6 animate-spin text-gray-500" />
      </div>
    );
  }

  return (
    <div className="space-y-4">
      {/* Filters */}
      <div className="flex items-center gap-3">
        <select
          value={filterType}
          onChange={(e) => setFilterType(e.target.value)}
          className="bg-white/5 border border-white/10 text-white text-xs px-3 py-2 font-mono"
        >
          <option value="">All Types</option>
          {Object.entries(AD_TYPE_LABELS).map(([id, label]) => (
            <option key={id} value={id}>{label}</option>
          ))}
        </select>

        <div className="flex gap-1">
          {['', '1:1', '9:16', '1.91:1'].map((r) => (
            <button
              key={r}
              onClick={() => setFilterRatio(r)}
              className={`px-3 py-1.5 text-xs font-mono ${
                filterRatio === r
                  ? 'bg-brand-lime text-brand-dark'
                  : 'bg-white/5 text-gray-400 hover:bg-white/10'
              }`}
            >
              {r || 'All'}
            </button>
          ))}
        </div>
      </div>

      {/* Template grid */}
      {Object.entries(grouped).map(([typeId, typeTemplates]) => (
        <div key={typeId}>
          <h4 className="text-xs text-gray-500 font-mono uppercase tracking-wider mb-2">
            {AD_TYPE_LABELS[typeId] || typeId}
          </h4>
          <div className="grid grid-cols-3 gap-3">
            {typeTemplates.map((t) => (
              <button
                key={t.id}
                onClick={() => onSelect(t)}
                className="group relative bg-white/5 border border-white/10 hover:border-brand-lime/50 p-3 transition-colors text-left"
              >
                <div className="flex items-center gap-2 mb-2">
                  <Grid3X3 className="w-3 h-3 text-gray-600" />
                  <span className="text-[10px] text-gray-500 font-mono">
                    {t.aspect_ratio}
                  </span>
                  {t.is_default && (
                    <span className="text-[10px] text-brand-lime/60 font-mono">SEED</span>
                  )}
                </div>
                <p className="text-xs text-gray-300 truncate">{t.name}</p>
              </button>
            ))}
          </div>
        </div>
      ))}

      {filtered.length === 0 && (
        <p className="text-center text-gray-600 text-sm py-8">
          No templates found. Create one or adjust filters.
        </p>
      )}
    </div>
  );
}
