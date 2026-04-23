"""
AtCoder — uses the public AtCoder Problems API (no auth required).
API: https://kenkoooo.com/atcoder/resources/contests.json
"""

import logging
from datetime import datetime, timezone
from typing import List

import aiohttp

from src.models import Contest
from src.platforms.base import BasePlatform

log = logging.getLogger(__name__)

API_URL = "https://kenkoooo.com/atcoder/resources/contests.json"


class AtCoderClient(BasePlatform):
    name = "AtCoder"
    color = 0x222222          # AtCoder dark
    icon_url = "https://img.atcoder.jp/assets/favicon.png"

    async def fetch(self) -> List[Contest]:
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(API_URL, timeout=aiohttp.ClientTimeout(total=10)) as resp:
                    data = await resp.json(content_type=None)
        except Exception as e:
            log.error(f"[AtCoder] Failed to fetch contests: {e}")
            return []

        now = datetime.now(timezone.utc).timestamp()
        contests = []

        for c in data:
            start_ts = c.get("start_epoch_second")
            duration_s = c.get("duration_second", 0)
            if start_ts is None:
                continue

            # Only upcoming contests within 14 days
            if start_ts <= now or start_ts - now > 14 * 86400:
                continue

            contest_id = c.get("id", "")
            contests.append(
                Contest(
                    id=f"atcoder-{contest_id}",
                    platform=self.name,
                    name=c.get("title", "Unknown Contest"),
                    url=f"https://atcoder.jp/contests/{contest_id}",
                    start_time=datetime.fromtimestamp(start_ts, tz=timezone.utc),
                    duration_seconds=duration_s,
                    color=self.color,
                    icon_url=self.icon_url,
                )
            )

        log.info(f"[AtCoder] {len(contests)} upcoming contest(s) found")
        return contests
