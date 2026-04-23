"""
Codeforces — uses the official public API (no auth required).
API docs: https://codeforces.com/apiHelp/methods#contest.list
"""

import logging
from datetime import datetime, timezone
from typing import List

import aiohttp

from src.models import Contest
from src.platforms.base import BasePlatform

log = logging.getLogger(__name__)

API_URL = "https://codeforces.com/api/contest.list?gym=false"


class CodeforcesClient(BasePlatform):
    name = "Codeforces"
    color = 0x1F8ACB          # Codeforces blue
    icon_url = "https://codeforces.org/s/0/favicon-32x32.png"

    async def fetch(self) -> List[Contest]:
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(API_URL, timeout=aiohttp.ClientTimeout(total=10)) as resp:
                    data = await resp.json()
        except Exception as e:
            log.error(f"[Codeforces] Failed to fetch contests: {e}")
            return []

        if data.get("status") != "OK":
            log.error(f"[Codeforces] API returned non-OK status: {data.get('comment')}")
            return []

        contests = []
        now = datetime.now(timezone.utc).timestamp()

        for c in data.get("result", []):
            # phase BEFORE = not started yet
            if c.get("phase") != "BEFORE":
                continue

            start_ts = c.get("startTimeSeconds")
            duration_s = c.get("durationSeconds", 0)
            if start_ts is None:
                continue

            # skip contests starting more than 14 days away (noise reduction)
            if start_ts - now > 14 * 86400:
                continue

            contest_id = str(c["id"])
            contests.append(
                Contest(
                    id=f"cf-{contest_id}",
                    platform=self.name,
                    name=c["name"],
                    url=f"https://codeforces.com/contest/{contest_id}",
                    start_time=datetime.fromtimestamp(start_ts, tz=timezone.utc),
                    duration_seconds=duration_s,
                    color=self.color,
                    icon_url=self.icon_url,
                )
            )

        log.info(f"[Codeforces] {len(contests)} upcoming contest(s) found")
        return contests
