
from __future__ import annotations

import datetime
import json
import logging
import os
from dataclasses import dataclass, field
from typing import Any, Callable

from agentic_framework.core.conversation import Conversation

from agentic_framework.core.crew import Crew
from openai import OpenAI
from dotenv import load_dotenv

from .entypoint_agent import build_entrypoint_agent
from .websearch_agent import build_websearch_agent
from .discord_agent import build_discord_agent

load_dotenv()
logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# OpenAI-compatible client (Ollama / LM Studio / OpenAI)
# ---------------------------------------------------------------------------

entrypoint_agent = build_entrypoint_agent()

client = OpenAI(
    base_url=os.getenv("LLM_BASE_URL", "https://ollama.com/v1"),
    api_key=os.getenv("OLLAMA_API_KEY", "ollama"),   
)
MODEL = os.getenv("LLM_MODEL", "llama3.1")


# ---------------------------------------------------------------------------
# Public entrypoint
# ---------------------------------------------------------------------------

async def answer_discord_question(question: str, context: str = "") -> str:
    question = question.strip()
    if not question:
        return "Nie rozumiem pytania. Napisz coś więcej!"

    entrypoint = build_entrypoint_agent()
    discord_agent = build_discord_agent()
    websearch_agent = build_websearch_agent()

    crew = Crew(
        entrypoint_agent=entrypoint,
        agents=[discord_agent, websearch_agent, entrypoint],
        conversation=Conversation(id='0'),
        shared_knowledge=False,  # Don't share conversation to avoid tool call bleed
    )

    user_content = question
    if context:
        user_content = (
            "[Recent conversation context— for reference only]\n"
            f"{context}\n"
            "[End context]\n\n"
            + user_content
        )

    answer = await crew.get_response(user_content)
    if len(answer) > 1900:
        answer = answer[:1850] + "\n...(skrócono)"

    return answer