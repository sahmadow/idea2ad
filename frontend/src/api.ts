const API_URL = import.meta.env.VITE_API_URL || "http://127.0.0.1:8000";

// Types matching backend Pydantic models

export type BusinessType = "commerce" | "saas";

export interface AnalyzeRequest {
  url: string;
  business_type?: BusinessType;
  product_description?: string;
  product_image_url?: string;
}

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
  creative_type?: string; // "product" | "person-centric" | "brand-centric"
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

// Job types for async polling
interface JobResponse {
  job_id: string;
  status: string;
  url: string;
}

interface JobStatusResponse {
  job_id: string;
  status: "pending" | "processing" | "complete" | "failed";
  result?: CampaignDraft;
  error?: string;
}

// Polling configuration
const POLL_INTERVAL_MS = 2000; // 2 seconds
const MAX_POLL_ATTEMPTS = 90; // 3 minutes max

const sleep = (ms: number) => new Promise((resolve) => setTimeout(resolve, ms));

const pollJobStatus = async (
  jobId: string,
  onProgress?: (status: string) => void
): Promise<CampaignDraft> => {
  let attempts = 0;

  while (attempts < MAX_POLL_ATTEMPTS) {
    const response = await fetch(`${API_URL}/jobs/${jobId}`);

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || "Failed to check job status");
    }

    const jobStatus: JobStatusResponse = await response.json();

    if (onProgress) {
      onProgress(jobStatus.status);
    }

    if (jobStatus.status === "complete" && jobStatus.result) {
      return jobStatus.result;
    }

    if (jobStatus.status === "failed") {
      throw new Error(jobStatus.error || "Analysis failed");
    }

    // Still processing, wait and try again
    await sleep(POLL_INTERVAL_MS);
    attempts++;
  }

  throw new Error("Analysis timed out. Please try again.");
};

export const analyzeUrl = async (
  url: string,
  onProgress?: (status: string) => void,
  options?: {
    businessType?: BusinessType;
    productDescription?: string;
    productImageUrl?: string;
  }
): Promise<CampaignDraft> => {
  // Start async job
  const requestBody: AnalyzeRequest = {
    url,
    business_type: options?.businessType,
    product_description: options?.productDescription,
    product_image_url: options?.productImageUrl,
  };

  const startResponse = await fetch(`${API_URL}/analyze/async`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(requestBody),
  });

  if (!startResponse.ok) {
    const error = await startResponse.json();
    throw new Error(error.detail || "Failed to start analysis");
  }

  const job: JobResponse = await startResponse.json();

  if (onProgress) {
    onProgress("pending");
  }

  // Poll for results
  return pollJobStatus(job.job_id, onProgress);
};

interface UploadResponse {
  url: string;
  filename: string;
  size: number;
}

// Quick Mode types
export type ToneOption = "professional" | "casual" | "playful" | "urgent" | "friendly";

export interface QuickAd {
  imageUrl?: string;
  primaryText: string;
  headline: string;
  description: string;
  cta: string;
}

export interface QuickAdResponse {
  ads: QuickAd[];
  targeting: string;
  campaignName: string;
}

export const generateQuickAd = async (
  idea: string,
  tone: ToneOption
): Promise<QuickAdResponse> => {
  const response = await fetch(`${API_URL}/quick/generate`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ idea, tone }),
  });

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || "Quick mode generation failed");
  }

  return response.json();
};

export const uploadProductImage = async (file: File): Promise<string> => {
  const formData = new FormData();
  formData.append("file", file);

  const response = await fetch(`${API_URL}/images/upload`, {
    method: "POST",
    body: formData,
  });

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || "Failed to upload image");
  }

  const result: UploadResponse = await response.json();
  return result.url;
};


// =====================================
// COMPETITOR INTELLIGENCE
// =====================================

export interface CompetitorProfile {
  name: string;
  url?: string;
  positioning: string;
  claims: string[];
  pricing?: string;
  differentiators: string[];
  facebook_page_id?: string;
  ad_count: number;
  error?: string;
}

export interface GapRecommendation {
  type: string;
  action: string;
  rationale: string;
  sample?: string;
  priority: string;
}

export interface CompetitorIntelligence {
  competitors: CompetitorProfile[];
  total_ads_analyzed: number;
  profitable_ads_count: number;
  hook_distribution: Record<string, number>;
  angle_distribution: Record<string, number>;
  cta_distribution: Record<string, number>;
  format_distribution: Record<string, number>;
  top_hooks: string[];
  top_angles: string[];
  avg_strength: number;
  gap_analysis: Record<string, unknown>;
  recommendations: GapRecommendation[];
  confidence_score: number;
  status: string;
}

interface CompetitorJobResponse {
  job_id: string;
  status: string;
}

interface CompetitorJobStatusResponse {
  job_id: string;
  status: "pending" | "processing" | "complete" | "failed";
  result?: CompetitorIntelligence;
  error?: string;
}

export const analyzeCompetitors = async (
  competitors: string[],
  userContext?: string,
  onProgress?: (status: string) => void
): Promise<CompetitorIntelligence> => {
  const body = {
    competitors: competitors.map((c) => ({ name_or_url: c })),
    user_context: userContext,
  };

  const startResponse = await fetch(`${API_URL}/competitors/analyze`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });

  if (!startResponse.ok) {
    const error = await startResponse.json();
    throw new Error(error.detail || "Failed to start competitor analysis");
  }

  const job: CompetitorJobResponse = await startResponse.json();

  if (onProgress) {
    onProgress("pending");
  }

  // Poll for results
  let attempts = 0;
  while (attempts < MAX_POLL_ATTEMPTS) {
    const response = await fetch(`${API_URL}/jobs/${job.job_id}`);
    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || "Failed to check job status");
    }

    const jobStatus: CompetitorJobStatusResponse = await response.json();

    if (onProgress) {
      onProgress(jobStatus.status);
    }

    if (jobStatus.status === "complete" && jobStatus.result) {
      return jobStatus.result;
    }

    if (jobStatus.status === "failed") {
      throw new Error(jobStatus.error || "Competitor analysis failed");
    }

    await sleep(POLL_INTERVAL_MS);
    attempts++;
  }

  throw new Error("Competitor analysis timed out. Please try again.");
};
