# -*- coding: utf-8 -*-
"""DashScope realtime TTS model implementation."""
import threading
from typing import TYPE_CHECKING, Any, AsyncGenerator, Literal

from ..message import AudioBlock, Base64Source, Msg
from ..types import JSONSerializableObject
from ._tts_base import TTSModelBase
from ._tts_response import TTSResponse

if TYPE_CHECKING:
    from dashscope.audio.qwen_tts_realtime import (
        QwenTtsRealtime,
        QwenTtsRealtimeCallback,
    )
else:
    QwenTtsRealtime = "dashscope.audio.qwen_tts_realtime.QwenTtsRealtime"
    QwenTtsRealtimeCallback = (
        "dashscope.audio.qwen_tts_realtime.QwenTtsRealtimeCallback"
    )


def _get_qwen_tts_realtime_callback_class() -> type["QwenTtsRealtimeCallback"]:
    from dashscope.audio.qwen_tts_realtime import QwenTtsRealtimeCallback

    class _DashScopeRealtimeTTSCallback(QwenTtsRealtimeCallback):
        """DashScope realtime TTS callback."""

        def __init__(self) -> None:
            super().__init__()
            self.chunk_event = threading.Event()
            self.finish_event = threading.Event()
            self._audio_data = ""

        def on_event(self, response: dict[str, Any]) -> None:
            """Handle SDK callback events."""
            try:
                event_type = response.get("type")
                if event_type == "session.created":
                    self._audio_data = ""
                    self.finish_event.clear()
                elif event_type == "response.audio.delta":
                    audio_data = response.get("delta")
                    if audio_data:
                        if isinstance(audio_data, bytes):
                            import base64

                            audio_data = base64.b64encode(audio_data).decode()
                        self._audio_data += audio_data
                        if not self.chunk_event.is_set():
                            self.chunk_event.set()
                elif event_type == "session.finished":
                    self.chunk_event.set()
                    self.finish_event.set()
            except Exception:
                import traceback

                traceback.print_exc()
                self.finish_event.set()

        async def get_audio_data(self, block: bool) -> TTSResponse:
            """Return the accumulated audio data."""
            if block:
                self.finish_event.wait()

            if self._audio_data:
                return TTSResponse(
                    content=AudioBlock(
                        type="audio",
                        source=Base64Source(
                            type="base64",
                            data=self._audio_data,
                            media_type="audio/pcm;rate=24000",
                        ),
                    ),
                )

            await self._reset()
            return TTSResponse(content=None)

        async def get_audio_chunk(self) -> AsyncGenerator[TTSResponse, None]:
            """Yield audio chunks as they arrive."""
            while True:
                if self.finish_event.is_set():
                    yield TTSResponse(
                        content=AudioBlock(
                            type="audio",
                            source=Base64Source(
                                type="base64",
                                data=self._audio_data,
                                media_type="audio/pcm;rate=24000",
                            ),
                        ),
                        is_last=True,
                    )
                    await self._reset()
                    break

                if self.chunk_event.is_set():
                    self.chunk_event.clear()
                else:
                    self.chunk_event.wait()

                yield TTSResponse(
                    content=AudioBlock(
                        type="audio",
                        source=Base64Source(
                            type="base64",
                            data=self._audio_data,
                            media_type="audio/pcm;rate=24000",
                        ),
                    ),
                    is_last=False,
                )

        async def _reset(self) -> None:
            self.finish_event.clear()
            self.chunk_event.clear()
            self._audio_data = ""

    return _DashScopeRealtimeTTSCallback


class DashScopeRealtimeTTSModel(TTSModelBase):
    """DashScope realtime TTS model."""

    supports_streaming_input: bool = True

    def __init__(
        self,
        api_key: str,
        model_name: str = "qwen3-tts-flash-realtime",
        voice: Literal["Cherry", "Nofish", "Ethan", "Jennifer"] | str = "Cherry",
        stream: bool = True,
        cold_start_length: int | None = None,
        cold_start_words: int | None = None,
        client_kwargs: dict[str, JSONSerializableObject] | None = None,
        generate_kwargs: dict[str, JSONSerializableObject] | None = None,
    ) -> None:
        """Initialize the DashScope realtime TTS model."""
        super().__init__(model_name=model_name, stream=stream)

        import dashscope
        from dashscope.audio.qwen_tts_realtime import QwenTtsRealtime

        dashscope.api_key = api_key

        self.voice = voice
        self.mode = "server_commit"
        self.cold_start_length = cold_start_length
        self.cold_start_words = cold_start_words
        self.client_kwargs = client_kwargs or {}
        self.generate_kwargs = generate_kwargs or {}
        self._dashscope_callback = _get_qwen_tts_realtime_callback_class()()
        self._tts_client: "QwenTtsRealtime" = QwenTtsRealtime(
            model=self.model_name,
            callback=self._dashscope_callback,
            **self.client_kwargs,
        )
        self._connected = False
        self._first_send = True
        self._current_msg_id: str | None = None
        self._current_prefix = ""

    async def connect(self) -> None:
        """Establish the realtime session."""
        if self._connected:
            return
        self._tts_client.connect()
        self._tts_client.update_session(
            voice=self.voice,
            mode=self.mode,
            **self.generate_kwargs,
        )
        self._connected = True

    async def close(self) -> None:
        """Close the realtime session."""
        if not self._connected:
            return
        self._connected = False
        self._tts_client.finish()
        self._tts_client.close()

    async def push(
        self,
        msg: Msg,
        **kwargs: Any,
    ) -> TTSResponse:
        """Append text to the realtime session."""
        del kwargs
        if not self._connected:
            raise RuntimeError(
                "TTS model is not connected. Call `connect()` first.",
            )
        if self._current_msg_id is not None and self._current_msg_id != msg.id:
            raise RuntimeError(
                "DashScopeRealtimeTTSModel can only handle one streaming "
                "input request at a time.",
            )

        self._current_msg_id = msg.id
        text = msg.get_text_content() or ""
        if not text:
            return TTSResponse(content=None)

        if self._first_send:
            if self.cold_start_length and len(text) < self.cold_start_length:
                delta_to_send = ""
            else:
                delta_to_send = text
            if delta_to_send and self.cold_start_words:
                if len(delta_to_send.split()) < self.cold_start_words:
                    delta_to_send = ""
        else:
            delta_to_send = text.removeprefix(self._current_prefix)

        if delta_to_send:
            self._tts_client.append_text(delta_to_send)
            self._current_prefix += delta_to_send
            self._first_send = False

        return await self._dashscope_callback.get_audio_data(block=False)

    async def synthesize(
        self,
        msg: Msg | None = None,
        **kwargs: Any,
    ) -> TTSResponse | AsyncGenerator[TTSResponse, None]:
        """Finish synthesis for the current realtime session."""
        del kwargs
        if not self._connected:
            raise RuntimeError(
                "TTS model is not connected. Call `connect()` first.",
            )

        if msg is None:
            delta_to_send = ""
        else:
            if self._current_msg_id is not None and self._current_msg_id != msg.id:
                raise RuntimeError(
                    "DashScopeRealtimeTTSModel can only handle one streaming "
                    "input request at a time.",
                )
            self._current_msg_id = msg.id
            delta_to_send = (msg.get_text_content() or "").removeprefix(
                self._current_prefix,
            )

        if delta_to_send:
            self._tts_client.append_text(delta_to_send)
            self._current_prefix += delta_to_send
            self._first_send = False

        self._tts_client.commit()
        self._tts_client.finish()

        if self.stream:
            result = self._dashscope_callback.get_audio_chunk()
        else:
            result = await self._dashscope_callback.get_audio_data(block=True)

        self._current_msg_id = None
        self._first_send = True
        self._current_prefix = ""
        return result

