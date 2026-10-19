import asyncio
import importlib
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

from agentic_framework import ImageInput
from agentic_framework.core.stream_events import FinalAnswerEvent
from src.discord.images import collect_image_inputs


def attachment(filename="photo.png", content_type="image/png"):
    return SimpleNamespace(
        filename=filename,
        content_type=content_type,
        url="https://cdn.discordapp.com/attachments/1/2/" + filename,
    )


def test_collects_multiple_images_and_ignores_other_files():
    inputs = collect_image_inputs(
        [
            attachment(),
            attachment("photo.JPG", None),
            attachment("photo.webp", "image/webp"),
            attachment("photo.gif", "image/gif"),
            attachment("notes.txt", "text/plain"),
            attachment("pretend.png", "application/pdf"),
            attachment("drawing.svg", "image/svg+xml"),
        ]
    )
    assert len(inputs) == 4
    assert all(isinstance(image, ImageInput) for image in inputs)
    assert inputs[0].url.endswith("/photo.png")


@pytest.fixture
def app(monkeypatch):
    monkeypatch.setenv("DISCORD_TOKEN", "test-token")
    return importlib.import_module("src.discord.app")


def test_discord_response_passes_attachments_to_agents(app, monkeypatch):
    received = {}

    async def answer(**kwargs):
        received.update(kwargs)
        yield FinalAnswerEvent(agent_name="test", answer="A cat")

    monkeypatch.setattr(app, "answer_discord_question", answer)
    monkeypatch.setattr(
        app, "_collect_recent_context", AsyncMock(return_value="context")
    )
    reply = SimpleNamespace(content="Thinking...", edit=AsyncMock())
    message = SimpleNamespace(
        attachments=[attachment()], reply=AsyncMock(return_value=reply)
    )
    asyncio.run(app._send_ai_response(message, "What is this?"))
    assert received["question"] == "What is this?"
    assert received["context"] == "context"
    assert received["images"][0].url == message.attachments[0].url
    assert reply.edit.call_args.kwargs["content"] == "A cat"


def test_ask_accepts_image_without_text(app, monkeypatch):
    send = AsyncMock()
    monkeypatch.setattr(app, "_send_ai_response", send)
    message = SimpleNamespace(attachments=[attachment()])
    ctx = SimpleNamespace(message=message, reply=AsyncMock())
    asyncio.run(app.ask_command.callback(ctx, question=""))
    send.assert_awaited_once_with(message, "")
    ctx.reply.assert_not_awaited()


@pytest.mark.parametrize(
    "guild,mentioned", [(None, False), (SimpleNamespace(id=123), True)]
)
def test_image_only_dm_and_mention_reach_response(app, monkeypatch, guild, mentioned):
    send = AsyncMock()
    monkeypatch.setattr(app, "_send_ai_response", send)
    monkeypatch.setattr(app, "_bot_was_mentioned", lambda message: mentioned)
    message = SimpleNamespace(
        content="",
        author=SimpleNamespace(bot=False),
        guild=guild,
        channel=SimpleNamespace(id=456),
        attachments=[attachment()],
    )
    asyncio.run(app.on_message(message))
    send.assert_awaited_once_with(message, "")


@pytest.mark.parametrize(
    "question,images",
    [
        ("", [ImageInput("https://example.com/a.png")]),
        ("Explain", []),
        (
            "Compare",
            [
                ImageInput("https://example.com/a.png"),
                ImageInput("https://example.com/b.png"),
            ],
        ),
    ],
)
def test_swarm_forwards_images_and_context(monkeypatch, question, images):
    from src.ai.factory import swarm

    received = {}

    class FakeCrew:
        def __init__(self, **kwargs):
            pass

        async def invoke(self, content, *, images):
            received.update(content=content, images=images)
            yield FinalAnswerEvent(agent_name="test", answer="ok")

    monkeypatch.setattr(swarm, "Crew", FakeCrew)

    async def collect():
        return [
            event
            async for event in swarm.answer_discord_question(
                question, "recent", images=images
            )
        ]

    events = asyncio.run(collect())
    assert events[-1].answer == "ok"
    assert received["images"] == images
    assert "recent" in received["content"]
    assert (question or "Describe the attached images.") in received["content"]


def test_swarm_rejects_empty_input():
    from src.ai.factory.swarm import answer_discord_question

    async def collect():
        return [event async for event in answer_discord_question("")]

    events = asyncio.run(collect())
    assert isinstance(events[0], FinalAnswerEvent)
    assert "Nie rozumiem" in events[0].answer
