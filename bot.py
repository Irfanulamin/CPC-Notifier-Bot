"""
CP Notifier — entry point.

Normal mode (default):  python bot.py
  Connects to Discord and polls on a loop (CHECK_INTERVAL_MINUTES).

One-shot mode (cron / GitHub Actions):  ONE_SHOT=true python bot.py
  Connects, runs a single poll, sends any notifications, then exits.
  Use this when triggered by an external scheduler (cron, GH Actions).
"""

import asyncio
import logging
import os

import discord
from discord.ext import commands

from src.config import Config
from src.scheduler import ContestScheduler

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
log = logging.getLogger("cp-notifier")

ONE_SHOT = os.environ.get("ONE_SHOT", "false").lower() == "true"


def main():
    config = Config.load()

    intents = discord.Intents.default()
    bot = commands.Bot(command_prefix="!", intents=intents)

    @bot.event
    async def on_ready():
        log.info(f"Logged in as {bot.user} (ID: {bot.user.id})")
        channel = bot.get_channel(config.channel_id)
        if channel is None:
            log.error(f"Channel {config.channel_id} not found. Check DISCORD_CHANNEL_ID.")
            await bot.close()
            return

        log.info(f"Sending notifications to #{channel.name}")
        scheduler = ContestScheduler(bot, config)

        if ONE_SHOT:
            log.info("ONE_SHOT mode — running single poll then exiting.")
            await scheduler.poll_once()
            await bot.close()
        else:
            asyncio.create_task(scheduler.run())

    bot.run(config.token)


if __name__ == "__main__":
    main()
