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
import os

SYSTEM_PROMPT = """
You are a Discord management agent that helps users manage their Discord servers. You have access to tools that allow you to get information about the server, its members, channels, and roles, as well as create new text channels. Use these tools to assist the user with their requests related to Discord server management.
If you don't know the answer to a question, you can say you don't know or ask for more information.
"""


def build_discord_agent() -> Agent:
    """
    Builds a Discord management agent that can be used to manage Discord servers.
    """
    return Agent(
        name="DiscordAgent",
        description="An agent that serves as the Discord management agent. Only discord stats, and possibility to create text channels.",
        conversation=Conversation(id='0'),
        model='kimi-k2.5',
        system_prompt=create_base_prompt() + SYSTEM_PROMPT,
        tools=[get_server_info, list_members, list_channels, list_roles, get_server_stats, get_member_info, get_channel_info, create_text_channel]
    )

