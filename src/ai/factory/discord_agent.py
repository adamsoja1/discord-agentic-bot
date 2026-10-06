from agentic_framework.core.agent import Agent
from agentic_framework.core.conversation import Conversation
from ..discord_tools import (
    create_text_channel,
    get_channel_info,
    get_member_info,
    get_recent_channel_messages,
    get_server_info,
    get_server_stats,
    list_members,
    list_channels,
    list_roles,
)
from ..prompts import create_base_prompt

GENERAL_SYSTEM_PROMPT = """
You are a Discord server helper for text channels.
Use tools when the user asks about server structure, members, roles, text channels, or recent text conversation.
You do not work with voice, audio, calls, or speech features. If asked about those, explain that this bot is text-only.
Keep answers easy to scan with short paragraphs or bullets.
"""

MODERATOR_SYSTEM_PROMPT = """
You are a Discord text-channel operations helper.
You can look up members, inspect text channels, and create new text channels when asked clearly.
Before creating a channel, infer a sensible lowercase hyphenated name if the user provides a natural-language name.
Do not claim to moderate messages, join calls, manage voice channels, or act outside the available tools.
"""

JOKE_SYSTEM_PROMPT = """
You are a light conversational helper for Discord.
You can write jokes, short replies, icebreakers, announcements, polls, summaries, and friendly copy.
Keep humor warm and concise. Match the user's language and tone.
"""


def build_discord_general_agent(model: str) -> Agent:
    """
    Builds a Discord General Agent.
    """
    return Agent(
        name="DiscordGeneralAgent",
        description="An agent that provides general information about the Discord server (stats, members, channels, roles).",
        conversation=Conversation(id='discord_general'),
        model=model,
        system_prompt=create_base_prompt() + GENERAL_SYSTEM_PROMPT,
        tools=[
            get_server_info,
            get_server_stats,
            list_members,
            list_channels,
            list_roles,
            get_recent_channel_messages,
        ]
    )


def build_discord_moderator_agent(model: str) -> Agent:
    """
    Builds a Discord Moderator Agent.
    """
    return Agent(
        name="DiscordModeratorAgent",
        description="An agent that handles moderation, member lookups, and channel management.",
        conversation=Conversation(id='discord_moderator'),
        model=model,
        system_prompt=create_base_prompt() + MODERATOR_SYSTEM_PROMPT,
        tools=[get_member_info, get_channel_info, create_text_channel]
    )


def build_discord_joke_agent(model: str) -> Agent:
    """
    Builds a Discord Joke Agent.
    """
    return Agent(
        name="DiscordJokeAgent",
        description="An agent that specializes in jokes, humor, and keeping the server atmosphere light.",
        conversation=Conversation(id='discord_joke'),
        model=model,
        system_prompt=create_base_prompt() + JOKE_SYSTEM_PROMPT,
        tools=[]
    )
