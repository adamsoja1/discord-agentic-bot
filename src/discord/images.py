"""Convert supported Discord image attachments to SDK image inputs."""

from pathlib import PurePosixPath
from typing import Iterable

import discord
from agentic_framework import ImageInput

SUPPORTED_IMAGE_TYPES = {"image/png", "image/jpeg", "image/webp", "image/gif"}
SUPPORTED_IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".webp", ".gif"}


def collect_image_inputs(attachments: Iterable[discord.Attachment]) -> list[ImageInput]:
    images = []
    for attachment in attachments:
        media_type = (attachment.content_type or "").split(";", 1)[0].strip().lower()
        extension = PurePosixPath(attachment.filename).suffix.lower()
        if media_type in SUPPORTED_IMAGE_TYPES or (
            not media_type and extension in SUPPORTED_IMAGE_EXTENSIONS
        ):
            images.append(ImageInput(url=attachment.url))
    return images
