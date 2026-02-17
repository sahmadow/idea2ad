"""
Renderer Client — async HTTP client for the Node.js Fabric.js renderer microservice.

Calls /render and /render/batch endpoints to convert Fabric.js canvas JSON into images.
"""

import logging
import os
from typing import Optional

import httpx

logger = logging.getLogger(__name__)

# Config from env
RENDERER_URL = os.environ.get("RENDERER_URL", "http://localhost:3100")
RENDERER_API_KEY = os.environ.get("RENDERER_API_KEY", "")
RENDER_TIMEOUT = 30.0  # seconds per render

_client: Optional[httpx.AsyncClient] = None


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


async def render_canvas(
    canvas_json: dict,
    width: int = 1080,
    height: int = 1080,
    fmt: str = "png",
    quality: int = 90,
) -> bytes:
    """
    Render a single Fabric.js canvas JSON to image bytes.

    Args:
        canvas_json: Fabric.js JSON (the output of canvas.toJSON())
        width: Canvas width in pixels
        height: Canvas height in pixels
        fmt: Output format ("png" or "jpeg")
        quality: JPEG quality (ignored for PNG)

    Returns:
        Raw image bytes (PNG or JPEG)

    Raises:
        httpx.HTTPStatusError: On renderer HTTP errors
        httpx.ConnectError: If renderer is unreachable
    """
    client = _get_client()
    resp = await client.post(
        "/render",
        json={
            "canvas_json": canvas_json,
            "width": width,
            "height": height,
            "format": fmt,
            "quality": quality,
        },
    )
    resp.raise_for_status()
    return resp.content


async def render_batch(
    items: list[dict],
) -> list[dict]:
    """
    Render multiple canvases in one request.

    Args:
        items: List of dicts with keys:
            id, canvas_json, width?, height?, format?, quality?

    Returns:
        List of dicts with keys:
            id, success, image_base64 (str|None), format, error (str|None)
    """
    client = _get_client()
    resp = await client.post(
        "/render/batch",
        json={"items": items},
        timeout=RENDER_TIMEOUT * len(items),
    )
    resp.raise_for_status()
    data = resp.json()
    return data.get("results", [])


async def health_check() -> bool:
    """Check if renderer service is reachable."""
    try:
        client = _get_client()
        resp = await client.get("/health")
        return resp.status_code == 200
    except Exception:
        return False
