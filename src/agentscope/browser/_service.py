# -*- coding: utf-8 -*-
"""Service layer for browser-backed webpage fetching."""
from __future__ import annotations

from dataclasses import dataclass
from html import unescape
import re
from typing import Callable

import requests


_DEFAULT_USER_AGENT = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/134.0.0.0 Safari/537.36"
)
_DEFAULT_BROWSER_CHANNELS = ("chrome", "msedge", "chromium")
_CHALLENGE_MARKERS = (
    "cdn-cgi/challenge-platform",
    "cf-chl",
    "cf-mitigated",
    "attention required! | cloudflare",
    "just a moment...",
    "challenge-platform",
    "invisible.js",
)


@dataclass(eq=True)
class BrowserFetchResult:
    """Normalized fetch result from either HTTP or browser path."""

    url: str
    title: str
    text: str
    html: str
    status_code: int | None
    fetch_mode: str
    backend: str
    challenge_detected: bool


class BrowserPageService:
    """Fetch webpage text with HTTP fast path and browser fallback."""

    def __init__(
        self,
        request_timeout_s: int = 30,
        browser_timeout_ms: int = 45_000,
        browser_channels: tuple[str, ...] = _DEFAULT_BROWSER_CHANNELS,
        user_agent: str = _DEFAULT_USER_AGENT,
        _requests_get: Callable | None = None,
    ) -> None:
        self.request_timeout_s = request_timeout_s
        self.browser_timeout_ms = browser_timeout_ms
        self.browser_channels = browser_channels
        self.user_agent = user_agent
        self._requests_get = _requests_get or requests.get

    def fetch_page(
        self,
        url: str,
        max_text_chars: int = 5000,
        force_browser: bool = False,
    ) -> BrowserFetchResult:
        """Fetch one webpage and escalate to browser when challenge detected."""
        http_error: Exception | None = None
        if not force_browser:
            try:
                result = self._fetch_with_http(
                    url,
                    max_text_chars=max_text_chars,
                )
            except Exception as error:  # noqa: BLE001
                http_error = error
            else:
                if not result.challenge_detected:
                    return result

        try:
            return self._fetch_with_playwright(url, max_text_chars=max_text_chars)
        except ImportError as error:
            detail = (
                f" HTTP fast path failed with: {http_error}."
                if http_error is not None
                else ""
            )
            raise ImportError(self._browser_install_message() + detail) from error

    def tool_functions(self) -> tuple:
        """Return the tool surface for Toolkit wiring."""
        from ._tools import fetch_webpage

        return (fetch_webpage,)

    def _fetch_with_http(
        self,
        url: str,
        max_text_chars: int,
    ) -> BrowserFetchResult:
        response = self._requests_get(
            url,
            timeout=self.request_timeout_s,
            headers={"User-Agent": self.user_agent},
        )
        html = getattr(response, "text", "") or ""
        status_code = getattr(response, "status_code", None)
        challenge = _looks_like_challenge(status_code, html)
        title = _extract_title(html)
        text = _html_to_text(html, max_text_chars=max_text_chars)
        return BrowserFetchResult(
            url=getattr(response, "url", url),
            title=title,
            text=text,
            html=html,
            status_code=status_code,
            fetch_mode="http",
            backend="http",
            challenge_detected=challenge,
        )

    def _fetch_with_playwright(
        self,
        url: str,
        max_text_chars: int,
    ) -> BrowserFetchResult:
        try:
            from playwright.sync_api import sync_playwright
        except ImportError as error:
            raise ImportError("playwright is required") from error

        errors: list[str] = []
        with sync_playwright() as playwright:
            for channel in self.browser_channels:
                browser = None
                try:
                    browser = self._launch_browser(playwright, channel)
                    context = browser.new_context(
                        ignore_https_errors=True,
                        user_agent=self.user_agent,
                        viewport={"width": 1440, "height": 900},
                        locale="en-US",
                    )
                    try:
                        page = context.new_page()
                        response = page.goto(
                            url,
                            wait_until="domcontentloaded",
                            timeout=self.browser_timeout_ms,
                        )
                        html = page.content()
                        text = page.locator("body").inner_text(
                            timeout=15_000,
                        )
                        title = page.title()
                    finally:
                        context.close()

                    return BrowserFetchResult(
                        url=page.url,
                        title=title,
                        text=text[:max_text_chars].strip(),
                        html=html,
                        status_code=response.status if response else None,
                        fetch_mode="browser",
                        backend=f"playwright:{channel}",
                        challenge_detected=True,
                    )
                except Exception as error:  # noqa: BLE001
                    errors.append(f"{channel}: {error}")
                finally:
                    if browser is not None:
                        browser.close()

        error_summary = "; ".join(errors) or "no available browser channels"
        raise RuntimeError(
            "Playwright browser fetch failed. "
            f"{error_summary}. {self._browser_install_message()}",
        )

    def _launch_browser(
        self,
        playwright: object,
        channel: str,
    ) -> object:
        launch_kwargs: dict = {
            "headless": True,
        }

        if channel in {"chrome", "msedge"}:
            launch_kwargs.update(
                {
                    "channel": channel,
                    "ignore_default_args": ["--headless=old"],
                    "args": [
                        "--headless=new",
                        "--disable-blink-features=AutomationControlled",
                    ],
                },
            )
        else:
            launch_kwargs["args"] = [
                "--disable-blink-features=AutomationControlled",
            ]

        return playwright.chromium.launch(**launch_kwargs)

    @staticmethod
    def _browser_install_message() -> str:
        return (
            "Browser fallback requires Playwright. Install it with "
            "`pip install agentscope[browser]`, then install a browser with "
            "`python -m playwright install`. For the best current fallback "
            "path, make sure Chrome or Microsoft Edge is available locally."
        )


def _extract_title(html: str) -> str:
    """Extract the HTML title text."""
    match = re.search(r"<title[^>]*>(.*?)</title>", html, flags=re.I | re.S)
    if not match:
        return ""
    return unescape(_normalize_text(match.group(1)))


def _html_to_text(html: str, max_text_chars: int = 5000) -> str:
    """Convert HTML into compact plain text."""
    raw = re.sub(r"<script.*?</script>", " ", html, flags=re.I | re.S)
    raw = re.sub(r"<style.*?</style>", " ", raw, flags=re.I | re.S)
    raw = re.sub(r"<[^>]+>", " ", raw)
    text = unescape(_normalize_text(raw))
    return text[:max_text_chars]


def _looks_like_challenge(status_code: int | None, html: str) -> bool:
    """Detect Cloudflare or similar challenge pages."""
    if status_code not in {403, 429, 503}:
        return False

    lowered = html.lower()
    return any(marker in lowered for marker in _CHALLENGE_MARKERS)


def _normalize_text(value: str) -> str:
    """Collapse whitespace while keeping readable spacing."""
    return re.sub(r"\s+", " ", value).strip()
