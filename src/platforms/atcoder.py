"""
AtCoder — uses clist.by API (free, requires API key).
Sign up at https://clist.by to get a free API key.
Add CLIST_USERNAME and CLIST_API_KEY to your .env and GitHub secrets.
"""

import logging
from datetime import datetime, timezone
from typing import List
import os

import aiohttp

from src.models import Contest
from src.platforms.base import BasePlatform

log = logging.getLogger(__name__)

API_URL = "https://clist.by/api/v4/contest/"


class AtCoderClient(BasePlatform):
    name = "AtCoder"
    color = 0x222222
    icon_url = "https://img.atcoder.jp/assets/favicon.png"

    async def fetch(self) -> List[Contest]:
        api_key = os.environ.get("CLIST_API_KEY", "").strip()
        username = os.environ.get("CLIST_USERNAME", "").strip()
        if not api_key or not username:
            log.warning("[AtCoder] CLIST_API_KEY or CLIST_USERNAME not set, skipping.")
            return []

        now = datetime.now(timezone.utc)
        params = {
            "resource": "atcoder.jp",
            "order_by": "start",
            "limit": 10,
            "start__gt": now.strftime("%Y-%m-%dT%H:%M:%S"),
        }
        headers = {"Authorization": f"ApiKey {username}:{api_key}"}

        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    API_URL,
                    params=params,
                    headers=headers,
                    timeout=aiohttp.ClientTimeout(total=15),
                ) as resp:
                    data = await resp.json(content_type=None)
                    if resp.status != 200:
                        log.error(f"[AtCoder] clist.by returned HTTP {resp.status}: {data}")
                        return []
        except Exception as e:
            log.error(f"[AtCoder] Failed to fetch contests: {e}")
            return []

        if not data or "objects" not in data:
            log.error(f"[AtCoder] Unexpected response: {data}")
            return []

        contests = []
        for c in data.get("objects", []):
            try:
                start_time = datetime.fromisoformat(
                    c["start"].replace("Z", "+00:00")
                ).astimezone(timezone.utc)
                end_time = datetime.fromisoformat(
                    c["end"].replace("Z", "+00:00")
                ).astimezone(timezone.utc)
            except Exception as e:
                log.warning(f"[AtCoder] Failed to parse dates for {c}: {e}")
                continue

            if start_time <= now:
                continue
            if (start_time - now).days > 14:
                continue

            duration_s = int((end_time - start_time).total_seconds())

            contests.append(
                Contest(
                    id=f"atcoder-{c.get('id')}",
                    platform=self.name,
                    name=c.get("event", "Unknown Contest"),
                    url=c.get("href", "https://atcoder.jp/contests/"),
                    start_time=start_time,
                    duration_seconds=duration_s,
                    color=self.color,
                    icon_url=self.icon_url,
                )
            )

        log.info(f"[AtCoder] {len(contests)} upcoming contest(s) found")
        return contests