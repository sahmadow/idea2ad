"""List available HeyGen avatars and voices."""

import asyncio
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

env_path = Path(__file__).resolve().parents[1] / ".env"
if env_path.exists():
    for line in env_path.read_text().splitlines():
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            key, _, val = line.partition("=")
            os.environ.setdefault(key.strip(), val.strip())

import httpx

API_KEY = os.environ["HEYGEN_API_KEY"]
HEADERS = {"X-Api-Key": API_KEY, "Content-Type": "application/json"}


async def main():
    async with httpx.AsyncClient(timeout=30) as client:
        # List avatars
        print("=== AVATARS ===")
        resp = await client.get(
            "https://api.heygen.com/v2/avatars",
            headers=HEADERS,
        )
        data = resp.json()
        avatars = data.get("data", {}).get("avatars", [])
        for a in avatars[:20]:
            print(f"  {a.get('avatar_id', 'N/A'):40s} | {a.get('avatar_name', 'N/A')}")

        # List voices
        print("\n=== VOICES ===")
        resp = await client.get(
            "https://api.heygen.com/v2/voices",
            headers=HEADERS,
        )
        data = resp.json()
        voices = data.get("data", {}).get("voices", [])
        for v in voices[:20]:
            print(f"  {v.get('voice_id', 'N/A'):40s} | {v.get('display_name', v.get('name', 'N/A')):20s} | {v.get('language', 'N/A')}")


if __name__ == "__main__":
    asyncio.run(main())
