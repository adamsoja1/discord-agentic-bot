
from __future__ import annotations

import datetime
import json
import logging
import os
from dataclasses import dataclass, field
from typing import Any, Callable

from agentic_framework.core.conversation import Conversation
from agentic_framework.core.stream_events import FinalAnswerEvent
from agentic_framework.core.crew import Crew
from openai import OpenAI
from dotenv import load_dotenv

from .entypoint_agent import build_entrypoint_agent
from .websearch_agent import build_websearch_agent
from .discord_agent import build_discord_agent

load_dotenv()
logger = logging.getLogger(__name__)


async def answer_discord_question(question: str, context: str = "") -> AsyncGenerator:
    question = question.strip()
    if not question:
        yield FinalAnswerEvent(answer="Nie rozumiem pytania. Napisz coś więcej!")
        return

    entrypoint = build_entrypoint_agent(model='kimi-k2.5')
    discord_agent = build_discord_agent(model='glm-5')
    websearch_agent = build_websearch_agent(model='glm-5')
    crew = Crew(
        entrypoint_agent=entrypoint,
        agents=[discord_agent, websearch_agent, entrypoint],
        conversation=Conversation(id='0'),
        shared_knowledge=False,
    )

    user_content = question
    if context:
        user_content = (
            "[Recent conversation context— for reference only]\n"
            f"{context}\n"
            "[End context]\n\n"
            + user_content
        )

    async for event in crew.invoke(user_content):  # crew.invoke must be async gen
        yield event