from pydantic import BaseModel
from typing import List, Optional, Dict, Any

class Project(BaseModel):
    url: str
    objective: str = "OUTCOME_SALES"  # Default Meta Objective
    budget_daily: float = 20.0

class StylingGuide(BaseModel):
    primary_colors: List[str]  # Hex color codes
    secondary_colors: List[str]  # Hex color codes
    font_families: List[str]  # Font names detected
    design_style: str  # e.g., "modern", "minimalist", "bold"
    mood: str  # e.g., "professional", "playful", "luxurious"

class AnalysisResult(BaseModel):
    summary: str
    unique_selling_proposition: str
    pain_points: List[str]
    call_to_action: str
    buyer_persona: Dict[str, Any]  # { "age_range": [25, 45], "gender": "All", ... }
    keywords: List[str]
    styling_guide: StylingGuide

class CreativeAsset(BaseModel):
    type: str # "image", "video", "copy_primary", "copy_headline"
    content: str # URL or Text
    rationale: Optional[str] = None
    image_url: Optional[str] = None

class TextOverlay(BaseModel):
    content: str  # The actual text to display
    font_size: str  # e.g., "large", "medium", "small", "48px"
    position: str  # e.g., "top-left", "center", "bottom-right"
    color: str  # Hex color code
    background: Optional[str] = None  # Optional background color/style

class ImageBrief(BaseModel):
    approach: str  # e.g., "product-focused", "lifestyle", "problem-solution"
    visual_description: str  # Detailed scene description
    styling_notes: str  # How to apply landing page styling
    text_overlays: List[TextOverlay]  # Explicit text specifications
    meta_best_practices: List[str]  # Applied best practices
    rationale: str  # Why this approach works
    image_url: Optional[str] = None  # Generated image URL

class AdSetTargeting(BaseModel):
    age_min: int = 18
    age_max: int = 65
    genders: List[str] = ["male", "female"]
    geo_locations: List[str] = ["US"]
    interests: List[str] # Detailed targeting keywords
    
class CampaignDraft(BaseModel):
    project_url: str
    analysis: AnalysisResult
    targeting: AdSetTargeting
    suggested_creatives: List[CreativeAsset]
    image_briefs: List[ImageBrief]
    status: str = "DRAFT"
