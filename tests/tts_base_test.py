# -*- coding: utf-8 -*-
"""Unit tests for the TTS model base helpers."""
from __future__ import annotations

from unittest import IsolatedAsyncioTestCase

from agentscope.message import Msg
from agentscope.tts import TTSModelBase, TTSResponse


class _StreamingBaseProbe(TTSModelBase):
    """Concrete probe used to exercise TTSModelBase defaults."""

    supports_streaming_input = True

    def __init__(self) -> None:
        super().__init__("probe", stream=False)
        self.events: list[str] = []

    async def connect(self) -> None:
        self.events.append("connect")

    async def close(self) -> None:
        self.events.append("close")

    async def synthesize(self, msg=None, **kwargs):
        del msg, kwargs
        return TTSResponse(content=None)


class _NonRealtimeBaseProbe(TTSModelBase):
    """Probe that uses base NotImplemented branches."""

    def __init__(self) -> None:
        super().__init__("non_realtime", stream=False)

    async def synthesize(self, msg=None, **kwargs):
        del msg, kwargs
        return TTSResponse(content=None)


class TTSModelBaseTest(IsolatedAsyncioTestCase):
    """Tests for common TTS model base behavior."""

    async def test_async_context_connects_and_closes_streaming_models(
        self,
    ) -> None:
        """Streaming-capable models should connect and close via context."""
        probe = _StreamingBaseProbe()

        async with probe:
            self.assertEqual(probe.events, ["connect"])

        self.assertEqual(probe.events, ["connect", "close"])

    async def test_default_non_realtime_methods_raise(self) -> None:
        """Base connect/close/push should raise on non-realtime probes."""
        probe = _NonRealtimeBaseProbe()
        msg = Msg("assistant", "hello", "assistant")

        with self.assertRaises(NotImplementedError):
            await probe.connect()

        with self.assertRaises(NotImplementedError):
            await probe.close()

        with self.assertRaises(NotImplementedError):
            await probe.push(msg)

    async def test_tts_response_prefers_instance_values_for_default_fields(
        self,
    ) -> None:
        """DictMixin-backed responses should expose overridden field values."""
        response = TTSResponse(
            content=None,
            metadata={"source": "test"},
            is_last=False,
        )

        self.assertEqual(response.metadata, {"source": "test"})
        self.assertFalse(response.is_last)
