from pydantic import BaseModel
from typing import List, Optional, Dict, Any, Literal


# Business type determines creative generation strategy
BusinessType = Literal["commerce", "saas"]


class Project(BaseModel):
    url: str
    objective: str = "OUTCOME_SALES"  # Default Meta Objective
    budget_daily: float = 20.0
    business_type: BusinessType = "commerce"
    product_description: Optional[str] = None  # Optional product description for commerce
    product_image_url: Optional[str] = None  # Optional user-uploaded product image URL


class StylingGuide(BaseModel):
    primary_colors: List[str]  # Hex color codes
    secondary_colors: List[str]  # Hex color codes
    font_families: List[str]  # Font names detected
    design_style: str  # e.g., "modern", "minimalist", "bold"
    mood: str  # e.g., "professional", "playful", "luxurious"


class LogoInfo(BaseModel):
    """Detected logo information from landing page."""
    url: str  # Direct URL or data URI
    type: str  # svg, png, jpg, ico
    source: str  # schema, header, favicon
    confidence: str  # high, medium, low
    width: Optional[int] = None
    height: Optional[int] = None
    score: Optional[int] = None


class DesignTokens(BaseModel):
    """Design tokens extracted from landing page CSS."""
    gradients: List[Dict[str, Any]] = []  # [{type, raw, colors}]
    border_radius: Optional[str] = None  # e.g., "8px"
    box_shadow: Optional[str] = None  # CSS box-shadow value


class BrandCSS(BaseModel):
    """Extracted CSS assets from landing page for HTML template rendering."""
    font_faces: List[str] = []  # @font-face CSS rules
    css_variables: Dict[str, str] = {}  # --var-name: value
    button_styles: Dict[str, str] = {}  # CTA computed styles
    primary_colors: List[str] = []  # Hex color codes
    secondary_colors: List[str] = []  # Hex color codes
    font_families: List[str] = []  # Font family names


class AnalysisResult(BaseModel):
    summary: str
    unique_selling_proposition: str
    pain_points: List[str]
    call_to_action: str
    buyer_persona: Dict[str, Any]  # { "age_range": [25, 45], "gender": "All", ... }
    keywords: List[str]
    styling_guide: StylingGuide
    logo: Optional[LogoInfo] = None  # Detected logo
    design_tokens: Optional[DesignTokens] = None  # CSS design tokens

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
    render_mode: str = "template"  # "template" | "imagen"
    product_image_prompt: Optional[str] = None  # Prompt for isolated product image
    product_image_url: Optional[str] = None  # URL after product image generation
    creative_type: Optional[str] = None  # "product" | "person-centric" | "brand-centric" (for SaaS)

class AdSetTargeting(BaseModel):
    age_min: int = 18
    age_max: int = 65
    genders: List[str] = ["male", "female"]
    geo_locations: List[str] = ["US"]
    interests: List[str] # Detailed targeting keywords
    
class Ad(BaseModel):
    """Complete ad creative for Meta Ads"""
    id: int  # 1 or 2
    imageUrl: Optional[str] = None
    primaryText: str
    headline: str
    description: str
    imageBrief: Optional[ImageBrief] = None  # Reference to source brief

class CampaignDraft(BaseModel):
    project_url: str
    analysis: AnalysisResult
    targeting: AdSetTargeting
    suggested_creatives: List[CreativeAsset]
    image_briefs: List[ImageBrief]
    ads: Optional[List[Ad]] = None  # 2 ready-to-use ads
    status: str = "DRAFT"


# =====================================
# REPLICA AD CREATIVE MODELS
# =====================================

class HeroData(BaseModel):
    """Extracted hero section data from landing page."""
    headline: str
    subheadline: Optional[str] = None
    background_color: Optional[str] = None  # Hex color of hero background
    background_url: Optional[str] = None
    background_screenshot: Optional[str] = None  # base64
    cta_text: str = "Learn More"
    cta_styles: Dict[str, Any] = {}


class FeatureItem(BaseModel):
    """Individual feature/benefit extracted from landing page."""
    title: str
    description: Optional[str] = None
    icon_url: Optional[str] = None
    screenshot: Optional[str] = None  # base64


class TestimonialItem(BaseModel):
    """Customer testimonial/review from landing page."""
    quote: str
    author: Optional[str] = None
    company: Optional[str] = None
    avatar_url: Optional[str] = None


class ReplicaData(BaseModel):
    """Complete extracted data for replica ad creatives."""
    url: str
    hero: HeroData
    logo_url: Optional[str] = None
    primary_color: str = "#ffffff"
    secondary_color: str = "#000000"
    accent_color: str = "#0066ff"
    font_family: str = "Inter"
    font_faces: List[str] = []
    css_variables: Dict[str, str] = {}
    features: List[FeatureItem] = []
    testimonials: List[TestimonialItem] = []
    product_screenshots: List[str] = []  # base64 list
    before_after: Optional[Dict[str, str]] = None  # {before: str, after: str}


class ReplicaCreative(BaseModel):
    """Single generated replica creative."""
    variation_type: str  # "hero", "features", "screenshot", "before_after", "testimonial"
    aspect_ratio: str  # "1:1", "4:5", "9:16"
    image_url: str  # S3 URL
    extracted_content: Dict[str, Any] = {}  # What was used from ReplicaData


class ReplicaResponse(BaseModel):
    """Response from replica creative generation."""
    url: str
    creatives: List[ReplicaCreative]
    replica_data: ReplicaData  # Full extracted data
