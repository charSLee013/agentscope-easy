# -*- coding: utf-8 -*-
"""Packaging boundary checks for browser fallback."""
from __future__ import annotations

from pathlib import Path


def test_browser_extra_stays_optional() -> None:
    """Browser runtime should stay out of base/full and exist in dev."""
    pyproject = Path(__file__).resolve().parents[2] / "pyproject.toml"
    text = pyproject.read_text(encoding="utf-8")

    assert 'browser = ["playwright' in text
    assert 'dev = [' in text
    assert '"agentscope[browser]"' in text
    full_section = text.split("full = [", maxsplit=1)[1].split("]", maxsplit=1)[0]
    assert '"agentscope[browser]"' not in full_section
