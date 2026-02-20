"""
HeyGen API Client — async wrapper for V2 video generation API.

Handles: generate video → poll status → download MP4.
Free tier: limited credits. Surfaces quota errors for UI prompting.
"""

import asyncio
import logging
import random
from dataclasses import dataclass
from enum import Enum

import httpx

from app.config import get_settings

logger = logging.getLogger(__name__)

HEYGEN_BASE_URL = "https://api.heygen.com"
POLL_INTERVAL_SECONDS = 30
MAX_POLL_ATTEMPTS = 20  # 10 min max wait


class HeyGenError(Exception):
    """Base error for HeyGen API failures."""
    pass


class HeyGenQuotaError(HeyGenError):
    """Raised when HeyGen free tier quota is exceeded."""
    pass


class VideoStatus(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


# ── Avatar catalog ──────────────────────────────────────────────────


@dataclass(frozen=True)
class AvatarSpec:
    id: str
    name: str
    gender: str       # "female" | "male"
    age_group: str    # "young_adult" | "mid_age" | "senior"
    appearance: str   # free-text note


AVATAR_CATALOG: list[AvatarSpec] = [
    AvatarSpec("0b6fa6a34d9e4ee6ab8a2fb85c59f8d3", "Diana",  "female", "young_adult", "Black"),
    AvatarSpec("ad582f0d8b9e4341bd6cdf58602f4367", "Matt",    "male",   "young_adult", "White"),
    AvatarSpec("2849873c21bc4665bbaad267ee8a1949", "Morgan",  "female", "young_adult", "White"),
    AvatarSpec("1375223b2cc24ff0a21830fbf5cb45ba", "Henry",   "male",   "mid_age",     "White"),
    AvatarSpec("92327cef7b7b4fe2bce77a46d1f47ed9", "Milani",  "female", "young_adult", "White"),
    AvatarSpec("b51059cba76e4e65a5923e6a5368eb25", "Harper",  "female", "young_adult", "South European/Asian"),
    AvatarSpec("c51581dab1ab49b689356a8b7bde90d4", "Julia",   "female", "senior",      "White"),
]

AVATAR_BY_ID: dict[str, AvatarSpec] = {a.id: a for a in AVATAR_CATALOG}

DEFAULT_AVATAR_ID = AVATAR_CATALOG[0].id  # Diana
DEFAULT_VOICE_ID = "f8c69e517f424cafaecde32dde57096b"  # Allison - English


def pick_random_avatar() -> AvatarSpec:
    """Pick a random avatar from the catalog."""
    return random.choice(AVATAR_CATALOG)


def _get_headers() -> dict[str, str]:
    settings = get_settings()
    if not settings.heygen_api_key:
        raise HeyGenError("HEYGEN_API_KEY not configured")
    return {
        "X-Api-Key": settings.heygen_api_key,
        "Content-Type": "application/json",
    }


async def generate_video(
    script: str,
    avatar_id: str = DEFAULT_AVATAR_ID,
    voice_id: str = DEFAULT_VOICE_ID,
    width: int = 720,
    height: int = 720,
) -> str:
    """
    Submit a UGC avatar video generation request.

    Args:
        script: The text for the avatar to speak (~80 words / 30s).
        avatar_id: HeyGen stock avatar ID.
        voice_id: HeyGen voice ID.
        width: Video width in pixels.
        height: Video height in pixels.

    Returns:
        video_id for polling status.

    Raises:
        HeyGenQuotaError: Free tier quota exceeded.
        HeyGenError: API or network failure.
    """
    payload = {
        "video_inputs": [
            {
                "character": {
                    "type": "avatar",
                    "avatar_id": avatar_id,
                    "avatar_style": "normal",
                },
                "voice": {
                    "type": "text",
                    "input_text": script,
                    "voice_id": voice_id,
                    "speed": 1.0,
                },
            }
        ],
        "dimension": {"width": width, "height": height},
    }

    async with httpx.AsyncClient(timeout=30) as client:
        try:
            resp = await client.post(
                f"{HEYGEN_BASE_URL}/v2/video/generate",
                json=payload,
                headers=_get_headers(),
            )
        except httpx.RequestError as e:
            raise HeyGenError(f"Network error: {e}") from e

    data = resp.json()

    data_str = str(data).lower()
    if resp.status_code == 429 or "quota" in data_str or "insufficient_credit" in data_str:
        raise HeyGenQuotaError(
            "HeyGen credits exhausted. Add credits at https://app.heygen.com/settings/billing"
        )

    if resp.status_code != 200 or data.get("error"):
        raise HeyGenError(f"HeyGen generate failed: {data}")

    video_id = data.get("data", {}).get("video_id")
    if not video_id:
        raise HeyGenError(f"No video_id in response: {data}")

    logger.info(f"HeyGen video submitted: {video_id}")
    return video_id


async def poll_video_status(video_id: str) -> dict:
    """
    Poll HeyGen for video status until completed or failed.

    Returns:
        dict with 'status' and 'video_url' (when completed).

    Raises:
        HeyGenError: On failure or timeout.
    """
    headers = _get_headers()

    for attempt in range(MAX_POLL_ATTEMPTS):
        async with httpx.AsyncClient(timeout=30) as client:
            try:
                resp = await client.get(
                    f"{HEYGEN_BASE_URL}/v1/video_status.get",
                    params={"video_id": video_id},
                    headers=headers,
                )
            except httpx.RequestError as e:
                logger.warning(f"Poll attempt {attempt + 1} network error: {e}")
                await asyncio.sleep(POLL_INTERVAL_SECONDS)
                continue

        data = resp.json().get("data", {})
        status = data.get("status", "unknown")

        if status == VideoStatus.COMPLETED:
            video_url = data.get("video_url")
            if not video_url:
                raise HeyGenError(f"Completed but no video_url: {data}")
            logger.info(f"HeyGen video ready: {video_id}")
            return {"status": "completed", "video_url": video_url}

        if status == VideoStatus.FAILED:
            error_msg = data.get("error", "Unknown error")
            error_str = str(error_msg).lower()
            if "insufficient_credit" in error_str or "resolution_not_allowed" in error_str:
                raise HeyGenQuotaError(
                    "HeyGen credits/plan insufficient. Upgrade at https://app.heygen.com/settings/billing"
                )
            raise HeyGenError(f"HeyGen render failed: {error_msg}")

        logger.debug(f"HeyGen poll {attempt + 1}/{MAX_POLL_ATTEMPTS}: {status}")
        await asyncio.sleep(POLL_INTERVAL_SECONDS)

    raise HeyGenError(f"HeyGen video timed out after {MAX_POLL_ATTEMPTS * POLL_INTERVAL_SECONDS}s")


async def download_video(video_url: str) -> bytes:
    """
    Download the completed MP4 from HeyGen's CDN.

    Returns:
        Raw MP4 bytes.
    """
    async with httpx.AsyncClient(timeout=120) as client:
        try:
            resp = await client.get(video_url)
            resp.raise_for_status()
        except httpx.HTTPError as e:
            raise HeyGenError(f"Failed to download video: {e}") from e

    logger.info(f"Downloaded video: {len(resp.content)} bytes")
    return resp.content
