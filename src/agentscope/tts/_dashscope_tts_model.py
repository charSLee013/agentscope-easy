# -*- coding: utf-8 -*-
"""DashScope SDK TTS model implementation using MultiModalConversation API."""
from typing import TYPE_CHECKING, Any, AsyncGenerator, Generator, Literal

from ..message import AudioBlock, Base64Source, Msg
from ..types import JSONSerializableObject
from ._tts_base import TTSModelBase
from ._tts_response import TTSResponse

if TYPE_CHECKING:
    from dashscope.api_entities.dashscope_response import (
        MultiModalConversationResponse,
    )
else:
    MultiModalConversationResponse = (
        "dashscope.api_entities.dashscope_response."
        "MultiModalConversationResponse"
    )


class DashScopeTTSModel(TTSModelBase):
    """DashScope TTS model implementation."""

    supports_streaming_input: bool = False

    def __init__(
        self,
        api_key: str,
        model_name: str = "qwen3-tts-flash",
        voice: Literal["Cherry", "Serena", "Ethan", "Chelsie"]
        | str = "Cherry",
        language_type: str = "Auto",
        stream: bool = True,
        generate_kwargs: dict[str, JSONSerializableObject] | None = None,
    ) -> None:
        """Initialize the DashScope TTS model."""
        super().__init__(model_name=model_name, stream=stream)
        self.api_key = api_key
        self.voice = voice
        self.language_type = language_type
        self.generate_kwargs = generate_kwargs or {}

    async def synthesize(
        self,
        msg: Msg | None = None,
        **kwargs: Any,
    ) -> TTSResponse | AsyncGenerator[TTSResponse, None]:
        """Call the DashScope TTS API."""
        if msg is None:
            return TTSResponse(content=None)

        text = msg.get_text_content()
        if not text:
            return TTSResponse(content=None)

        import dashscope

        response = dashscope.MultiModalConversation.call(
            model=self.model_name,
            api_key=self.api_key,
            text=text,
            voice=self.voice,
            language_type=self.language_type,
            stream=True,
            **self.generate_kwargs,
            **kwargs,
        )

        if self.stream:
            return self._parse_into_async_generator(response)

        audio_data = ""
        for chunk in response:
            if chunk.output is None:
                continue
            audio = chunk.output.audio
            if not audio or not audio.data:
                continue
            audio_data += audio.data
        return TTSResponse(
            content=AudioBlock(
                type="audio",
                source=Base64Source(
                    type="base64",
                    data=audio_data,
                    media_type="audio/pcm;rate=24000",
                ),
            ),
        )

    @staticmethod
    async def _parse_into_async_generator(
        response: Generator["MultiModalConversationResponse", None, None],
    ) -> AsyncGenerator[TTSResponse, None]:
        """Parse the DashScope streaming response."""
        audio_data = ""
        for chunk in response:
            if chunk.output is None:
                continue
            audio = chunk.output.audio
            if not audio or not audio.data:
                continue
            audio_data += audio.data
            yield TTSResponse(
                content=AudioBlock(
                    type="audio",
                    source=Base64Source(
                        type="base64",
                        data=audio_data,
                        media_type="audio/pcm;rate=24000",
                    ),
                ),
                is_last=False,
            )

        yield TTSResponse(
            content=AudioBlock(
                type="audio",
                source=Base64Source(
                    type="base64",
                    data=audio_data,
                    media_type="audio/pcm;rate=24000",
                ),
            ),
            is_last=True,
        )
