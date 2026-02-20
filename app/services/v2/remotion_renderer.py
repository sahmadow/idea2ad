"""
Remotion Renderer — async Python wrapper for server-side Remotion video rendering.

Calls `npx tsx remotion/src/render-api.ts` as a subprocess, passing props via
a temp JSON file and reading the rendered MP4 bytes from a temp output path.

Security: Uses create_subprocess_exec (not shell=True) to prevent injection.
All arguments are passed as list elements, not interpolated into a shell string.
"""

import asyncio
import json
import logging
import os
import tempfile
from pathlib import Path

logger = logging.getLogger(__name__)

# Path to the remotion project root (relative to repo root)
REMOTION_DIR = Path(__file__).resolve().parents[3] / "remotion"
RENDER_SCRIPT = REMOTION_DIR / "src" / "render-api.ts"

# Max render time before we kill the subprocess
RENDER_TIMEOUT_SECONDS = 120


class RemotionRenderError(Exception):
    """Raised when Remotion rendering fails."""


async def render_remotion_video(
    composition_id: str,
    props: dict,
) -> bytes:
    """
    Render a Remotion composition to MP4 and return the video bytes.

    Args:
        composition_id: Remotion composition ID (e.g. "BrandedStatic", "ServiceHero")
        props: Input props dict matching the composition's expected schema

    Returns:
        MP4 file bytes

    Raises:
        RemotionRenderError: on subprocess failure or timeout
    """
    props_file = None
    output_file = None

    try:
        # Write props to temp JSON file (avoids shell escaping issues)
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".json", delete=False
        ) as f:
            json.dump(props, f)
            props_file = f.name

        # Create temp output path for MP4
        fd, output_file = tempfile.mkstemp(suffix=".mp4")
        os.close(fd)

        logger.info(
            f"Rendering Remotion composition '{composition_id}' → {output_file}"
        )

        # Run Remotion CLI via create_subprocess_exec (no shell injection risk)
        proc = await asyncio.create_subprocess_exec(
            "npx", "tsx", str(RENDER_SCRIPT),
            composition_id, props_file, output_file,
            cwd=str(REMOTION_DIR),
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )

        try:
            stdout, stderr = await asyncio.wait_for(
                proc.communicate(), timeout=RENDER_TIMEOUT_SECONDS
            )
        except asyncio.TimeoutError:
            proc.kill()
            await proc.wait()
            raise RemotionRenderError(
                f"Remotion render timed out after {RENDER_TIMEOUT_SECONDS}s "
                f"for composition '{composition_id}'"
            )

        if proc.returncode != 0:
            stderr_text = stderr.decode("utf-8", errors="replace")[-2000:]
            raise RemotionRenderError(
                f"Remotion render failed (exit {proc.returncode}) "
                f"for '{composition_id}': {stderr_text}"
            )

        # Read rendered MP4 bytes
        mp4_path = Path(output_file)
        if not mp4_path.exists() or mp4_path.stat().st_size == 0:
            raise RemotionRenderError(
                f"Remotion render produced no output for '{composition_id}'"
            )

        video_bytes = mp4_path.read_bytes()
        logger.info(
            f"Remotion render complete: '{composition_id}' "
            f"({len(video_bytes)} bytes)"
        )
        return video_bytes

    finally:
        # Cleanup temp files
        for p in (props_file, output_file):
            if p:
                try:
                    os.unlink(p)
                except OSError:
                    pass
