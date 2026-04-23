"""
Embed builder — converts Contest objects into beautiful Discord embeds.
"""

import discord
from datetime import datetime, timezone
from src.models import Contest


def new_contest_embed(contest: Contest) -> discord.Embed:
    """Embed for a newly announced contest."""
    embed = discord.Embed(
        title=f"🆕  New Contest — {contest.name}",
        url=contest.url,
        description=f"A new contest has been announced on **{contest.platform}**!",
        color=contest.color,
        timestamp=datetime.now(timezone.utc),
    )
    embed.add_field(name="🕐 Start Time", value=contest.start_str(), inline=True)
    embed.add_field(name="⏱ Duration", value=contest.duration_str(), inline=True)
    embed.add_field(name="🔗 Link", value=f"[Register / View]({contest.url})", inline=False)
    embed.set_thumbnail(url=contest.icon_url)
    embed.set_footer(text=f"{contest.platform} • Contest Notifier")
    return embed


def reminder_embed(contest: Contest, minutes_left: int) -> discord.Embed:
    """Embed for a pre-start reminder."""
    if minutes_left <= 10:
        emoji = "🚨"
        urgency = f"**{minutes_left} minutes** — get ready!"
    elif minutes_left <= 30:
        emoji = "⚡"
        urgency = f"**{minutes_left} minutes** to go!"
    else:
        emoji = "⏰"
        urgency = f"Starting in **{minutes_left} minutes**"

    embed = discord.Embed(
        title=f"{emoji}  Reminder — {contest.name}",
        url=contest.url,
        description=f"{urgency}\n\n**Platform:** {contest.platform}",
        color=contest.color,
        timestamp=datetime.now(timezone.utc),
    )
    embed.add_field(name="🕐 Start Time", value=contest.start_str(), inline=True)
    embed.add_field(name="⏱ Duration", value=contest.duration_str(), inline=True)
    embed.add_field(name="🔗 Link", value=f"[Open Contest]({contest.url})", inline=False)
    embed.set_thumbnail(url=contest.icon_url)
    embed.set_footer(text=f"{contest.platform} • Contest Notifier")
    return embed
