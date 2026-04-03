# -*- coding: utf-8 -*-
"""Toolkit integration for browser fallback tools."""
from __future__ import annotations

from unittest import IsolatedAsyncioTestCase

from agentscope.browser import BrowserPageService, fetch_webpage
from agentscope.message import ToolUseBlock
from agentscope.tool import Toolkit


class BrowserToolTest(IsolatedAsyncioTestCase):
    """Tool-level tests for browser page fetching."""

    async def asyncSetUp(self) -> None:
        self.service = BrowserPageService(
            _requests_get=lambda *_args, **_kwargs: type(
                "Response",
                (),
                {
                    "text": (
                        "<html><title>Example</title>"
                        "<body>Hello browser tool</body></html>"
                    ),
                    "status_code": 200,
                    "url": "https://example.com",
                    "headers": {"content-type": "text/html; charset=utf-8"},
                },
            )(),
        )
        self.toolkit = Toolkit()
        self.toolkit.register_tool_function(
            fetch_webpage,
            preset_kwargs={"service": self.service},
        )

    async def test_preset_service_argument_is_hidden_from_schema(self) -> None:
        """Toolkit schemas should not expose the injected service argument."""
        schema = self.toolkit.get_json_schemas()[0]
        assert schema["function"]["name"] == "fetch_webpage"
        assert (
            "service"
            not in schema["function"]["parameters"]["properties"]
        )

    async def test_tool_executes_with_service_injection(self) -> None:
        """Browser fetch tool should execute successfully through Toolkit."""
        result = await self.toolkit.call_tool_function(
            ToolUseBlock(
                type="tool_use",
                id="browser-1",
                name="fetch_webpage",
                input={"url": "https://example.com"},
            ),
        )

        chunks = [chunk async for chunk in result]
        text = chunks[-1].content[0]["text"]
        assert "Fetch mode: http" in text
        assert "Title: Example" in text
        assert "Hello browser tool" in text
