# -*- coding: utf-8 -*-
"""Tests for the wave-036 real runtime validation helpers."""
from __future__ import annotations

import importlib.util
import os
from pathlib import Path
from tempfile import TemporaryDirectory
from types import ModuleType
from unittest import TestCase
from unittest.mock import patch

from agentscope.message import Msg, ToolResultBlock, ToolUseBlock


MODULE_PATH = (
    Path(__file__).resolve().parents[1]
    / "specs/036-core-agent-tool-mcp-runtime/real_runtime_validation.py"
)


def _load_module() -> ModuleType:
    spec = importlib.util.spec_from_file_location(
        "wave036_real_runtime_validation",
        MODULE_PATH,
    )
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class RealRuntimeValidationSupportTest(TestCase):
    """Contract tests for the wave-036 runtime validation helper."""

    def test_env_file_overrides_shell_openai_settings(
        self,
    ) -> None:
        """The validation script should read the repo `.env` as truth."""
        module = _load_module()

        with TemporaryDirectory() as temp_dir:
            env_file = Path(temp_dir) / ".env"
            env_file.write_text(
                "\n".join(
                    [
                        "OPENAI_API_KEY=file-key",
                        "OPENAI_MODEL=file-model",
                        "OPENAI_BASE_URL=https://example.invalid/v1",
                    ],
                ),
                encoding="utf-8",
            )

            with patch.dict(
                os.environ,
                {
                    "OPENAI_API_KEY": "shell-key",
                    "OPENAI_MODEL": "shell-model",
                    "OPENAI_BASE_URL": "https://shell.invalid/v1",
                },
            ):
                settings = module.load_openai_runtime_settings(env_file)

        self.assertEqual(settings.api_key, "file-key")
        self.assertEqual(settings.model_name, "file-model")
        self.assertEqual(settings.base_url, "https://example.invalid/v1")

    def test_collect_tool_trace_keeps_use_and_result_events(self) -> None:
        """The validation evidence should preserve the MCP tool trace."""
        module = _load_module()
        messages = [
            Msg(
                "assistant",
                [
                    ToolUseBlock(
                        type="tool_use",
                        id="call-1",
                        name="multiply",
                        input={"c": 2345, "d": 3456},
                    ),
                    ToolUseBlock(
                        type="tool_use",
                        id="call-2",
                        name="add",
                        input={"a": 8104320, "b": 4567},
                    ),
                ],
                "assistant",
            ),
            Msg(
                "system",
                [
                    ToolResultBlock(
                        type="tool_result",
                        id="call-1",
                        name="multiply",
                        output="8104320",
                    ),
                ],
                "system",
            ),
        ]

        self.assertEqual(
            module.collect_tool_trace(messages),
            [
                {"event": "tool_use", "name": "multiply"},
                {"event": "tool_use", "name": "add"},
                {"event": "tool_result", "name": "multiply"},
            ],
        )
