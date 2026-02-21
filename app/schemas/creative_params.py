"""
CreativeParameters — the single data object that feeds all downstream creative generation.

Combines scraper output + LLM analysis into a validated, structured parameter set.
Every ad type template reads from this object.
"""

from pydantic import BaseModel, Field
from typing import Literal


class BrandColors(BaseModel):
    """Brand color palette extracted from landing page CSS."""
    primary: str = "#1A365D"  # hex
    secondary: str | None = None
    accent: str | None = None


class PersonaDemographics(BaseModel):
    """Targeting demographics derived from persona analysis."""
    age_min: int = 18
    age_max: int = 65
    gender_skew: Literal["neutral", "male", "female"] = "neutral"
    locations: list[str] | None = None  # country codes


class TargetPersona(BaseModel):
    """Buyer persona with psychographics and visual scene descriptions."""
    label: str  # "Side sleeper with chronic neck pain, 35-55"
    demographics: PersonaDemographics = PersonaDemographics()
    psychographics: list[str] = []  # ["Values quality over price"]
    scenes: list[str] = []  # Visual scene descriptions for this persona
    language_style: str = "Conversational, benefit-focused"
    specific_pains: list[str] = []
    specific_desires: list[str] = []


class CreativeParameters(BaseModel):
    """
    All extracted/inferred parameters for creative generation.

    This is the single source of truth that every ad type template reads from.
    Fields are populated by the parameter extraction pipeline (scraper + Gemini).
    """

    # --- Source ---
    source_url: str | None = None
    source_description: str | None = None

    # --- Product Core ---
    product_name: str
    product_category: str = "General"
    product_description_short: str = ""  # <15 words
    price: str | None = None
    currency: str | None = None

    # --- Brand Identity ---
    brand_name: str = ""
    brand_colors: BrandColors = BrandColors()
    brand_fonts: list[str] = Field(default_factory=lambda: ["Inter"])
    brand_logo_url: str | None = None

    # --- Images ---
    hero_image_url: str | None = None
    product_images: list[str] = []
    # original url -> processed (bg-removed) url
    processed_images: dict[str, str] = {}

    # --- Headlines ---
    headline: str = ""
    subheadline: str | None = None

    # --- Value Messaging ---
    key_benefit: str = ""  # single most important benefit
    key_differentiator: str = ""  # what makes it unique
    value_props: list[str] = []  # 3-5 value propositions

    # --- Pain / Desire ---
    customer_pains: list[str] = []  # 3-5 pain points
    customer_desires: list[str] = []  # 3-5 desired outcomes
    objections: list[str] = []

    # --- Social Proof ---
    social_proof: str | None = None  # "12,847 5-star reviews"
    testimonials: list[str] = []

    # --- CTA ---
    cta_text: str = "Shop Now"
    destination_url: str = ""

    # --- Personas ---
    persona_primary: TargetPersona | None = None
    persona_secondary: TargetPersona | None = None

    # --- Visual Scenes (LLM-generated descriptions for image gen) ---
    scene_problem: str | None = None  # "Person rubbing stiff neck at desk"
    scene_solution: str | None = None  # "Person sleeping peacefully"
    scene_lifestyle: str | None = None  # "Bright bedroom, morning light"

    # --- Business Type ---
    business_type: Literal["ecommerce", "saas", "service"] = "ecommerce"

    # --- Language & Geo ---
    language: str = "en"  # ISO 639-1
    target_countries: list[str] = Field(default_factory=lambda: ["US"])

    # --- Tone & Urgency ---
    tone: Literal["premium", "casual", "clinical", "playful", "urgent"] = "casual"
    urgency_hooks: list[str] = []

    def has_enough_value_props(self, minimum: int = 3) -> bool:
        return len(self.value_props) >= minimum

    def has_social_proof(self) -> bool:
        return bool(self.social_proof) or len(self.testimonials) > 0

    def has_scene_problem(self) -> bool:
        return bool(self.scene_problem)

    def has_pains_and_desires(self) -> bool:
        return len(self.customer_pains) > 0 and len(self.customer_desires) > 0

    def has_enough_product_images(self, minimum: int = 3) -> bool:
        return len(self.product_images) >= minimum

    def is_saas(self) -> bool:
        return self.business_type == "saas"

    @property
    def verified_purchase_label(self) -> str:
        if self.business_type == "saas":
            return "Verified User"
        return "Verified Purchase"
