# -*- coding: utf-8 -*-
"""Host-level import and export wiring for browser fallback."""
from __future__ import annotations

import agentscope
from agentscope.browser import BrowserPageService


def test_agentscope_exports_browser_module() -> None:
    """`import agentscope` should expose the browser public module."""
    assert hasattr(agentscope, "browser")
    assert hasattr(agentscope.browser, "BrowserPageService")


def test_service_exposes_tool_surface() -> None:
    """The public service should provide a minimal tool surface."""
    service = BrowserPageService(
        _requests_get=lambda *_args, **_kwargs: type(
            "Response",
            (),
            {
                "text": "<html><title>OK</title><body>ok</body></html>",
                "status_code": 200,
                "url": "https://example.com",
                "headers": {"content-type": "text/html; charset=utf-8"},
            },
        )(),
    )

    tool_names = [tool.__name__ for tool in service.tool_functions()]
    assert tool_names == ["fetch_webpage"]
