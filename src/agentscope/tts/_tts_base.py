# -*- coding: utf-8 -*-
"""The TTS model base class."""

from abc import ABC, abstractmethod
from typing import Any, AsyncGenerator

from ..message import Msg
from ._tts_response import TTSResponse


class TTSModelBase(ABC):
    """Base class for TTS models in AgentScope."""

    supports_streaming_input: bool = False

    def __init__(self, model_name: str, stream: bool) -> None:
        """Initialize the TTS model base class."""
        self.model_name = model_name
        self.stream = stream

    async def __aenter__(self) -> "TTSModelBase":
        """Enter the async context manager."""
        if self.supports_streaming_input:
            await self.connect()
        return self

    async def __aexit__(
        self,
        exc_type: Any,
        exc_value: Any,
        traceback: Any,
    ) -> None:
        """Exit the async context manager."""
        if self.supports_streaming_input:
            await self.close()

    async def connect(self) -> None:
        """Connect to the TTS model if it needs a live session."""
        raise NotImplementedError(
            f"The connect method is not implemented for "
            f"{self.__class__.__name__}.",
        )

    async def close(self) -> None:
        """Close resources held by the TTS model."""
        raise NotImplementedError(
            f"The close method is not implemented for "
            f"{self.__class__.__name__}.",
        )

    async def push(
        self,
        msg: Msg,
        **kwargs: Any,
    ) -> TTSResponse:
        """Append text for realtime TTS models."""
        raise NotImplementedError(
            f"The push method is not implemented for "
            f"{self.__class__.__name__}.",
        )

    @abstractmethod
    async def synthesize(
        self,
        msg: Msg | None = None,
        **kwargs: Any,
    ) -> TTSResponse | AsyncGenerator[TTSResponse, None]:
        """Synthesize speech from text."""
