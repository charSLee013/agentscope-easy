# -*- coding: utf-8 -*-
"""Entrypoint for training AgentScope workflows."""
from __future__ import annotations

from dataclasses import dataclass

from ._workflow import WorkflowType, _validate_function_signature


def tune(workflow_func: WorkflowType, config_path: str) -> None:
    """Train an AgentScope workflow with Trinity-RFT.

    Args:
        workflow_func (`WorkflowType`):
            The async workflow function to train.
        config_path (`str`):
            Path to the Trinity-RFT YAML configuration file.
    """
    try:
        from omegaconf import OmegaConf
        from trinity.cli.launcher import run_stage
        from trinity.common.config import Config
    except ImportError as exc:
        raise ImportError(
            "Trinity-RFT is not installed. Please install it with "
            "`pip install trinity-rft`.",
        ) from exc

    if not _validate_function_signature(workflow_func):
        raise ValueError(
            "Invalid workflow function signature, please check the types of "
            "your workflow input and output.",
        )

    @dataclass
    class TuneConfig(Config):
        """Configuration wrapper for Trinity-RFT workflow training."""

        def to_trinity_config(self, workflow: WorkflowType) -> Config:
            """Convert config to the Trinity-RFT adapter form."""
            workflow_name = "agentscope_workflow_adapter"
            self.buffer.explorer_input.taskset.default_workflow_type = (
                workflow_name
            )
            self.buffer.explorer_input.default_workflow_type = workflow_name
            self.buffer.explorer_input.taskset.workflow_args[
                "workflow_func"
            ] = workflow
            return self.check_and_update()

        @classmethod
        def load_config(cls, path: str) -> "TuneConfig":
            """Load a training config from YAML."""
            schema = OmegaConf.structured(cls)
            yaml_config = OmegaConf.load(path)
            try:
                config = OmegaConf.merge(schema, yaml_config)
                return OmegaConf.to_object(config)
            except Exception as exc:  # pragma: no cover - omegaconf surface
                raise ValueError(
                    f"Invalid configuration: {exc}",
                ) from exc

    run_stage(
        config=TuneConfig.load_config(config_path).to_trinity_config(
            workflow_func,
        ),
    )
