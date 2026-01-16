const API_URL = import.meta.env.VITE_API_URL || "http://127.0.0.1:8000";

// Types matching backend Pydantic models

export interface StylingGuide {
  primary_colors: string[];
  secondary_colors: string[];
  font_families: string[];
  design_style: string;
  mood: string;
}

export interface AnalysisResult {
  summary: string;
  unique_selling_proposition: string;
  pain_points: string[];
  call_to_action: string;
  buyer_persona: Record<string, unknown>;
  keywords: string[];
  styling_guide: StylingGuide;
}

export interface TextOverlay {
  content: string;
  font_size: string;
  position: string;
  color: string;
  background?: string;
}

export interface ImageBrief {
  approach: string;
  visual_description: string;
  styling_notes: string;
  text_overlays: TextOverlay[];
  meta_best_practices: string[];
  rationale: string;
  image_url?: string;
}

export interface CreativeAsset {
  type: string;
  content: string;
  rationale?: string;
  image_url?: string;
}

export interface AdSetTargeting {
  age_min: number;
  age_max: number;
  genders: string[];
  geo_locations: string[];
  interests: string[];
}

export interface Ad {
  id: number;
  imageUrl?: string;
  primaryText: string;
  headline: string;
  description: string;
  imageBrief?: ImageBrief;
}

export interface CampaignDraft {
  project_url: string;
  analysis: AnalysisResult;
  targeting: AdSetTargeting;
  suggested_creatives: CreativeAsset[];
  image_briefs: ImageBrief[];
  ads?: Ad[];
  status: string;
}

export const analyzeUrl = async (url: string): Promise<CampaignDraft> => {
  const response = await fetch(`${API_URL}/analyze`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ url }),
  });

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || "Analysis failed");
  }

  return response.json();
};
