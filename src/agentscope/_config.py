# -*- coding: utf-8 -*-
"""Compatibility module exposing runtime config through module attributes."""
from __future__ import annotations

import sys
from types import ModuleType

from ._run_config import _build_run_config


_CONFIG = _build_run_config()

# These module attributes are runtime-managed by `_ConfigModule`, but keeping
# concrete names here helps static analyzers understand the public surface.
project = _CONFIG.project
name = _CONFIG.name
run_id = _CONFIG.run_id
created_at = _CONFIG.created_at
trace_enabled = _CONFIG.trace_enabled
audio_playback_enabled = _CONFIG.audio_playback_enabled


class _ConfigModule(ModuleType):
    """Bridge module attributes onto the context-local config object."""

    @property
    def project(self) -> str:
        return _CONFIG.project

    @project.setter
    def project(self, value: str) -> None:
        _CONFIG.project = value

    @property
    def name(self) -> str:
        return _CONFIG.name

    @name.setter
    def name(self, value: str) -> None:
        _CONFIG.name = value

    @property
    def run_id(self) -> str:
        return _CONFIG.run_id

    @run_id.setter
    def run_id(self, value: str) -> None:
        _CONFIG.run_id = value

    @property
    def created_at(self) -> str:
        return _CONFIG.created_at

    @created_at.setter
    def created_at(self, value: str) -> None:
        _CONFIG.created_at = value

    @property
    def trace_enabled(self) -> bool:
        return _CONFIG.trace_enabled

    @trace_enabled.setter
    def trace_enabled(self, value: bool) -> None:
        _CONFIG.trace_enabled = value

    @property
    def audio_playback_enabled(self) -> bool:
        return _CONFIG.audio_playback_enabled

    @audio_playback_enabled.setter
    def audio_playback_enabled(self, value: bool) -> None:
        _CONFIG.audio_playback_enabled = value


sys.modules[__name__].__class__ = _ConfigModule
