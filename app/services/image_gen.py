import asyncio
import io
import logging
import os
import tempfile
from typing import List, Optional, Dict, Any

from app.config import get_settings
from app.services.color_utils import hex_to_color_name

logger = logging.getLogger(__name__)


def _setup_gcp_credentials():
    """Setup GCP credentials from env var or settings"""
    from app.config import get_settings
    settings = get_settings()

    # If credentials file already set in env and exists, use it
    creds_path = os.environ.get("GOOGLE_APPLICATION_CREDENTIALS")
    if creds_path and os.path.exists(creds_path):
        return

    # Check settings for credentials path (loaded from .env by pydantic)
    if settings.google_application_credentials and os.path.exists(settings.google_application_credentials):
        os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = settings.google_application_credentials
        logger.info(f"GCP credentials set from settings: {settings.google_application_credentials}")
        return

    # Check for JSON credentials in env var
    creds_json = os.environ.get("GOOGLE_APPLICATION_CREDENTIALS_JSON")
    if creds_json:
        # Write to temp file and set path
        fd, path = tempfile.mkstemp(suffix=".json")
        with os.fdopen(fd, "w") as f:
            f.write(creds_json)
        os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = path
        logger.info(f"GCP credentials written to {path}")


class ImageGenerator:
    """Image generation service using Google Vertex AI Imagen 3.0"""

    def __init__(self):
        self._initialized = False
        self._model = None

    def _ensure_initialized(self):
        """Lazy initialization of Vertex AI"""
        if self._initialized:
            return

        settings = get_settings()

        if not settings.google_cloud_project:
            raise ValueError("GOOGLE_CLOUD_PROJECT not configured")

        # Setup credentials from env var if needed
        _setup_gcp_credentials()

        try:
            import vertexai
            from vertexai.preview.vision_models import ImageGenerationModel

            vertexai.init(project=settings.google_cloud_project)
            self._model = ImageGenerationModel.from_pretrained("imagen-3.0-generate-001")
            self._initialized = True
            logger.info("Vertex AI Imagen initialized successfully")

        except ImportError:
            raise ImportError(
                "google-cloud-aiplatform not installed. "
                "Run: pip install google-cloud-aiplatform"
            )
        except Exception as e:
            logger.error(f"Failed to initialize Vertex AI: {e}")
            raise

    async def generate_image(
        self,
        prompt: str,
        aspect_ratio: str = "1:1",
        negative_prompt: Optional[str] = None
    ) -> bytes:
        """
        Generate image using Vertex AI Imagen 3.0

        Args:
            prompt: Text prompt describing the image
            aspect_ratio: "1:1", "16:9", "9:16", "4:3", "3:4"
            negative_prompt: Things to avoid in the image

        Returns:
            PNG image bytes
        """
        self._ensure_initialized()

        try:
            loop = asyncio.get_event_loop()

            def _generate():
                response = self._model.generate_images(
                    prompt=prompt,
                    number_of_images=1,
                    aspect_ratio=aspect_ratio,
                    safety_filter_level="block_some",
                    person_generation="allow_adult",
                    negative_prompt=negative_prompt,
                )
                return response

            response = await loop.run_in_executor(None, _generate)

            if not response.images:
                raise ValueError("No image generated")

            # Convert PIL Image to bytes
            img = response.images[0]._pil_image
            buffer = io.BytesIO()
            img.save(buffer, format="PNG", optimize=True)
            buffer.seek(0)

            logger.info(f"Image generated successfully for prompt: {prompt[:50]}...")
            return buffer.getvalue()

        except Exception as e:
            logger.error(f"Image generation failed: {e}")
            raise

    async def generate_isolated_product(
        self,
        product_prompt: str,
        styling_guide: Optional[Dict[str, Any]] = None,
    ) -> bytes:
        """
        Generate isolated product image on white background for easy removal.

        Args:
            product_prompt: Description of product to generate
            styling_guide: Brand styling for color consistency

        Returns:
            PNG image bytes with solid white background
        """
        self._ensure_initialized()

        prompt = f"""Professional product photography, isolated product shot.

SUBJECT: {product_prompt}

REQUIREMENTS:
- Single product centered, solid white background (#ffffff)
- Professional studio lighting, sharp focus
- No text, no watermarks, no other objects
- Product fills 70-80% of frame
- High contrast edges for easy background removal

STYLE: Commercial product photography, 4K quality"""

        return await self.generate_image(
            prompt=prompt,
            aspect_ratio="1:1",
            negative_prompt="busy background, multiple objects, text, shadows, gradient, patterns, watermark"
        )

    def _build_color_precise_prompt(
        self,
        visual_description: str,
        styling_notes: str,
        approach: str,
        styling_guide: Optional[Dict[str, Any]] = None,
        design_tokens: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Build a color-precise prompt for Imagen with explicit hex codes and color names.

        Args:
            visual_description: Scene description
            styling_notes: Brand styling info
            approach: Creative approach
            styling_guide: StylingGuide with colors, fonts, mood
            design_tokens: Design tokens (gradients, shadows, etc.)

        Returns:
            Color-optimized prompt string
        """
        # Extract colors from styling guide
        primary_hex = "#ffffff"
        accent_hex = "#000000"
        primary_name = "neutral"
        accent_name = "dark"
        mood = "professional"
        design_style = "modern"

        if styling_guide:
            primary_colors = styling_guide.get("primary_colors", [])
            secondary_colors = styling_guide.get("secondary_colors", [])

            if primary_colors:
                primary_hex = primary_colors[0]
                primary_name = hex_to_color_name(primary_hex)

            if len(primary_colors) > 1:
                accent_hex = primary_colors[1]
                accent_name = hex_to_color_name(accent_hex)
            elif secondary_colors:
                accent_hex = secondary_colors[0]
                accent_name = hex_to_color_name(accent_hex)

            mood = styling_guide.get("mood", "professional")
            design_style = styling_guide.get("design_style", "modern")

        # Build gradient instructions if present
        gradient_instruction = ""
        if design_tokens and design_tokens.get("gradients"):
            gradients = design_tokens["gradients"]
            if gradients:
                grad = gradients[0]
                grad_colors = grad.get("colors", [])
                if len(grad_colors) >= 2:
                    gradient_instruction = f"Use subtle gradient from {grad_colors[0]} to {grad_colors[1]} for background depth."

        # Build the color-precise prompt
        prompt = f"""Professional {approach} advertising image.

SCENE: {visual_description}

MANDATORY COLOR PALETTE - EXACT COLORS ONLY:
- Primary/Background: {primary_hex} ({primary_name})
- Accent highlights: {accent_hex} ({accent_name})

COLOR REQUIREMENTS:
- The dominant background color MUST be {primary_hex} ({primary_name})
- All accent elements MUST use {accent_hex} ({accent_name})
- Do NOT introduce any colors outside this palette
- Maintain {mood} mood with these exact colors
{gradient_instruction}

STYLE: {design_style}
- {styling_notes}

COMPOSITION:
- Mobile-optimized (1:1 aspect ratio)
- Clean, minimal, professional
- Reserve bottom 20% for text overlay (keep simple/clear background)
- Strong focal point in upper 2/3

QUALITY: Professional advertising photography, studio lighting, 4K quality"""

        return prompt

    async def generate_person_image(
        self,
        buyer_persona: Dict[str, Any],
        styling_guide: Optional[Dict[str, Any]] = None,
    ) -> bytes:
        """
        Generate a person image for SaaS person-centric ads based on buyer persona.

        Args:
            buyer_persona: Dict with age_range, gender, profession, etc.
            styling_guide: Brand styling for aesthetic consistency

        Returns:
            PNG image bytes
        """
        self._ensure_initialized()

        # Extract persona details with defaults
        age_range = buyer_persona.get("age_range", [30, 45])
        gender = buyer_persona.get("gender", "All")
        profession = buyer_persona.get("profession", "professional")

        # Calculate target age
        if isinstance(age_range, list) and len(age_range) >= 2:
            target_age = (age_range[0] + age_range[1]) // 2
        else:
            target_age = 35

        # Map gender
        if gender == "All" or gender == "all":
            # Alternate or pick one
            gender_desc = "professional"
        elif gender.lower() in ["male", "men"]:
            gender_desc = "man"
        elif gender.lower() in ["female", "women"]:
            gender_desc = "woman"
        else:
            gender_desc = "person"

        # Get mood from styling guide
        mood = "professional"
        if styling_guide:
            mood = styling_guide.get("mood", "professional")

        prompt = f"""Professional portrait photography for business advertising.

SUBJECT: A confident, happy {target_age}-year-old {gender_desc}, {profession}

REQUIREMENTS:
- Professional business casual attire
- Genuine, warm smile showing confidence and success
- Clean, minimal background (soft gray or white studio)
- Chest-up or waist-up framing
- Professional studio lighting
- High-end commercial photography style
- Diverse, authentic representation
- {mood} mood and energy

STYLE: Modern corporate photography, lifestyle brand imagery
HIGH QUALITY: 4K resolution, sharp focus, professional retouching"""

        return await self.generate_image(
            prompt=prompt,
            aspect_ratio="1:1",
            negative_prompt="awkward pose, fake smile, busy background, unflattering angle, amateur, low quality, distorted features"
        )

    async def generate_ad_image(
        self,
        visual_description: str,
        styling_notes: str,
        approach: str = "product-focused",
        styling_guide: Optional[Dict[str, Any]] = None,
        design_tokens: Optional[Dict[str, Any]] = None,
        text_overlays: Optional[List[Dict[str, Any]]] = None,
        apply_text_overlays: bool = True
    ) -> bytes:
        """
        Generate ad image from image brief with brand-consistent colors.

        Args:
            visual_description: Detailed visual description
            styling_notes: Brand styling information
            approach: "product-focused", "lifestyle", or "problem-solution"
            styling_guide: StylingGuide dict with colors, fonts, mood
            design_tokens: Design tokens (gradients, shadows, border-radius)
            text_overlays: List of TextOverlay dicts to apply
            apply_text_overlays: Whether to composite text overlays

        Returns:
            PNG image bytes
        """
        # Build color-precise prompt if styling guide provided
        if styling_guide:
            prompt = self._build_color_precise_prompt(
                visual_description=visual_description,
                styling_notes=styling_notes,
                approach=approach,
                styling_guide=styling_guide,
                design_tokens=design_tokens
            )
        else:
            # Fallback to legacy prompt
            prompt = f"""Professional advertising photography, {approach} style.

{visual_description}

Style: {styling_notes}

Requirements:
- High quality, professional lighting
- Clean composition suitable for Meta ads
- Minimal text area reserved for overlays
- Mobile-optimized focal point
- Brand-consistent colors"""

        # Generate base image
        base_image = await self.generate_image(
            prompt=prompt,
            aspect_ratio="1:1",
            negative_prompt="blurry, low quality, text, watermark, logo, amateur, words, letters"
        )

        # Apply text overlays if provided and enabled
        if apply_text_overlays and text_overlays and styling_guide:
            try:
                from app.services.image_compositor import get_image_compositor
                from app.models import TextOverlay as TextOverlayModel

                compositor = get_image_compositor()

                # Convert dict overlays to TextOverlay models
                overlay_models = []
                for overlay in text_overlays:
                    if isinstance(overlay, dict):
                        overlay_models.append(TextOverlayModel(**overlay))
                    else:
                        overlay_models.append(overlay)

                # Get font families from styling guide
                font_families = styling_guide.get("font_families", ["Inter", "Roboto"])

                # Composite text overlays
                final_image = await compositor.composite_text_overlays(
                    base_image=base_image,
                    text_overlays=overlay_models,
                    font_families=font_families
                )

                logger.info(f"Applied {len(overlay_models)} text overlays to image")
                return final_image

            except Exception as e:
                logger.warning(f"Failed to apply text overlays, returning base image: {e}")
                return base_image

        return base_image


# Singleton instance
_generator: Optional[ImageGenerator] = None


def get_image_generator() -> ImageGenerator:
    """Get singleton ImageGenerator instance"""
    global _generator
    if _generator is None:
        _generator = ImageGenerator()
    return _generator
