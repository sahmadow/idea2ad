"""
Image Editor — Gemini-powered image editing via prompt.

Takes a source image + text prompt, returns an edited image.
Uses Gemini 2.0 Flash with image generation capabilities.
"""

import logging
import os
from pathlib import Path

from google import genai
from google.genai import types

logger = logging.getLogger(__name__)

IMAGE_EDIT_MODEL = "gemini-2.5-flash-image"


def _get_client() -> genai.Client:
    api_key = os.environ.get("GOOGLE_API_KEY")
    if not api_key:
        raise ValueError("GOOGLE_API_KEY not set")
    return genai.Client(api_key=api_key)


async def edit_image(
    image_bytes: bytes,
    prompt: str,
    mime_type: str = "image/png",
) -> bytes:
    """Edit an image using Gemini with a text prompt.

    Args:
        image_bytes: Source image bytes
        prompt: Edit instruction (e.g. "Change background to Paris")
        mime_type: MIME type of the input image

    Returns:
        Edited image bytes (PNG)
    """
    client = _get_client()

    contents = [
        types.Part.from_bytes(data=image_bytes, mime_type=mime_type),
        prompt,
    ]

    result = await client.aio.models.generate_content(
        model=IMAGE_EDIT_MODEL,
        contents=contents,
        config=types.GenerateContentConfig(
            response_modalities=["IMAGE", "TEXT"],
        ),
    )

    # Extract image from response
    for part in result.candidates[0].content.parts:
        if part.inline_data and part.inline_data.mime_type.startswith("image/"):
            logger.info(f"Image edited: {len(part.inline_data.data) // 1024}KB")
            return part.inline_data.data

    raise RuntimeError("Gemini returned no image in response")


async def edit_image_from_file(
    image_path: str,
    prompt: str,
) -> bytes:
    """Convenience: edit from a local file path."""
    path = Path(image_path)
    if not path.is_file():
        raise FileNotFoundError(f"Image not found: {image_path}")

    import mimetypes
    mime = mimetypes.guess_type(str(path))[0] or "image/png"
    return await edit_image(path.read_bytes(), prompt, mime)
