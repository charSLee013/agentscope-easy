# -*- coding: utf-8 -*-
"""Convert AgentScope content blocks into tracing-friendly parts."""
from typing import Any

from ..message import ContentBlock
from ._utils import _serialize_to_str


def _convert_media_block(
    source: dict[str, Any],
    modality: str,
) -> dict[str, Any] | None:
    """Convert media source blocks into a normalized tracing payload."""
    source_type = source.get("type")

    if source_type == "url":
        return {
            "type": "uri",
            "uri": source.get("url", ""),
            "modality": modality,
        }

    if source_type == "base64":
        media_type = source.get("media_type")
        if not media_type:
            defaults = {
                "image": "image/jpeg",
                "audio": "audio/wav",
                "video": "video/mp4",
            }
            media_type = defaults.get(modality, "application/octet-stream")
        return {
            "type": "blob",
            "content": source.get("data", ""),
            "media_type": media_type,
            "modality": modality,
        }

    return None


def _convert_block_to_part(block: ContentBlock) -> dict[str, Any] | None:
    """Convert one message block into a normalized tracing part."""
    block_type = block.get("type")

    if block_type == "text":
        return {
            "type": "text",
            "content": block.get("text", ""),
        }

    if block_type == "thinking":
        return {
            "type": "reasoning",
            "content": block.get("thinking", ""),
        }

    if block_type == "tool_use":
        return {
            "type": "tool_call",
            "id": block.get("id", ""),
            "name": block.get("name", ""),
            "arguments": block.get("input", {}),
        }

    if block_type == "tool_result":
        return {
            "type": "tool_call_response",
            "id": block.get("id", ""),
            "response": _serialize_to_str(block.get("output", "")),
        }

    if block_type in {"image", "audio", "video"}:
        source = block.get("source", {})
        if isinstance(source, dict):
            return _convert_media_block(source, block_type)

    return None
