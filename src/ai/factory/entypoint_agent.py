from agentic_framework.core.agent import Agent
from agentic_framework.core.conversation import Conversation
from ..prompts import create_base_prompt
import os



SYSTEM_PROMPT = """

You can delegate tasks to other agents if you can specify the task clearly and the agent has the necessary tools to perform it. If you don't know the answer to a question, you can say you don't know or ask for more information.
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

