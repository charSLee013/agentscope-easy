# -*- coding: utf-8 -*-
"""Tests for environment-driven console output defaults."""
from __future__ import annotations

from ._shared import build_host_agent


def test_agent_respects_disable_console_env(
    monkeypatch,
) -> None:
    """Agent should default to silent mode when env flag is set."""
    monkeypatch.setenv("AGENTSCOPE_DISABLE_CONSOLE_OUTPUT", "true")

    agent = build_host_agent()

    assert agent._disable_console_output is True
