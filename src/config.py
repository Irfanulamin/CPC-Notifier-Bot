"""
Configuration — loads from environment variables or a .env file.
"""

import os
import logging
from dataclasses import dataclass, field
from typing import List

log = logging.getLogger(__name__)

# Try to load .env without requiring python-dotenv
def _load_dotenv(path: str = ".env"):
    try:
        with open(path) as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    key, _, value = line.partition("=")
                    os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))
    except FileNotFoundError:
        pass


@dataclass
class Config:
    token: str
    channel_id: int
    check_interval_minutes: int          # how often to poll all platforms
    remind_before_minutes: List[int]     # e.g. [60, 10] → remind 60 min & 10 min before start
    role_id: int                         # Discord role ID to mention on notifications (0 = no mention)

    @classmethod
    def load(cls, env_path: str = ".env") -> "Config":
        _load_dotenv(env_path)

        token = os.environ.get("DISCORD_TOKEN", "").strip()
        if not token:
            raise ValueError("DISCORD_TOKEN is not set. Add it to your .env file.")

        channel_id_raw = os.environ.get("DISCORD_CHANNEL_ID", "").strip()
        if not channel_id_raw:
            raise ValueError("DISCORD_CHANNEL_ID is not set. Add it to your .env file.")

        try:
            channel_id = int(channel_id_raw)
        except ValueError:
            raise ValueError(f"DISCORD_CHANNEL_ID must be an integer, got: {channel_id_raw!r}")

        interval = int(os.environ.get("CHECK_INTERVAL_MINUTES", "15"))
        remind_raw = os.environ.get("REMIND_BEFORE_MINUTES", "60,10")
        remind = [int(x.strip()) for x in remind_raw.split(",") if x.strip().isdigit()]

        role_id_raw = os.environ.get("DISCORD_ROLE_ID", "0").strip()
        try:
            role_id = int(role_id_raw)
        except ValueError:
            role_id = 0

        log.info(
            f"Config loaded — interval={interval}m, reminders at {remind} min before start"
        )
        return cls(
            token=token,
            channel_id=channel_id,
            check_interval_minutes=interval,
            remind_before_minutes=remind,
            role_id=role_id,
        )
