# -*- coding: utf-8 -*-
"""OpenAI-compatible model adapter for Trinity-RFT training."""
from __future__ import annotations

from typing import TYPE_CHECKING

from ._openai_model import OpenAIChatModel
from ..types import JSONSerializableObject

if TYPE_CHECKING:
    from openai import AsyncOpenAI
else:
    AsyncOpenAI = "openai.AsyncOpenAI"


class TrinityChatModel(OpenAIChatModel):
    """Chat model adapter for Trinity-RFT managed OpenAI-compatible clients."""

    def __init__(
        self,
        openai_async_client: AsyncOpenAI,
        generate_kwargs: dict[str, JSONSerializableObject] | None = None,
        enable_thinking: bool | None = None,
    ) -> None:
        """Initialize a Trinity-RFT-backed chat model.

        Args:
            openai_async_client (`AsyncOpenAI`):
                The async OpenAI-compatible client instance provided by
                Trinity-RFT.
            generate_kwargs (`dict[str, JSONSerializableObject] | None`, \
            optional):
                Extra generation keyword arguments.
            enable_thinking (`bool | None`, optional):
                Optional chat-template toggle used by Qwen3-style models.
        """
        model_name = getattr(openai_async_client, "model_path", None)
        if model_name is None:
            raise ValueError(
                "The provided openai_async_client does not have a "
                "`model_path` attribute. Please ensure you are using the "
                "client instance created by Trinity-RFT.",
            )

        super().__init__(
            model_name=model_name,
            api_key="EMPTY",
            generate_kwargs=generate_kwargs,
            stream=False,
        )

        if enable_thinking is not None:
            chat_template_kwargs = self.generate_kwargs.setdefault(
                "chat_template_kwargs",
                {},
            )
            if not isinstance(chat_template_kwargs, dict):
                raise ValueError(
                    "generate_kwargs['chat_template_kwargs'] must be a "
                    "dictionary when provided.",
                )
            chat_template_kwargs["enable_thinking"] = enable_thinking

        self.client = openai_async_client
