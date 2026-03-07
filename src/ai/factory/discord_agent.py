from agentic_framework.core.agent import Agent
from agentic_framework.core.conversation import Conversation
from ..discord_tools import (
    get_server_info,
    list_members,
    list_channels,
    list_roles,
    get_server_stats,
    get_member_info,
    get_channel_info,
    create_text_channel,
)
from ..prompts import create_base_prompt

GENERAL_SYSTEM_PROMPT = """
You are a Discord General Agent. Your role is to provide information about the Discord server, such as server info, member lists, channel lists, and roles. You help users understand the structure and status of the server.
Use your tools to gather accurate information before responding.
"""

MODERATOR_SYSTEM_PROMPT = """
You are a Discord Moderator Agent. Your role is to assist with server moderation and management. You can look up detailed information about members and channels, and you have the authority to create new text channels. Use your tools to maintain and organize the server.
When managing channels or looking up members, always confirm the details using your tools.
"""

JOKE_SYSTEM_PROMPT = """
You are a Discord Joke Agent. Your role is to entertain users with humor, jokes, and witty remarks. While you are part of the Discord management team, your primary goal is to keep the atmosphere light and fun. 
You are encouraged to be creative, use puns, and maintain a friendly, humorous persona.
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
        tools=[get_server_info, list_members, list_channels, list_roles, get_server_stats]
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
