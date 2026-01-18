"""Background removal service using rembg."""
import asyncio
import io
import logging
from typing import Optional

from PIL import Image

logger = logging.getLogger(__name__)


class BackgroundRemover:
    """Remove backgrounds from images using rembg u2net model."""

    def __init__(self):
        self._session = None

    def _ensure_initialized(self):
        """Lazy-initialize rembg session."""
        if self._session:
            return
        try:
            from rembg import new_session
            self._session = new_session("u2net")
            logger.info("rembg session initialized with u2net model")
        except ImportError:
            raise ImportError(
                "rembg not installed. Run: pip install rembg onnxruntime"
            )

    async def remove_background(self, image_bytes: bytes) -> bytes:
        """
        Remove background from image, returning transparent PNG.

        Args:
            image_bytes: Input image bytes (PNG/JPEG)

        Returns:
            PNG bytes with transparent background
        """
        self._ensure_initialized()
        loop = asyncio.get_event_loop()

        def _process():
            from rembg import remove
            input_img = Image.open(io.BytesIO(image_bytes))
            output_img = remove(
                input_img,
                session=self._session,
                alpha_matting=True,
                alpha_matting_foreground_threshold=240,
                alpha_matting_background_threshold=10,
            )
            buffer = io.BytesIO()
            output_img.save(buffer, format="PNG")
            buffer.seek(0)
            return buffer.getvalue()

        try:
            result = await loop.run_in_executor(None, _process)
            logger.info("Background removed successfully")
            return result
        except Exception as e:
            logger.error(f"Background removal failed: {e}")
            raise


_remover: Optional[BackgroundRemover] = None


def get_background_remover() -> BackgroundRemover:
    """Get singleton BackgroundRemover instance."""
    global _remover
    if _remover is None:
        _remover = BackgroundRemover()
    return _remover
