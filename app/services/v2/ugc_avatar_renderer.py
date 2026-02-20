"""
UGC Avatar Renderer — orchestrates HeyGen API to produce avatar videos.

Flow: generate script → submit to HeyGen → poll → download → optional S3 upload.
Surfaces quota errors so the frontend can prompt user action.
"""

import logging
import time
import uuid

from app.services.v2.heygen_client import (
    generate_video,
    poll_video_status,
    download_video,
    HeyGenError,
    HeyGenQuotaError,
    DEFAULT_VOICE_ID,
    pick_random_avatar,
)

logger = logging.getLogger(__name__)


class UGCAvatarResult:
    """Result of a talking head video render."""

    def __init__(
        self,
        video_bytes: bytes | None = None,
        asset_url: str | None = None,
        heygen_video_id: str | None = None,
        generation_time_ms: int = 0,
        error: str | None = None,
        quota_exceeded: bool = False,
    ):
        self.video_bytes = video_bytes
        self.asset_url = asset_url
        self.heygen_video_id = heygen_video_id
        self.generation_time_ms = generation_time_ms
        self.error = error
        self.quota_exceeded = quota_exceeded

    @property
    def success(self) -> bool:
        return self.video_bytes is not None and self.error is None


async def render_ugc_avatar(
    script: str,
    avatar_id: str | None = None,
    voice_id: str = DEFAULT_VOICE_ID,
    upload_to_s3: bool = False,
) -> UGCAvatarResult:
    """
    End-to-end UGC avatar video generation.

    Args:
        script: Text for the avatar to speak (~80 words, 30s).
        avatar_id: HeyGen avatar ID. None = random pick from catalog.
        voice_id: HeyGen voice ID.
        upload_to_s3: Whether to upload the resulting MP4 to S3.

    Returns:
        UGCAvatarResult with video bytes and metadata.
    """
    if avatar_id is None:
        avatar = pick_random_avatar()
        avatar_id = avatar.id
        logger.info(f"Picked avatar: {avatar.name} ({avatar.id[:8]}…)")

    start = time.time()

    # 1. Submit to HeyGen
    try:
        video_id = await generate_video(
            script=script,
            avatar_id=avatar_id,
            voice_id=voice_id,
        )
    except HeyGenQuotaError as e:
        logger.warning(f"HeyGen quota exceeded: {e}")
        return UGCAvatarResult(
            error=str(e),
            quota_exceeded=True,
        )
    except HeyGenError as e:
        logger.error(f"HeyGen generate failed: {e}")
        return UGCAvatarResult(error=str(e))

    # 2. Poll until complete
    try:
        status = await poll_video_status(video_id)
    except HeyGenError as e:
        logger.error(f"HeyGen poll failed: {e}")
        return UGCAvatarResult(
            heygen_video_id=video_id,
            error=str(e),
        )

    # 3. Download MP4
    try:
        video_bytes = await download_video(status["video_url"])
    except HeyGenError as e:
        logger.error(f"HeyGen download failed: {e}")
        return UGCAvatarResult(
            heygen_video_id=video_id,
            error=str(e),
        )

    gen_ms = int((time.time() - start) * 1000)

    # 4. Optional S3 upload
    asset_url = None
    if upload_to_s3:
        asset_url = await _upload_video_to_s3(video_bytes)

    return UGCAvatarResult(
        video_bytes=video_bytes,
        asset_url=asset_url,
        heygen_video_id=video_id,
        generation_time_ms=gen_ms,
    )


async def _upload_video_to_s3(video_bytes: bytes) -> str | None:
    """Upload MP4 to S3, return URL or None on failure."""
    try:
        from app.services.s3 import get_s3_service
        s3 = get_s3_service()
        filename = f"v2/ugc_avatar_{uuid.uuid4().hex[:8]}.mp4"
        result = s3.upload_image(video_bytes, "v2-videos", filename)
        if result.get("success"):
            return result["url"]
    except Exception as e:
        logger.warning(f"S3 video upload failed: {e}")
    return None
