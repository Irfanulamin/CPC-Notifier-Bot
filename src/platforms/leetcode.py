"""
LeetCode — uses LeetCode's own GraphQL API to fetch upcoming contests.
No auth required for the contest list query.
API: https://leetcode.com/graphql
"""

import logging
from datetime import datetime, timezone
from typing import List

import aiohttp

from src.models import Contest
from src.platforms.base import BasePlatform

log = logging.getLogger(__name__)

GRAPHQL_URL = "https://leetcode.com/graphql"

QUERY = """
query {
  allContests {
    title
    titleSlug
    startTime
    duration
    __typename
  }
}
"""


class LeetCodeClient(BasePlatform):
    name = "LeetCode"
    color = 0xFFA116          # LeetCode orange
    icon_url = "https://leetcode.com/favicon-32x32.png"

    async def fetch(self) -> List[Contest]:
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    GRAPHQL_URL,
                    json={"query": QUERY},
                    headers={
                        "Content-Type": "application/json",
                        "Referer": "https://leetcode.com/contest/",
                    },
                    timeout=aiohttp.ClientTimeout(total=15),
                ) as resp:
                    data = await resp.json(content_type=None)
        except Exception as e:
            log.error(f"[LeetCode] Failed to fetch contests: {e}")
            return []

        now = datetime.now(timezone.utc).timestamp()
        contests = []

        for c in data.get("data", {}).get("allContests", []):
            start_ts = c.get("startTime")
            duration_s = c.get("duration", 0)
            if start_ts is None:
                continue

            # Only upcoming contests within 14 days
            if start_ts <= now or start_ts - now > 14 * 86400:
                continue

            slug = c.get("titleSlug", "")
            contests.append(
                Contest(
                    id=f"leetcode-{slug}",
                    platform=self.name,
                    name=c.get("title", "Unknown Contest"),
                    url=f"https://leetcode.com/contest/{slug}/",
                    start_time=datetime.fromtimestamp(start_ts, tz=timezone.utc),
                    duration_seconds=duration_s,
                    color=self.color,
                    icon_url=self.icon_url,
                )
            )

        log.info(f"[LeetCode] {len(contests)} upcoming contest(s) found")
        return contests
