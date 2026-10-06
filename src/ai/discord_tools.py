"""Text-only Discord server tools for the agentic bot."""

import asyncio
import re
from typing import Optional

import discord
from discord.ext import commands

from agentic_framework.tools.base import tool

# ---------------------------------------------------------------------------
# Global state (set by bot.py at startup / on each message)
# ---------------------------------------------------------------------------

_bot_instance: Optional[commands.Bot] = None
_current_guild_id: Optional[int] = None
_current_channel_id: Optional[int] = None


def set_bot_instance(bot: commands.Bot) -> None:
    global _bot_instance
    _bot_instance = bot


def set_current_guild_context(guild_id: int) -> None:
    global _current_guild_id
    _current_guild_id = guild_id


def set_current_channel_context(channel_id: int) -> None:
    global _current_channel_id
    _current_channel_id = channel_id


def _get_bot() -> commands.Bot:
    if _bot_instance is None:
        raise RuntimeError("Bot instance not set. Call set_bot_instance() first.")
    return _bot_instance


def _get_guild(guild_id: Optional[int] = None) -> discord.Guild:
    bot = _get_bot()
    gid = _coerce_discord_id(guild_id) or _current_guild_id
    if gid:
        guild = bot.get_guild(gid)
        if guild:
            return guild
    if not bot.guilds:
        raise RuntimeError("Bot is not in any guilds.")
    return bot.guilds[0]


def _coerce_discord_id(value: str | int | None) -> Optional[int]:
    if value is None or value == "":
        return None
    if isinstance(value, int):
        return value

    match = re.search(r"\d{15,25}", value)
    if not match:
        raise ValueError(f"Expected a Discord ID or mention, got: {value}")
    return int(match.group(0))


def _get_text_channel(channel_id: str | int | None = None) -> discord.TextChannel:
    guild = _get_guild()
    cid = _coerce_discord_id(channel_id) or _current_channel_id

    if cid is None:
        raise RuntimeError("No current text channel is available.")

    channel = guild.get_channel(cid) or _get_bot().get_channel(cid)
    if not isinstance(channel, discord.TextChannel):
        raise RuntimeError("Only text channels are supported.")

    return channel


# ---------------------------------------------------------------------------
# Server information
# ---------------------------------------------------------------------------
@tool
def get_server_info(guild_id: Optional[int] = None) -> str:
    """Get general information about the Discord server."""
    try:
        g = _get_guild(guild_id)
        owner = g.owner.name if g.owner else "N/A"
        return (
            f"Server: {g.name} (ID: {g.id})\n"
            f"Owner: {owner}\n"
            f"Members: {g.member_count}\n"
            f"Created: {g.created_at.strftime('%Y-%m-%d')}\n"
            f"Text channels: {len(g.text_channels)}\n"
            f"Roles: {len(g.roles)}\n"
            f"Emojis: {len(g.emojis)}"
        )
    except Exception as e:
        return f"Error getting server info: {e}"

@tool
def list_members(guild_id: Optional[int] = None, limit: int = 20) -> str:
    """List recent members of the Discord server."""
    try:
        limit = 20
        g = _get_guild(guild_id)
        members = sorted(
            g.members, key=lambda m: m.joined_at or m.created_at, reverse=True
        )[:limit]
        lines = [f"Members of {g.name} (showing {len(members)}):"]
        for m in members:
            kind = "Bot" if m.bot else "User"
            roles = ", ".join(r.name for r in m.roles[1:]) or "None"
            lines.append(f"  {m.name}, {m.id} [{kind}] — roles: {roles}")
        return "\n".join(lines)
    except Exception as e:
        return f"Error listing members: {e}"

@tool
def list_channels(guild_id: Optional[int] = None) -> str:
    """List text channels on the Discord server."""
    try:
        g = _get_guild(guild_id)
        lines = [f"Text channels in {g.name}:"]
        for c in g.text_channels:
            category = f" [{c.category.name}]" if c.category else ""
            topic = f" - {c.topic}" if c.topic else ""
            lines.append(f"  #{c.name}{category} (ID: {c.id}){topic}")
        return "\n".join(lines)
    except Exception as e:
        return f"Error listing channels: {e}"

@tool
def list_roles(guild_id: Optional[int] = None) -> str:
    """List all roles on the Discord server with member counts."""
    try:
        g = _get_guild(guild_id)
        roles = sorted(g.roles, key=lambda r: r.position, reverse=True)
        lines = [f"Roles in {g.name}:"]
        for r in roles:
            lines.append(f"  {r.name} — {len(r.members)} members")
        return "\n".join(lines)
    except Exception as e:
        return f"Error listing roles: {e}"

@tool
def get_server_stats(guild_id: Optional[int] = None) -> str:
    """Get detailed statistics about the Discord server."""
    try:
        g = _get_guild(guild_id)
        online = sum(1 for m in g.members if m.status == discord.Status.online)
        idle   = sum(1 for m in g.members if m.status == discord.Status.idle)
        dnd    = sum(1 for m in g.members if m.status == discord.Status.dnd)
        offline= sum(1 for m in g.members if m.status == discord.Status.offline)
        bots   = sum(1 for m in g.members if m.bot)
        return (
            f"Stats for {g.name}:\n"
            f"  Total members: {g.member_count} ({g.member_count - bots} humans, {bots} bots)\n"
            f"  Online: {online} | Idle: {idle} | DnD: {dnd} | Offline: {offline}\n"
            f"  Text channels: {len(g.text_channels)} | Roles: {len(g.roles)} | Emojis: {len(g.emojis)}"
        )
    except Exception as e:
        return f"Error getting server stats: {e}"

@tool
def get_member_info(member_id: str, guild_id: Optional[int] = None) -> str:
    """Get information about a specific Discord member by user ID or mention."""
    try:
        g = _get_guild(guild_id)
        member = g.get_member(_coerce_discord_id(member_id))
        if not member:
            return f"Member with ID {member_id} not found on this server."
        roles = ", ".join(r.name for r in member.roles[1:]) or "None"
        joined = member.joined_at.strftime("%Y-%m-%d") if member.joined_at else "N/A"
        return (
            f"Member: {member.name} (ID: {member.id})\n"
            f"  Bot: {member.bot}\n"
            f"  Account created: {member.created_at.strftime('%Y-%m-%d')}\n"
            f"  Joined server: {joined}\n"
            f"  Roles: {roles}"
        )
    except Exception as e:
        return f"Error getting member info: {e}"

@tool
def get_channel_info(channel_id: str, guild_id: Optional[int] = None) -> str:
    """Get information about a specific text channel by ID or mention."""
    try:
        g = _get_guild(guild_id)
        channel = g.get_channel(_coerce_discord_id(channel_id))
        if not channel:
            return f"Channel with ID {channel_id} not found."
        if isinstance(channel, discord.TextChannel):
            return (
                f"Text channel: #{channel.name} (ID: {channel.id})\n"
                f"  Topic: {channel.topic or 'None'}\n"
                f"  Category: {channel.category.name if channel.category else 'None'}\n"
                f"  NSFW: {channel.is_nsfw()}\n"
                f"  Created: {channel.created_at.strftime('%Y-%m-%d')}"
            )
        return f"Only text channels are supported. Got: {type(channel).__name__}"
    except Exception as e:
        return f"Error getting channel info: {e}"


@tool
def create_text_channel(name: str, category_id: Optional[int] = None) -> str:
    """Create a new text channel on the Discord server."""
    try:
        bot = _get_bot()
        g = _get_guild()

        async def _create():
            category = g.get_channel(_coerce_discord_id(category_id)) if category_id else None
            channel = await g.create_text_channel(name=name, category=category)
            return f"Created text channel: #{channel.name} (ID: {channel.id})"

        future = asyncio.run_coroutine_threadsafe(_create(), bot.loop)
        return future.result(timeout=10)
    except Exception as e:
        return f"Error creating channel: {e}"


@tool
def get_recent_channel_messages(channel_id: Optional[str] = None, limit: int = 20) -> str:
    """Read recent messages from the current or specified text channel."""
    try:
        bot = _get_bot()
        channel = _get_text_channel(channel_id)
        limit = max(1, min(int(limit), 50))

        async def _read_messages():
            lines: list[str] = []
            async for message in channel.history(limit=limit):
                if message.author.bot or not message.content.strip():
                    continue
                created = message.created_at.strftime("%Y-%m-%d %H:%M")
                lines.insert(0, f"[{created}] {message.author.display_name}: {message.content.strip()}")
            return lines

        future = asyncio.run_coroutine_threadsafe(_read_messages(), bot.loop)
        lines = future.result(timeout=10)
        if not lines:
            return f"No recent text messages found in #{channel.name}."
        return f"Recent text messages in #{channel.name}:\n" + "\n".join(lines)
    except Exception as e:
        return f"Error reading recent messages: {e}"
