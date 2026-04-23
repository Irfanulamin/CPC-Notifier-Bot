"""
Shared Contest dataclass used across all platform fetchers.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional


@dataclass(frozen=True, eq=True)
class Contest:
    id: str                    # unique per platform, e.g. "cf-1234" or "atcoder-abc300"
    platform: str              # human-readable label, e.g. "Codeforces"
    name: str
    url: str
    start_time: datetime       # always UTC-aware
    duration_seconds: int
    color: int                 # Discord embed colour (hex int)
    icon_url: str              # platform logo for embed thumbnail

    # Optional — some platforms don't expose this
    end_time: Optional[datetime] = field(default=None, compare=False)

    def duration_str(self) -> str:
        total = self.duration_seconds
        hours, remainder = divmod(total, 3600)
        minutes = remainder // 60
        if hours and minutes:
            return f"{hours}h {minutes}m"
        if hours:
            return f"{hours}h"
        return f"{minutes}m"

    def start_str(self) -> str:
        """ISO-8601 UTC string for display."""
        return self.start_time.strftime("%Y-%m-%d %H:%M UTC")
