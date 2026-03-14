# -*- coding: utf-8 -*-
"""OpenAI TTS model implementation."""
import base64
from typing import TYPE_CHECKING, Any, AsyncGenerator, Literal

from ..message import AudioBlock, Base64Source, Msg
from ..types import JSONSerializableObject
from ._tts_base import TTSModelBase
from ._tts_response import TTSResponse

if TYPE_CHECKING:
    from openai import HttpxBinaryResponseContent
else:
    HttpxBinaryResponseContent = "openai.HttpxBinaryResponseContent"


class OpenAITTSModel(TTSModelBase):
    """OpenAI TTS model implementation."""

    supports_streaming_input: bool = False

    def __init__(
        self,
        api_key: str,
        model_name: str = "gpt-4o-mini-tts",
        voice: Literal["alloy", "ash", "ballad", "coral"] | str = "alloy",
        stream: bool = True,
        client_kwargs: dict[str, JSONSerializableObject] | None = None,
        generate_kwargs: dict[str, JSONSerializableObject] | None = None,
    ) -> None:
        """Initialize the OpenAI TTS model."""
        super().__init__(model_name=model_name, stream=stream)
        self.api_key = api_key
        self.voice = voice
        self.generate_kwargs = generate_kwargs or {}

        import openai

        self._client = openai.AsyncOpenAI(
            api_key=self.api_key,
            **(client_kwargs or {}),
        )

    async def synthesize(
        self,
        msg: Msg | None = None,
        **kwargs: Any,
    ) -> TTSResponse | AsyncGenerator[TTSResponse, None]:
        """Synthesize speech with the OpenAI audio API."""
        if msg is None:
            return TTSResponse(content=None)

        text = msg.get_text_content()
        if not text:
            return TTSResponse(content=None)

        if self.stream:
            response = (
                self._client.audio.speech.with_streaming_response.create(
                    model=self.model_name,
                    voice=self.voice,
                    input=text,
                    response_format="pcm",
                    **self.generate_kwargs,
                    **kwargs,
                )
            )
            return self._parse_into_async_generator(response)

        response = await self._client.audio.speech.create(
            model=self.model_name,
            voice=self.voice,
            input=text,
            response_format="pcm",
            **self.generate_kwargs,
            **kwargs,
        )
        audio_base64 = base64.b64encode(response.content).decode("utf-8")
        return TTSResponse(
            content=AudioBlock(
                type="audio",
                source=Base64Source(
                    type="base64",
                    data=audio_base64,
                    media_type="audio/pcm",
                ),
            ),
        )

    @staticmethod
    async def _parse_into_async_generator(
        response: "HttpxBinaryResponseContent",
    ) -> AsyncGenerator[TTSResponse, None]:
        """Parse the OpenAI streaming response."""
        audio_base64 = ""
        async with response as stream:
            async for chunk in stream.iter_bytes():
                if not chunk:
                    continue
                audio_base64 = base64.b64encode(chunk).decode("utf-8")
                yield TTSResponse(
                    content=AudioBlock(
                        type="audio",
                        source=Base64Source(
                            type="base64",
                            data=audio_base64,
                            media_type="audio/pcm",
                        ),
                    ),
                    is_last=False,
                )

        yield TTSResponse(
            content=AudioBlock(
                type="audio",
                source=Base64Source(
                    type="base64",
                    data=audio_base64,
                    media_type="audio/pcm",
                ),
            ),
            is_last=True,
        )

