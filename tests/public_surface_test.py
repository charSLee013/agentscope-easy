# -*- coding: utf-8 -*-
"""Public surface regression tests for the wave-1 hard cut."""
from __future__ import annotations

import agentscope.agent
import agentscope.realtime
import agentscope.tool


def test_agent_public_surface_switches_to_realtime() -> None:
    assert hasattr(agentscope.agent, "RealtimeAgent")
    assert not hasattr(agentscope.agent, "SubAgentBase")


def test_tool_public_surface_hides_legacy_search_exports() -> None:
    for attr in (
        "search_bing",
        "search_sogou",
        "search_github",
        "search_wiki",
    ):
        assert not hasattr(agentscope.tool, attr)


def test_realtime_module_is_exposed_from_top_level_package() -> None:
    assert hasattr(agentscope.realtime, "OpenAIRealtimeModel")
