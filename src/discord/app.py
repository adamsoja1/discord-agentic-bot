import os
import logging
from datetime import datetime, timedelta, timezone

import discord
from discord.ext import commands
from dotenv import load_dotenv

from agentic_framework.core.stream_events import TextDeltaEvent, FinalAnswerEvent, ToolCallStartEvent, ToolResultEvent, DelegationEvent
from ..ai.factory.swarm import answer_discord_question
from ..ai import discord_tools


# =========================
# Konfiguracja
# =========================

MAX_HISTORY_MESSAGES = 3      # ile wiadomości maksymalnie w kontekście
MAX_HISTORY_AGE_HOURS = 5     # próg wieku wiadomości (np. 3–5h)

load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")

if not TOKEN:
    raise SystemExit("DISCORD_TOKEN not set.")


# =========================
# Discord setup
# =========================

intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix="!", intents=intents)
logger = logging.getLogger(__name__)


# =========================
# Events
# =========================

@bot.event
async def on_ready():
    logging.info(f"Logged in as {bot.user} (id: {bot.user.id})")
    print(f"Logged in as {bot.user} (id: {bot.user.id})")
    discord_tools.set_bot_instance(bot)


@bot.event
async def on_message(message: discord.Message):
    if message.author.bot:
        return

    print(f"Message from {message.author}: {message.content}")

    # ustaw kontekst guildii
    if message.guild:
        discord_tools.set_current_guild_context(message.guild.id)

    # jeśli bot nie jest oznaczony – normalna obsługa komend
    if bot.user not in message.mentions:
        await bot.process_commands(message)
        return

    # reakcja "thinking"
    try:
        await message.add_reaction("✅")
    except Exception:
        logging.exception("Failed to add reaction")

    thinking_msg = await message.reply(
        content="🤖 Generuję odpowiedź...",
        mention_author=False,
    )

    try:
        # =========================
        # Budowa kontekstu czasowego
        # =========================

        context_lines: list[str] = []

        now = datetime.now(timezone.utc)
        max_age = timedelta(hours=MAX_HISTORY_AGE_HOURS)

        # pobieramy więcej, filtrujemy ręcznie
        async for msg in message.channel.history(limit=5):
            if msg.id == message.id:
                continue

            # pomijamy stare wiadomości
            if now - msg.created_at > max_age:
                continue

            context_lines.insert(
                0,
                f"{msg.author.name}: {msg.content}"
            )

            if len(context_lines) >= MAX_HISTORY_MESSAGES:
                break

        context = "\n".join(context_lines)

        # =========================
        # Pytanie użytkownika
        # =========================

        question = message.content.replace(
            f"<@{bot.user.id}>",
            ""
        ).strip()
        answer = None

        async for event in answer_discord_question(question=question, context=context):
            if isinstance(event, FinalAnswerEvent):
                answer = event.answer[:1900]  # zabezpieczenie przed 2k limitem
            
            elif isinstance(event, ToolCallStartEvent):
                answer = f"🔧 Używam: {event.tool_name} ..."
                if event.tool_name.startswith("delegate_"):
                    answer = '➡️ Przygotowuje narzędzia...'
                    
            elif isinstance(event, ToolResultEvent):
                answer = f"✅ Sprawdzam wyniki z: {event.tool_name} ..."
            
            elif isinstance(event, DelegationEvent):
                answer = f"➡️ Sprawdzam możliwości ..."

            elif isinstance(event, TextDeltaEvent):
                print(event.delta, end="")
                continue
            

            print(f"Event: {type(event).__name__}, answer so far: {answer}")

            if not answer:
                answer = 'Czekaj myślę...'

            await thinking_msg.edit(
                content=answer or "..."
            )

    except Exception as e:
        logging.exception("AI error")
        await thinking_msg.edit(content=f"❌ Błąd: {e}")

    await bot.process_commands(message)


# =========================
# Entrypoint
# =========================

def main():
    logging.basicConfig(level=logging.INFO)
    bot.run(TOKEN)


if __name__ == "__main__":
    main()