# -*- coding: utf-8 -*-
"""Browser fallback tool functions."""
from __future__ import annotations

import asyncio

from agentscope.message import TextBlock
from agentscope.tool import ToolResponse


async def fetch_webpage(
    service: object,
    url: str,
    max_text_chars: int = 5000,
) -> ToolResponse:
    """Fetch webpage text with automatic browser fallback."""
    result = await asyncio.to_thread(
        service.fetch_page,
        url,
        max_text_chars,
    )
    text = "\n".join(
        [
            f"URL: {result.url}",
            f"Fetch mode: {result.fetch_mode}",
            f"Backend: {result.backend}",
            f"HTTP status: {result.status_code}",
            f"Title: {result.title or '<empty>'}",
            "Text:",
            result.text or "<empty>",
        ],
    )
    return ToolResponse(content=[TextBlock(type="text", text=text)])


__all__ = ["fetch_webpage"]
