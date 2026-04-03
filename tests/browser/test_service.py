# -*- coding: utf-8 -*-
"""Service-layer behavior for browser fallback."""
from __future__ import annotations

from unittest.mock import patch

from agentscope.browser import BrowserFetchResult, BrowserPageService


class _FakeResponse:
    def __init__(
        self,
        text: str,
        status_code: int = 200,
        url: str = "https://example.com",
        content_type: str = "text/html; charset=utf-8",
        server: str | None = None,
    ) -> None:
        self.text = text
        self.status_code = status_code
        self.url = url
        self.headers = {
            "content-type": content_type,
        }
        if server:
            self.headers["server"] = server


def test_http_success_stays_on_fast_path() -> None:
    """Normal pages should return from the HTTP path without browser fallback."""
    service = BrowserPageService(
        _requests_get=lambda *_args, **_kwargs: _FakeResponse(
            "<html><title>Example</title><body>Hello browser fallback</body></html>",
        ),
    )

    result = service.fetch_page("https://example.com")

    assert result.fetch_mode == "http"
    assert result.backend == "http"
    assert result.status_code == 200
    assert result.title == "Example"
    assert "Hello browser fallback" in result.text
    assert result.challenge_detected is False


def test_challenge_response_falls_back_to_browser() -> None:
    """Challenge pages should escalate into the browser backend."""
    service = BrowserPageService(
        _requests_get=lambda *_args, **_kwargs: _FakeResponse(
            (
                "<html><head><title>Just a moment...</title></head>"
                "<body><script src='/cdn-cgi/challenge-platform/invisible.js'></script></body></html>"
            ),
            status_code=403,
            server="cloudflare",
        ),
    )

    expected = BrowserFetchResult(
        url=(
            "https://openai.com/business/guides-and-resources/"
            "a-practical-guide-to-building-ai-agents/"
        ),
        title="A practical guide to building agents | OpenAI",
        text="Introduction to the agent guide",
        html="<html>resolved</html>",
        status_code=200,
        fetch_mode="browser",
        backend="playwright:chrome",
        challenge_detected=True,
    )

    with patch.object(
        service,
        "_fetch_with_playwright",
        return_value=expected,
    ) as mocked_browser:
        result = service.fetch_page(expected.url)

    mocked_browser.assert_called_once_with(expected.url, max_text_chars=5000)
    assert result == expected


def test_browser_dependency_error_is_human_readable() -> None:
    """Missing browser runtime should surface with installation guidance."""
    service = BrowserPageService(
        _requests_get=lambda *_args, **_kwargs: _FakeResponse(
            (
                "<html><head><title>Blocked</title></head>"
                "<body>cdn-cgi/challenge-platform invisible.js</body></html>"
            ),
            status_code=403,
            server="cloudflare",
        ),
    )

    with patch.object(
        service,
        "_fetch_with_playwright",
        side_effect=ImportError("No module named 'playwright'"),
    ):
        try:
            service.fetch_page("https://openai.com/index/introducing-gpt-5/")
        except ImportError as error:
            message = str(error)
        else:
            raise AssertionError("Expected ImportError was not raised")

    assert "pip install agentscope[browser]" in message
    assert "python -m playwright install" in message


def test_request_error_falls_back_to_browser() -> None:
    """Request-layer hard failures should also escalate to the browser path."""
    service = BrowserPageService(
        _requests_get=lambda *_args, **_kwargs: (_ for _ in ()).throw(
            RuntimeError("socket timeout"),
        ),
    )
    expected = BrowserFetchResult(
        url="https://openai.com/index/introducing-gpt-5/",
        title="Introducing GPT-5 | OpenAI",
        text="Fallback recovered content",
        html="<html>ok</html>",
        status_code=200,
        fetch_mode="browser",
        backend="playwright:chrome",
        challenge_detected=True,
    )

    with patch.object(
        service,
        "_fetch_with_playwright",
        return_value=expected,
    ) as mocked_browser:
        result = service.fetch_page(expected.url)

    mocked_browser.assert_called_once_with(expected.url, max_text_chars=5000)
    assert result == expected


def test_challenge_detection_is_narrow() -> None:
    """Challenge detection should not trigger on normal successful pages."""
    service = BrowserPageService(
        _requests_get=lambda *_args, **_kwargs: _FakeResponse(
            "<html><title>Anthropic</title><body>Built a multi-agent research system</body></html>",
            status_code=200,
            server="cloudflare",
        ),
    )

    result = service.fetch_page(
        "https://www.anthropic.com/engineering/built-multi-agent-research-system",
    )

    assert result.fetch_mode == "http"
    assert result.challenge_detected is False
