"""
CodeChef — tries multiple known endpoint structures since CodeChef
has changed their API layout several times without notice.

Strategy:
  1. GET /api/list/contests/future  (newer structure)
  2. GET /api/contests/          (older structure)
  3. Kontests aggregator fallback

On first run with a new structure, the raw JSON is logged at DEBUG
level so you can inspect it and file a bug report.
"""

import logging
from datetime import datetime, timezone
from typing import List, Optional

import aiohttp

from src.models import Contest
from src.platforms.base import BasePlatform

log = logging.getLogger(__name__)

HEADERS = {
    "User-Agent": "Mozilla/5.0 (compatible; cp-notifier-bot/1.0)",
    "Accept": "application/json",
}


def _parse_dt(s: str) -> datetime:
    """Parse ISO-8601 string → UTC-aware datetime. Handles trailing Z."""
    s = s.replace("Z", "+00:00")
    return datetime.fromisoformat(s).astimezone(timezone.utc)


def _extract_contest_list(data: dict) -> Optional[list]:
    """
    Try every known JSON shape CodeChef has used and return the raw list,
    or None if nothing matched.
    """
    # Shape A (seen ~2023-2024):
    # { "result": { "data": { "content": { "contestList": [...] } } } }
    try:
        return data["result"]["data"]["content"]["contestList"]
    except (KeyError, TypeError):
        pass

    # Shape B (seen ~2022):
    # { "result": { "data": { "future": [...] } } }
    try:
        return data["result"]["data"]["future"]
    except (KeyError, TypeError):
        pass

    # Shape C — flat list at top level
    if isinstance(data, list):
        return data

    # Shape D — { "contests": [...] }
    if isinstance(data.get("contests"), list):
        return data["contests"]

    # Shape E — { "future_contests": [...] }
    if isinstance(data.get("future_contests"), list):
        return data["future_contests"]

    # Unknown — log the top-level keys so we can adapt
    log.warning(
        f"[CodeChef] Unrecognised JSON structure. Top-level keys: {list(data.keys()) if isinstance(data, dict) else type(data).__name__}"
    )
    return None


def _parse_contest(raw: dict, platform_name: str, color: int, icon_url: str, now: datetime) -> Optional[Contest]:
    """
    Try every field-name variant CodeChef has used across API versions.
    Returns a Contest or None if the entry should be skipped.
    """
    # --- start time ---
    start_time = None
    for key in ("contest_start_date_iso", "startDate", "start_date", "start_time"):
        val = raw.get(key)
        if val:
            try:
                start_time = _parse_dt(str(val))
                break
            except Exception:
                continue
    if start_time is None:
        return None

    if start_time <= now:
        return None
    if (start_time - now).days > 14:
        return None

    # --- end time ---
    end_time = None
    for key in ("contest_end_date_iso", "endDate", "end_date", "end_time"):
        val = raw.get(key)
        if val:
            try:
                end_time = _parse_dt(str(val))
                break
            except Exception:
                continue

    # contest_duration field is in minutes; prefer it over date subtraction
    if raw.get("contest_duration"):
        try:
            duration_s = int(raw["contest_duration"]) * 60
        except (ValueError, TypeError):
            duration_s = int((end_time - start_time).total_seconds()) if end_time else 0
    else:
        duration_s = int((end_time - start_time).total_seconds()) if end_time else 0

    # --- contest code / id ---
    code = (
        raw.get("contest_code")
        or raw.get("code")
        or raw.get("contestCode")
        or raw.get("name", "unknown").replace(" ", "-").lower()
    )

    # --- name ---
    name = (
        raw.get("contest_name")
        or raw.get("name")
        or raw.get("title")
        or "Unknown Contest"
    )

    return Contest(
        id=f"codechef-{code}",
        platform=platform_name,
        name=name,
        url=f"https://www.codechef.com/{code}",
        start_time=start_time,
        duration_seconds=duration_s,
        color=color,
        icon_url=icon_url,
        end_time=end_time,
    )


class CodeChefClient(BasePlatform):
    name = "CodeChef"
    color = 0x5B4638
    icon_url = "https://cdn.codechef.com/images/cc-logo.svg"

    ENDPOINTS = [
        "https://www.codechef.com/api/list/contests/future",
        "https://www.codechef.com/api/contests/?sort_by=start&sorting_order=asc&offset=0&mode=future",
    ]
    FALLBACK_URL = "https://kontests.net/api/v1/code_chef"

    async def fetch(self) -> List[Contest]:
        # Try each official endpoint in order
        for url in self.ENDPOINTS:
            result = await self._fetch_url(url)
            if result is not None:
                return result

        # Last resort: Kontests
        log.warning("[CodeChef] All primary endpoints failed, trying Kontests fallback…")
        return await self._fetch_kontests()

    async def _fetch_url(self, url: str) -> Optional[List[Contest]]:
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    url, headers=HEADERS, timeout=aiohttp.ClientTimeout(total=15)
                ) as resp:
                    if resp.status != 200:
                        log.debug(f"[CodeChef] {url} → HTTP {resp.status}")
                        return None
                    data = await resp.json(content_type=None)
        except Exception as e:
            log.debug(f"[CodeChef] {url} request error: {e}")
            return None

        contest_list = _extract_contest_list(data)
        if contest_list is None:
            return None

        now = datetime.now(timezone.utc)
        contests = []
        for raw in contest_list:
            c = _parse_contest(raw, self.name, self.color, self.icon_url, now)
            if c:
                contests.append(c)

        log.info(f"[CodeChef] {len(contests)} upcoming contest(s) found")
        return contests

    async def _fetch_kontests(self) -> List[Contest]:
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    self.FALLBACK_URL, timeout=aiohttp.ClientTimeout(total=10)
                ) as resp:
                    data = await resp.json(content_type=None)
        except Exception as e:
            log.error(f"[CodeChef] Kontests fallback failed: {e}")
            return []

        now = datetime.now(timezone.utc)
        contests = []
        for raw in data:
            c = _parse_contest(raw, self.name, self.color, self.icon_url, now)
            if c:
                contests.append(c)

        log.info(f"[CodeChef] {len(contests)} upcoming contest(s) found (Kontests fallback)")
        return contests
