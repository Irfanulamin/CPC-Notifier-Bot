"""
AtCoder — scrapes the upcoming contests table from atcoder.jp/contests/
The kenkoooo.com archive only contains past contests, not future ones.
No auth required.
"""

import logging
import re
from datetime import datetime, timezone
from typing import List

import aiohttp

from src.models import Contest
from src.platforms.base import BasePlatform

log = logging.getLogger(__name__)

URL = "https://atcoder.jp/contests/"


class AtCoderClient(BasePlatform):
    name = "AtCoder"
    color = 0x222222
    icon_url = "https://img.atcoder.jp/assets/favicon.png"

    async def fetch(self) -> List[Contest]:
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    URL,
                    headers={"Accept-Language": "en-US,en;q=0.9"},
                    timeout=aiohttp.ClientTimeout(total=15),
                ) as resp:
                    html = await resp.text()
        except Exception as e:
            log.error(f"[AtCoder] Failed to fetch contests page: {e}")
            return []

        contests = []
        now = datetime.now(timezone.utc)

        upcoming_match = re.search(
            r'id="contest-table-upcoming".*?</tbody>',
            html,
            re.DOTALL,
        )
        if not upcoming_match:
            log.warning("[AtCoder] Could not find upcoming contests table in page HTML")
            return []

        table_html = upcoming_match.group(0)
        rows = re.findall(r"<tr>(.*?)</tr>", table_html, re.DOTALL)

        for row in rows:
            cells = re.findall(r"<td[^>]*>(.*?)</td>", row, re.DOTALL)
            if len(cells) < 3:
                continue

            time_match = re.search(r'(\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}[+-]\d{2}:\d{2})', cells[0])
            if not time_match:
                continue
            try:
                start_time = datetime.fromisoformat(time_match.group(1)).astimezone(timezone.utc)
            except Exception:
                continue

            if start_time <= now:
                continue
            if (start_time - now).days > 14:
                continue

            link_match = re.search(r'href="/contests/([^"]+)"[^>]*>([^<]+)<', cells[1])
            if not link_match:
                continue
            contest_id = link_match.group(1).strip()
            name = link_match.group(2).strip()

            dur_match = re.search(r"(\d+)", re.sub(r"<[^>]+>", "", cells[2]))
            duration_s = int(dur_match.group(1)) * 60 if dur_match else 0

            contests.append(
                Contest(
                    id=f"atcoder-{contest_id}",
                    platform=self.name,
                    name=name,
                    url=f"https://atcoder.jp/contests/{contest_id}",
                    start_time=start_time,
                    duration_seconds=duration_s,
                    color=self.color,
                    icon_url=self.icon_url,
                )
            )

        log.info(f"[AtCoder] {len(contests)} upcoming contest(s) found")
        return contests