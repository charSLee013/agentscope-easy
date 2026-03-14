# -*- coding: utf-8 -*-
# pylint: disable=unused-argument
"""Tests for AgentScope training helpers."""
from __future__ import annotations

from types import ModuleType, SimpleNamespace
from typing import Any, Dict, List
from unittest import TestCase
from unittest.mock import patch

from agentscope.model import OpenAIChatModel, TrinityChatModel
from agentscope.tune import tune
from agentscope.tune._workflow import _validate_function_signature


async def correct_interface(task: Dict, model: TrinityChatModel) -> float:
    """Correct interface matching the workflow type."""
    return task["reward"]


async def wrong_interface_1(
    task: Dict,
    model: TrinityChatModel,
    extra: Any,
) -> float:
    """Wrong interface with an extra argument."""
    return 0.0


async def wrong_interface_2(task: Dict) -> float:
    """Wrong interface with a missing argument."""
    return 0.0


async def wrong_interface_3(task: List, model: TrinityChatModel) -> float:
    """Wrong interface with a wrong task type."""
    return 0.0


async def wrong_interface_4(task: Dict, model: OpenAIChatModel) -> float:
    """Wrong interface with a wrong model type."""
    return 0.0


async def wrong_interface_5(task: Dict, model: TrinityChatModel) -> str:
    """Wrong interface with a wrong return type."""
    return "0.0"


class AgentTuneTest(TestCase):
    """Test AgentScope training helpers."""

    def test_workflow_interface_validate(self) -> None:
        """Workflow signature validation should be strict."""
        self.assertTrue(_validate_function_signature(correct_interface))
        self.assertFalse(_validate_function_signature(wrong_interface_1))
        self.assertFalse(_validate_function_signature(wrong_interface_2))
        self.assertFalse(_validate_function_signature(wrong_interface_3))
        self.assertFalse(_validate_function_signature(wrong_interface_4))
        self.assertFalse(_validate_function_signature(wrong_interface_5))

    def test_tune_requires_trinity_runtime(self) -> None:
        """Calling tune() without Trinity-RFT should raise a clear error."""
        with patch.dict("sys.modules", {"omegaconf": None, "trinity": None}):
            with self.assertRaisesRegex(ImportError, "trinity-rft"):
                tune(correct_interface, "config.yaml")

    def test_tune_runs_with_fake_trinity_runtime(self) -> None:
        """tune() should adapt the workflow into Trinity config."""
        calls: dict[str, Any] = {}

        class FakeConfig:
            """Minimal Trinity config base."""

            def check_and_update(self) -> "FakeConfig":
                return self

        class FakeOmegaConf:
            """Minimal OmegaConf facade."""

            @staticmethod
            def structured(cls: type) -> type:
                return cls

            @staticmethod
            def load(path: str) -> dict[str, str]:
                return {"config_path": path}

            @staticmethod
            def merge(schema: type, yaml_config: dict[str, str]) -> dict[str, Any]:
                return {"schema": schema, "yaml_config": yaml_config}

            @staticmethod
            def to_object(config: dict[str, Any]) -> Any:
                instance = config["schema"]()
                instance.buffer = SimpleNamespace(
                    explorer_input=SimpleNamespace(
                        taskset=SimpleNamespace(
                            default_workflow_type=None,
                            workflow_args={},
                        ),
                        default_workflow_type=None,
                    ),
                )
                return instance

        def fake_run_stage(*, config: Any) -> str:
            calls["config"] = config
            return "stage-ok"

        trinity_module = ModuleType("trinity")
        trinity_cli = ModuleType("trinity.cli")
        trinity_cli_launcher = ModuleType("trinity.cli.launcher")
        trinity_cli_launcher.run_stage = fake_run_stage
        trinity_common = ModuleType("trinity.common")
        trinity_common_config = ModuleType("trinity.common.config")
        trinity_common_config.Config = FakeConfig
        omegaconf_module = ModuleType("omegaconf")
        omegaconf_module.OmegaConf = FakeOmegaConf

        with patch.dict(
            "sys.modules",
            {
                "trinity": trinity_module,
                "trinity.cli": trinity_cli,
                "trinity.cli.launcher": trinity_cli_launcher,
                "trinity.common": trinity_common,
                "trinity.common.config": trinity_common_config,
                "omegaconf": omegaconf_module,
            },
        ):
            tune(correct_interface, "config.yaml")

        self.assertIn("config", calls)
        config = calls["config"]
        self.assertEqual(
            config.buffer.explorer_input.default_workflow_type,
            "agentscope_workflow_adapter",
        )
        self.assertEqual(
            config.buffer.explorer_input.taskset.default_workflow_type,
            "agentscope_workflow_adapter",
        )
        self.assertIs(
            config.buffer.explorer_input.taskset.workflow_args[
                "workflow_func"
            ],
            correct_interface,
        )
