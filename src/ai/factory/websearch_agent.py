from agentic_framework.core.agent import Agent
from agentic_framework.core.conversation import Conversation
from ..prompts import create_base_prompt

SYSTEM_PROMPT = """
You are a web, research, gaming, and technical lookup helper.
Use web search when the user needs current facts, external sources, documentation, guides, patch notes, or page content.
If you don't know the answer to a question, you can say you don't know or ask for more information.
For verifiable information, include concise source links when available.
"""

def build_websearch_agent(model: str) -> Agent:
    """
    Builds a web search agent that can be used to search the web.
    """
    return Agent(
        name="WebSearchAgent",
        description="An agent that serves as the web search agent.",
        system_prompt=create_base_prompt() + SYSTEM_PROMPT,
        conversation=Conversation(id='0'),
        model=model,
        web_search=True,
        max_iterations=20,
    )
