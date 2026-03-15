# -*- coding: utf-8 -*-
"""Base helpers for ReMe-backed long-term memories."""
from abc import ABCMeta
from typing import Any

from .._long_term_memory_base import LongTermMemoryBase
from ...embedding import DashScopeTextEmbedding, OpenAITextEmbedding
from ...model import DashScopeChatModel, OpenAIChatModel


class ReMeLongTermMemoryBase(LongTermMemoryBase, metaclass=ABCMeta):
    """Base class for ReMe-backed long-term memory implementations."""

    def __init__(
        self,
        agent_name: str | None = None,
        user_name: str | None = None,
        run_name: str | None = None,
        model: DashScopeChatModel | OpenAIChatModel | None = None,
        embedding_model: (
            DashScopeTextEmbedding | OpenAITextEmbedding | None
        ) = None,
        reme_config_path: str | None = None,
        **kwargs: Any,
    ) -> None:
        """Initialize a ReMe-backed long-term memory."""
        super().__init__()

        self.agent_name = agent_name
        self.workspace_id = user_name
        self.run_name = run_name

        config_args = []

        if isinstance(model, DashScopeChatModel):
            llm_api_base = "https://dashscope.aliyuncs.com/compatible-mode/v1"
            llm_api_key = model.api_key
        elif isinstance(model, OpenAIChatModel):
            base_url = getattr(model.client, "base_url", None)
            llm_api_base = str(base_url) if base_url else None
            llm_api_key = str(getattr(model.client, "api_key", None))
        else:
            raise ValueError(
                "model must be a DashScopeChatModel or OpenAIChatModel "
                f"instance. Got {type(model).__name__} instead.",
            )

        if model.model_name:
            config_args.append(f"llm.default.model_name={model.model_name}")

        if isinstance(embedding_model, DashScopeTextEmbedding):
            embedding_api_base = (
                "https://dashscope.aliyuncs.com/compatible-mode/v1"
            )
            embedding_api_key = embedding_model.api_key
        elif isinstance(embedding_model, OpenAITextEmbedding):
            base_url = getattr(embedding_model.client, "base_url", None)
            embedding_api_base = str(base_url) if base_url else None
            embedding_api_key = str(
                getattr(embedding_model.client, "api_key", None),
            )
        else:
            raise ValueError(
                "embedding_model must be a DashScopeTextEmbedding or "
                "OpenAITextEmbedding instance. "
                f"Got {type(embedding_model).__name__} instead.",
            )

        if embedding_model.model_name:
            config_args.append(
                "embedding_model.default.model_name="
                f"{embedding_model.model_name}",
            )

        config_args.append(
            "embedding_model.default.params="
            f'{{"dimensions": {embedding_model.dimensions}}}',
        )

        try:
            from reme_ai import ReMeApp
        except ImportError as exc:
            raise ImportError(
                "The 'reme_ai' library is required for ReMe-based long-term "
                "memory. Please install it with `pip install reme-ai`.",
            ) from exc

        self.app = ReMeApp(
            *config_args,
            llm_api_key=llm_api_key,
            llm_api_base=llm_api_base,
            embedding_api_key=embedding_api_key,
            embedding_api_base=embedding_api_base,
            config_path=reme_config_path,
            **kwargs,
        )
        self._app_started = False

    async def __aenter__(self) -> "ReMeLongTermMemoryBase":
        """Enter the async ReMe app context."""
        await self.app.__aenter__()
        self._app_started = True
        return self

    async def __aexit__(
        self,
        exc_type: Any = None,
        exc_val: Any = None,
        exc_tb: Any = None,
    ) -> None:
        """Exit the async ReMe app context."""
        await self.app.__aexit__(exc_type, exc_val, exc_tb)
        self._app_started = False
