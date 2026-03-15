# -*- coding: utf-8 -*-
"""Context-local runtime configuration for AgentScope."""
from contextvars import ContextVar
from datetime import datetime

import shortuuid


def _generate_random_suffix(length: int) -> str:
    """Generate a random suffix."""
    return shortuuid.uuid()[:length]


def _default_project() -> str:
    """Build the default project name."""
    return "UnnamedProject_At" + datetime.now().strftime("%Y%m%d")


def _default_name() -> str:
    """Build the default run name."""
    return datetime.now().strftime("%H%M%S_") + _generate_random_suffix(4)


def _default_created_at() -> str:
    """Build the default creation timestamp."""
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]


class _RunConfig:
    """Thread- and async-safe runtime configuration wrapper."""

    def __init__(self) -> None:
        self._project = ContextVar("project", default=_default_project())
        self._name = ContextVar("name", default=_default_name())
        self._run_id = ContextVar("run_id", default=shortuuid.uuid())
        self._created_at = ContextVar(
            "created_at",
            default=_default_created_at(),
        )
        self._trace_enabled = ContextVar("trace_enabled", default=False)
        self._audio_playback_enabled = ContextVar(
            "audio_playback_enabled",
            default=False,
        )

    @property
    def project(self) -> str:
        return self._project.get()

    @project.setter
    def project(self, value: str) -> None:
        self._project.set(value)

    @property
    def name(self) -> str:
        return self._name.get()

    @name.setter
    def name(self, value: str) -> None:
        self._name.set(value)

    @property
    def run_id(self) -> str:
        return self._run_id.get()

    @run_id.setter
    def run_id(self, value: str) -> None:
        self._run_id.set(value)

    @property
    def created_at(self) -> str:
        return self._created_at.get()

    @created_at.setter
    def created_at(self, value: str) -> None:
        self._created_at.set(value)

    @property
    def trace_enabled(self) -> bool:
        return self._trace_enabled.get()

    @trace_enabled.setter
    def trace_enabled(self, value: bool) -> None:
        self._trace_enabled.set(value)

    @property
    def audio_playback_enabled(self) -> bool:
        return self._audio_playback_enabled.get()

    @audio_playback_enabled.setter
    def audio_playback_enabled(self, value: bool) -> None:
        self._audio_playback_enabled.set(value)


def _build_run_config() -> _RunConfig:
    """Create a fresh run configuration container."""
    return _RunConfig()
