# -*- coding: utf-8 -*-
"""The TTS response module."""

from dataclasses import dataclass, field
from typing import Literal

from .._utils._common import _get_timestamp
from .._utils._mixin import DictMixin
from ..message import AudioBlock
from ..types import JSONSerializableObject


@dataclass
class TTSUsage(DictMixin):
    """The usage of a TTS model API invocation."""

    input_tokens: int
    output_tokens: int
    time: float
    type: Literal["tts"] = field(default_factory=lambda: "tts")


@dataclass
class TTSResponse(DictMixin):
    """The response of TTS models."""

    content: AudioBlock | None
    id: str = field(default_factory=lambda: _get_timestamp(True))
    created_at: str = field(default_factory=_get_timestamp)
    type: Literal["tts"] = field(default_factory=lambda: "tts")
    usage: TTSUsage | None = field(default_factory=lambda: None)
    metadata: dict[str, JSONSerializableObject] | None = field(
        default_factory=lambda: None,
    )
    is_last: bool = True

