# -*- coding: utf-8 -*-
"""Shared helpers for A2UI sample tests."""
from __future__ import annotations

import importlib.util
import sys
import types
from contextlib import contextmanager
from pathlib import Path
from typing import Iterator

from a2a.types import AgentCard, AgentExtension

SAMPLE_DIR = (
    Path(__file__).resolve().parents[1]
    / "examples"
    / "agent"
    / "a2ui_agent"
    / "samples"
    / "general_agent"
)
SKILL_DIR = SAMPLE_DIR / "skills" / "A2UI_response_generator"
SAMPLE_AGENT_CARD_PATH = SAMPLE_DIR / "agent_card.py"
TEST_A2UI_EXTENSION_URI = "https://example.com/a2ui-extension"


def purge_a2ui_skill_modules() -> None:
    """Remove cached A2UI skill modules to exercise import-time behavior."""
    for module_name in list(sys.modules):
        if module_name == "skills" or module_name.startswith(
            "skills.A2UI_response_generator",
        ):
            sys.modules.pop(module_name, None)


@contextmanager
def sample_on_path() -> Iterator[None]:
    """Temporarily add the A2UI sample package root to sys.path."""
    sys.path.insert(0, str(SAMPLE_DIR))
    try:
        yield
    finally:
        sys.path.remove(str(SAMPLE_DIR))


def _build_stub_a2ui_module() -> types.ModuleType:
    """Create the stub module required by the sample agent card."""
    stub_module = types.ModuleType("a2ui.extension.a2ui_extension")
    stub_module.A2UI_MIME_TYPE = "application/vnd.a2ui+json"
    stub_module.MIME_TYPE_KEY = "mimeType"
    stub_module.A2UI_EXTENSION_URI = TEST_A2UI_EXTENSION_URI

    def get_a2ui_agent_extension() -> AgentExtension:
        return AgentExtension(uri=TEST_A2UI_EXTENSION_URI)

    stub_module.get_a2ui_agent_extension = get_a2ui_agent_extension
    return stub_module


@contextmanager
def stubbed_a2ui_extension() -> Iterator[None]:
    """Temporarily stub the A2UI extension module required by the sample."""
    module_names = (
        "a2ui",
        "a2ui.extension",
        "a2ui.extension.a2ui_extension",
    )
    old_modules = {name: sys.modules.get(name) for name in module_names}
    sys.modules["a2ui"] = types.ModuleType("a2ui")
    sys.modules["a2ui.extension"] = types.ModuleType("a2ui.extension")
    sys.modules["a2ui.extension.a2ui_extension"] = _build_stub_a2ui_module()
    spec = importlib.util.spec_from_file_location(
        "test_sample_agent_card",
        SAMPLE_AGENT_CARD_PATH,
    )
    assert spec is not None and spec.loader is not None
    try:
        yield
    finally:
        for name, old_module in old_modules.items():
            if old_module is None:
                sys.modules.pop(name, None)
            else:
                sys.modules[name] = old_module


def load_sample_agent_card() -> AgentCard:
    """Load the real sample agent card with a stubbed A2UI dependency."""
    spec = importlib.util.spec_from_file_location(
        "test_sample_agent_card",
        SAMPLE_AGENT_CARD_PATH,
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    with stubbed_a2ui_extension():
        spec.loader.exec_module(module)
    return module.agent_card
