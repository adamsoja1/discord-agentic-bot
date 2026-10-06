import logging
import os
import re
from datetime import datetime, timedelta, timezone

import discord
from discord.ext import commands
from dotenv import load_dotenv

from agentic_framework.core.stream_events import (
    DelegationEvent,
    ErrorEvent,
    FinalAnswerEvent,
    TextDeltaEvent,
    ToolCallStartEvent,
    ToolResultEvent,
)
from ..ai import discord_tools
from ..ai.factory.swarm import answer_discord_question


logger = logging.getLogger(__name__)

MAX_HISTORY_MESSAGES = 5
MAX_HISTORY_AGE_HOURS = 5
MAX_DISCORD_CONTENT_LENGTH = 1900
MAX_FOLLOW_UP_CHUNKS = 2

load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")

if not TOKEN:
    raise SystemExit("DISCORD_TOKEN not set.")


intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix="!", intents=intents, help_command=None)


def _bot_was_mentioned(message: discord.Message) -> bool:
    return bool(bot.user and bot.user in message.mentions)


def _strip_bot_mention(content: str) -> str:
    if not bot.user:
        return content.strip()

    mention_pattern = rf"<@!?{bot.user.id}>"
    return re.sub(mention_pattern, "", content).strip()


def _normalise_answer(text: str | None) -> str:
    cleaned = (text or "").strip()
    if not cleaned:
        return "I could not produce a useful answer. Try adding a little more detail."
    return discord.utils.escape_mentions(cleaned)


def _split_for_discord(text: str) -> list[str]:
    if len(text) <= MAX_DISCORD_CONTENT_LENGTH:
        return [text]

    chunks: list[str] = []
    remaining = text

    while remaining and len(chunks) <= MAX_FOLLOW_UP_CHUNKS:
        if len(remaining) <= MAX_DISCORD_CONTENT_LENGTH:
            chunks.append(remaining)
            break

        split_at = remaining.rfind("\n", 0, MAX_DISCORD_CONTENT_LENGTH)
        if split_at < MAX_DISCORD_CONTENT_LENGTH // 2:
            split_at = remaining.rfind(" ", 0, MAX_DISCORD_CONTENT_LENGTH)
        if split_at < MAX_DISCORD_CONTENT_LENGTH // 2:
            split_at = MAX_DISCORD_CONTENT_LENGTH

        chunks.append(remaining[:split_at].strip())
        remaining = remaining[split_at:].strip()

    if remaining and chunks:
        chunks[-1] = chunks[-1].rstrip() + "\n\n[Answer shortened to fit Discord.]"

    return chunks


async def _collect_recent_context(message: discord.Message) -> str:
    context_lines: list[str] = []
    now = datetime.now(timezone.utc)
    max_age = timedelta(hours=MAX_HISTORY_AGE_HOURS)

    async for msg in message.channel.history(limit=MAX_HISTORY_MESSAGES * 3):
        if msg.id == message.id or msg.author.bot or not msg.content.strip():
            continue
        if now - msg.created_at > max_age:
            continue

        context_lines.insert(0, f"{msg.author.display_name}: {msg.content.strip()}")
        if len(context_lines) >= MAX_HISTORY_MESSAGES:
            break

    return "\n".join(context_lines)


async def _edit_status(reply: discord.Message, content: str) -> None:
    chunk = _split_for_discord(_normalise_answer(content))[0]

    if reply.content != chunk:
        await reply.edit(content=chunk, allowed_mentions=discord.AllowedMentions.none())


def _status_for_event(event: object) -> str | None:
    if isinstance(event, ToolCallStartEvent):
        tool_name = event.tool_name.removeprefix("delegate_to_agent_")
        if event.tool_name.startswith("delegate_to_agent_"):
            return f"Routing this to {tool_name}..."
        return f"Checking {tool_name}..."

    if isinstance(event, ToolResultEvent):
        return f"Reading results from {event.tool_name}..."

    if isinstance(event, DelegationEvent):
        return f"Asking {event.target_agent} for help..."

    if isinstance(event, ErrorEvent):
        return f"Error: {event.error}"

    return None


async def _send_ai_response(message: discord.Message, question: str) -> None:
    reply = await message.reply(
        content="Thinking...",
        mention_author=False,
        allowed_mentions=discord.AllowedMentions.none(),
    )

    answer: str | None = None
    context = await _collect_recent_context(message)

    async for event in answer_discord_question(question=question, context=context):
        if isinstance(event, FinalAnswerEvent):
            answer = event.answer
            continue

        if isinstance(event, TextDeltaEvent):
            logger.debug("Text delta from %s: %s", event.agent_name, event.delta)
            continue

        status = _status_for_event(event)
        if status:
            logger.info("Agent event: %s", type(event).__name__)
            await _edit_status(reply, status)

    chunks = _split_for_discord(_normalise_answer(answer))
    await reply.edit(content=chunks[0], allowed_mentions=discord.AllowedMentions.none())

    for chunk in chunks[1:]:
        await message.channel.send(
            chunk,
            reference=message,
            allowed_mentions=discord.AllowedMentions.none(),
        )


@bot.event
async def on_ready():
    logger.info("Logged in as %s (id: %s)", bot.user, bot.user.id if bot.user else "unknown")
    discord_tools.set_bot_instance(bot)


@bot.event
async def on_message(message: discord.Message):
    if message.author.bot:
        return

    logger.info("Message from %s: %s", message.author, message.content)

    if message.guild:
        discord_tools.set_current_guild_context(message.guild.id)
        discord_tools.set_current_channel_context(message.channel.id)

    if message.content.startswith("!"):
        await bot.process_commands(message)
        return

    should_answer = message.guild is None or _bot_was_mentioned(message)
    if not should_answer:
        await bot.process_commands(message)
        return

    try:
        await _send_ai_response(message, _strip_bot_mention(message.content))
    except Exception as e:
        logger.exception("AI error")
        await message.reply(
            content=f"Error while generating the answer: {e}",
            mention_author=False,
            allowed_mentions=discord.AllowedMentions.none(),
        )


@bot.command(name="ask")
async def ask_command(ctx: commands.Context, *, question: str = ""):
    """Ask the bot without mentioning it."""
    if question.strip():
        await _send_ai_response(ctx.message, question.strip())
        return

    await ctx.reply(
        "Usage: `!ask your question`",
        mention_author=False,
        allowed_mentions=discord.AllowedMentions.none(),
    )


@bot.command(name="help")
async def help_command(ctx: commands.Context):
    """Show text-only usage help."""
    await ctx.reply(
        "\n".join(
            [
                "Text bot commands:",
                "`@bot your question` - ask in a server channel.",
                "`!ask your question` - ask without mentioning the bot.",
                "DM the bot - ask privately.",
                "",
                "I can help with server info, text-channel organization, web research, code questions, summaries, drafts, and light conversation.",
            ]
        ),
        mention_author=False,
        allowed_mentions=discord.AllowedMentions.none(),
    )


def main():
    logging.basicConfig(level=logging.INFO)
    bot.run(TOKEN)


if __name__ == "__main__":
    main()
