"""Generate a 30s UGC avatar sample video for peec.ai."""

import asyncio
import os
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

# Load .env manually (no dotenv dependency needed)
env_path = Path(__file__).resolve().parents[1] / ".env"
if env_path.exists():
    for line in env_path.read_text().splitlines():
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            key, _, val = line.partition("=")
            os.environ.setdefault(key.strip(), val.strip())

from app.services.v2.heygen_client import (
    generate_video,
    poll_video_status,
    download_video,
)

SCRIPT = (
    "Stop scrolling — if you're still making ads by hand, you need to hear this. "
    "peec.ai takes any landing page and turns it into scroll-stopping ad creatives "
    "in seconds. Not templates. Not generic stuff. It actually scrapes your site, "
    "pulls your brand colors, your copy, your vibe — and builds ads that look like "
    "your brand. People are already switching from agencies and saving hours every week. "
    "Seriously, just try it. The link is right below this video."
)

OUTPUT = Path(__file__).resolve().parents[1] / "scripts" / "output" / "ugc_avatar_peecai.mp4"


async def main():
    print(f"Script ({len(SCRIPT.split())} words):")
    print(SCRIPT)
    print()

    print("Submitting to HeyGen...")
    video_id = await generate_video(script=SCRIPT, width=720, height=720)
    print(f"Video ID: {video_id}")

    print("Polling for completion (this takes 2-8 min)...")
    status = await poll_video_status(video_id)
    print(f"Status: {status['status']}")

    print("Downloading MP4...")
    video_bytes = await download_video(status["video_url"])

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_bytes(video_bytes)
    print(f"Done! Output: {OUTPUT} ({len(video_bytes) / 1024:.0f} KB)")


if __name__ == "__main__":
    asyncio.run(main())
