"""
ContestScheduler — the core polling loop.

Every CHECK_INTERVAL minutes it:
1. Fetches contests from all platforms.
2. Sends "new contest" embeds for anything not yet seen.
3. Sends reminder embeds when a contest is within a configured window
   (e.g. 60 min or 10 min before start) and hasn't been reminded yet.
"""

import asyncio
import logging
from datetime import datetime, timezone
from typing import List

import discord

from src.config import Config
from src.embeds import new_contest_embed, reminder_embed
from src.models import Contest
from src.platforms import ALL_PLATFORMS
from src.tracker import SeenTracker

log = logging.getLogger(__name__)


class ContestScheduler:
    def __init__(self, bot: discord.Client, config: Config):
        self.bot = bot
        self.config = config
        self.seen = SeenTracker(namespace="seen")
        self.reminded = SeenTracker(namespace="reminded")

    # ------------------------------------------------------------------ #
    # Public entry point
    # ------------------------------------------------------------------ #

    async def run(self):
        log.info("Scheduler started.")
        while True:
            try:
                await self._tick()
            except Exception as e:
                log.exception(f"Unexpected error in scheduler tick: {e}")
            await asyncio.sleep(self.config.check_interval_minutes * 60)

    async def poll_once(self):
        """Run a single poll — used in ONE_SHOT / cron mode."""
        try:
            await self._tick()
        except Exception as e:
            log.exception(f"Unexpected error in poll_once: {e}")

    # ------------------------------------------------------------------ #
    # Core tick
    # ------------------------------------------------------------------ #

    async def _tick(self):
        log.info("Polling all platforms…")
        channel = self.bot.get_channel(self.config.channel_id)
        if channel is None:
            log.error("Notification channel not found — skipping tick.")
            return

        all_contests: List[Contest] = []
        for platform in ALL_PLATFORMS:
            try:
                contests = await platform.fetch()
                all_contests.extend(contests)
            except Exception as e:
                log.error(f"[{platform.name}] Unhandled error: {e}")

        now = datetime.now(timezone.utc)

        for contest in all_contests:
            await self._handle_new(channel, contest)
            await self._handle_reminders(channel, contest, now)

    # ------------------------------------------------------------------ #
    # New-contest notifications
    # ------------------------------------------------------------------ #

    async def _handle_new(self, channel, contest: Contest):
        key = f"new:{contest.id}"
        if self.seen.is_new(key):
            try:
                embed = new_contest_embed(contest)
                mention = f"<@&{self.config.role_id}>" if self.config.role_id else "@Competitive Programmer"
                await channel.send(
                    content=f"{mention} New contest announced on **{contest.platform}**!",
                    embed=embed,
                )
                self.seen.mark(key)
                log.info(f"[NEW] {contest.platform} — {contest.name}")
            except Exception as e:
                log.error(f"Failed to send new-contest embed for {contest.id}: {e}")

    # ------------------------------------------------------------------ #
    # Reminder notifications
    # ------------------------------------------------------------------ #

    async def _handle_reminders(self, channel, contest: Contest, now: datetime):
        seconds_left = (contest.start_time - now).total_seconds()
        if seconds_left <= 0:
            return  # already started

        for remind_min in self.config.remind_before_minutes:
            remind_sec = remind_min * 60
            # Fire when within [remind_sec, remind_sec + poll_interval) seconds away
            window = self.config.check_interval_minutes * 60
            if remind_sec >= seconds_left and seconds_left > remind_sec - window:
                key = f"remind:{contest.id}:{remind_min}"
                if self.reminded.is_new(key):
                    try:
                        embed = reminder_embed(contest, remind_min)
                        mention = f"<@&{self.config.role_id}>" if self.config.role_id else "@Competitive Programmer"
                        await channel.send(
                            content=f"{mention} Reminder: **{contest.name}** starts in {remind_min} minute(s)!",
                            embed=embed,
                        )
                        self.reminded.mark(key)
                        log.info(
                            f"[REMIND {remind_min}m] {contest.platform} — {contest.name}"
                        )
                    except Exception as e:
                        log.error(f"Failed to send reminder embed for {contest.id}: {e}")
