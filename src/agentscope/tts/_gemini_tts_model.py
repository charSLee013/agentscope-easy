# -*- coding: utf-8 -*-
"""Gemini TTS model implementation."""
import base64
from typing import TYPE_CHECKING, Any, AsyncGenerator, Iterator, Literal

from ..message import AudioBlock, Base64Source, Msg
from ..types import JSONSerializableObject
from ._tts_base import TTSModelBase
from ._tts_response import TTSResponse

if TYPE_CHECKING:
    from google.genai.types import GenerateContentResponse
else:
    GenerateContentResponse = "google.genai.types.GenerateContentResponse"


class GeminiTTSModel(TTSModelBase):
    """Gemini TTS model implementation."""

    supports_streaming_input: bool = False

    def __init__(
        self,
        api_key: str,
        model_name: str = "gemini-2.5-flash-preview-tts",
        voice: Literal["Zephyr", "Kore", "Orus", "Autonoe"] | str = "Kore",
        stream: bool = True,
        client_kwargs: dict[str, JSONSerializableObject] | None = None,
        generate_kwargs: dict[str, JSONSerializableObject] | None = None,
    ) -> None:
        """Initialize the Gemini TTS model."""
        super().__init__(model_name=model_name, stream=stream)
        self.api_key = api_key
        self.voice = voice
        self.generate_kwargs = generate_kwargs or {}

        from google import genai

        self._client = genai.Client(
            api_key=self.api_key,
            **(client_kwargs or {}),
        )

    async def synthesize(
        self,
        msg: Msg | None = None,
        **kwargs: Any,
    ) -> TTSResponse | AsyncGenerator[TTSResponse, None]:
        """Synthesize speech with Gemini."""
        if msg is None:
            return TTSResponse(content=None)

        from google.genai import types

        text = msg.get_text_content()
        if not text:
            return TTSResponse(content=None)

        config = types.GenerateContentConfig(
            response_modalities=["AUDIO"],
            speech_config=types.SpeechConfig(
                voice_config=types.VoiceConfig(
                    prebuilt_voice_config=types.PrebuiltVoiceConfig(
                        voice_name=self.voice,
                    ),
                ),
            ),
            **self.generate_kwargs,
            **kwargs,
        )
        api_kwargs: dict[str, JSONSerializableObject] = {
            "model": self.model_name,
            "contents": text,
            "config": config,
        }

        if self.stream:
            response = self._client.models.generate_content_stream(
                **api_kwargs,
            )
            return self._parse_into_async_generator(response)

        response = self._client.models.generate_content(**api_kwargs)
        if (
            response.candidates
            and response.candidates[0].content
            and response.candidates[0].content.parts
            and response.candidates[0].content.parts[0].inline_data
        ):
            audio_data = (
                response.candidates[0].content.parts[0].inline_data.data
            )
            mime_type = (
                response.candidates[0].content.parts[0].inline_data.mime_type
            )
            return TTSResponse(
                content=AudioBlock(
                    type="audio",
                    source=Base64Source(
                        type="base64",
                        data=base64.b64encode(audio_data).decode("utf-8"),
                        media_type=mime_type,
                    ),
                ),
            )

        return TTSResponse(
            content=AudioBlock(
                type="audio",
                source=Base64Source(
                    type="base64",
                    data="",
                    media_type="audio/pcm;rate=24000",
                ),
            ),
        )

    @staticmethod
    async def _parse_into_async_generator(
        response: Iterator["GenerateContentResponse"],
    ) -> AsyncGenerator[TTSResponse, None]:
        """Parse Gemini streaming response."""
        audio_bytes = bytearray()
        mime_type = "audio/pcm;rate=24000"
        for chunk in response:
            chunk_audio_data = (
                chunk.candidates[0].content.parts[0].inline_data.data
            )
            mime_type = (
                chunk.candidates[0].content.parts[0].inline_data.mime_type
            )
            audio_bytes.extend(chunk_audio_data)
            yield TTSResponse(
                content=AudioBlock(
                    type="audio",
                    source=Base64Source(
                        type="base64",
                        data=base64.b64encode(audio_bytes).decode("utf-8"),
                        media_type=mime_type,
                    ),
                ),
                is_last=False,
            )
        if audio_bytes:
            yield TTSResponse(
                content=AudioBlock(
                    type="audio",
                    source=Base64Source(
                        type="base64",
                        data=base64.b64encode(audio_bytes).decode("utf-8"),
                        media_type=mime_type,
                    ),
                ),
                is_last=True,
            )
