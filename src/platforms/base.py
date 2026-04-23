"""
Abstract base class that every platform fetcher must implement.
Adding a new platform = subclass this, implement fetch(), register in scheduler.
"""

from __future__ import annotations
import logging
from abc import ABC, abstractmethod
from typing import List
from src.models import Contest

log = logging.getLogger(__name__)


class BasePlatform(ABC):
    name: str = "Unknown"          # human-readable e.g. "Codeforces"
    color: int = 0x5865F2          # Discord embed colour
    icon_url: str = ""             # thumbnail shown in embeds

    @abstractmethod
    async def fetch(self) -> List[Contest]:
        """
        Fetch upcoming contests from the platform.
        Returns a list of Contest objects (may be empty on error).
        Should never raise — catch exceptions internally and log them.
        """
        ...
