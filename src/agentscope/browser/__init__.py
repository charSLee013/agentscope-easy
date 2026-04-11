# -*- coding: utf-8 -*-
"""Browser fallback public exports."""

from ._service import BrowserFetchResult, BrowserPageService
from ._tools import fetch_webpage

__all__ = [
    "BrowserFetchResult",
    "BrowserPageService",
    "fetch_webpage",
]
