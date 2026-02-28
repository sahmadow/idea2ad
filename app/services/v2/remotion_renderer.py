"""
Remotion Renderer — async HTTP client for video rendering via the renderer microservice.

Calls POST /render/video on the Node.js renderer, which bundles and renders
Remotion compositions server-side. Returns MP4 bytes.
"""

import base64
import logging
import os
from typing import Optional

import httpx

logger = logging.getLogger(__name__)

# Config from env (same vars as renderer_client.py)
RENDERER_URL = os.environ.get("RENDERER_URL", "http://localhost:3100")
RENDERER_API_KEY = os.environ.get("RENDERER_API_KEY", "")
RENDER_TIMEOUT = 120.0  # seconds — video renders are slower than image renders

_client: Optional[httpx.AsyncClient] = None


class RemotionRenderError(Exception):
    """Raised when Remotion rendering fails."""


def _get_client() -> httpx.AsyncClient:
    global _client
    if _client is None:
        headers = {}
        if RENDERER_API_KEY:
            headers["X-API-Key"] = RENDERER_API_KEY
        _client = httpx.AsyncClient(
            base_url=RENDERER_URL,
            timeout=RENDER_TIMEOUT,
            headers=headers,
        )
    return _client


async def render_remotion_video(
    composition_id: str,
    props: dict,
) -> bytes:
    """
    Render a Remotion composition to MP4 via the renderer microservice.

    Args:
        composition_id: Remotion composition ID (e.g. "BrandedStatic", "ServiceHero")
        props: Input props dict matching the composition's expected schema

    Returns:
        MP4 file bytes

    Raises:
        RemotionRenderError: on HTTP or render failure
    """
    client = _get_client()

    logger.info(f"Requesting video render: '{composition_id}'")

    try:
        resp = await client.post(
            "/render/video",
            json={
                "composition_id": composition_id,
                "input_props": props,
            },
        )
        resp.raise_for_status()
    except httpx.TimeoutException:
        raise RemotionRenderError(
            f"Video render timed out after {RENDER_TIMEOUT}s "
            f"for composition '{composition_id}'"
        )
    except httpx.HTTPStatusError as e:
        detail = ""
        try:
            detail = e.response.json().get("detail", "")
        except Exception:
            detail = e.response.text[:500]
        raise RemotionRenderError(
            f"Video render failed (HTTP {e.response.status_code}) "
            f"for '{composition_id}': {detail}"
        )
    except httpx.ConnectError:
        raise RemotionRenderError(
            f"Cannot reach renderer at {RENDERER_URL} — is it running?"
        )

    data = resp.json()
    if not data.get("success"):
        raise RemotionRenderError(
            f"Video render failed for '{composition_id}': "
            f"{data.get('detail', 'unknown error')}"
        )

    video_base64 = data.get("video_base64")
    if not video_base64:
        raise RemotionRenderError(
            f"Renderer returned no video data for '{composition_id}'"
        )

    video_bytes = base64.b64decode(video_base64)
    logger.info(
        f"Video render complete: '{composition_id}' ({len(video_bytes)} bytes)"
    )
    return video_bytes
