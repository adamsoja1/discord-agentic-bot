from agentic_framework.core.agent import Agent
from agentic_framework.core.conversation import Conversation
from ..prompts import create_base_prompt


SYSTEM_PROMPT = """
You are the first responder for Discord messages.
Answer directly for conversation, writing, summarization, coding help, explanations, planning, and lightweight reasoning.
Delegate when a request needs current web information, Discord server data, member/channel lookups, recent channel messages, or text-channel creation.
For verifiable facts from tools or the web, include compact source links.
If the request is ambiguous, ask one short clarifying question.
"""

def build_entrypoint_agent(model: str) -> Agent:
    """
    Builds an entry point agent that can be used to start a conversation.
    """
    return Agent(
        name="ZIOMAL",
        description="An agent that serves as the entry point for a conversation.",
        system_prompt=create_base_prompt()+SYSTEM_PROMPT,
        conversation=Conversation(id='0'),
        model=model,
        max_iterations=10
    )
