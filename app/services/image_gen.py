import asyncio
import io
import json
import logging
import os
import tempfile
from typing import Optional
from PIL import Image

from app.config import get_settings

logger = logging.getLogger(__name__)


def _setup_gcp_credentials():
    """Setup GCP credentials from env var if needed"""
    # If credentials file already set and exists, use it
    creds_path = os.environ.get("GOOGLE_APPLICATION_CREDENTIALS")
    if creds_path and os.path.exists(creds_path):
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

    async def generate_ad_image(
        self,
        visual_description: str,
        styling_notes: str,
        approach: str = "product-focused"
    ) -> bytes:
        """
        Generate ad image from image brief

        Args:
            visual_description: Detailed visual description
            styling_notes: Brand styling information
            approach: "product-focused", "lifestyle", or "problem-solution"

        Returns:
            PNG image bytes
        """
        # Construct optimized prompt for ad images
        prompt = f"""Professional advertising photography, {approach} style.

{visual_description}

Style: {styling_notes}

Requirements:
- High quality, professional lighting
- Clean composition suitable for Meta ads
- Minimal text area reserved for overlays
- Mobile-optimized focal point
- Brand-consistent colors"""

        # Use 1:1 for feed ads (most versatile)
        return await self.generate_image(
            prompt=prompt,
            aspect_ratio="1:1",
            negative_prompt="blurry, low quality, text, watermark, logo, amateur"
        )


# Singleton instance
_generator: Optional[ImageGenerator] = None


def get_image_generator() -> ImageGenerator:
    """Get singleton ImageGenerator instance"""
    global _generator
    if _generator is None:
        _generator = ImageGenerator()
    return _generator
