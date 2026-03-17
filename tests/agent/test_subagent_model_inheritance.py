# -*- coding: utf-8 -*-
"""Subagent model inheritance tests."""
from __future__ import annotations

import asyncio
from typing import Any

from agentscope.agent._subagent_base import SubAgentBase
from agentscope.message import Msg, TextBlock, ToolUseBlock
from agentscope.model import ChatModelBase, ChatResponse
from ._shared import (
    SubAgentInput,
    build_host_agent,
    build_spec,
    invoke_tool,
)


class TaggedModel(ChatModelBase):
    """Simple model object used to verify identity inheritance."""

    def __init__(self, name: str) -> None:
        super().__init__(name, stream=False)

    async def __call__(
        self,
        _messages: list[dict],
        **kwargs: Any,
    ) -> ChatResponse:
        return ChatResponse(
            content=[TextBlock(type="text", text=self.model_name)],
        )


class ModelCaptureSubAgent(SubAgentBase):
    """Capture the effective model passed into the subagent."""

    seen_models: list[ChatModelBase | None] = []
    InputModel = SubAgentInput

    async def observe(self, msg: Msg | list[Msg] | None) -> None:
        await self.memory.add(msg)

    async def reply(
        self,
        input_obj: SubAgentInput,
        **_,
    ) -> Msg:
        self.__class__.seen_models.append(self.model_override)
        return Msg(
            name=self.spec_name,
            content="model-ok",
            role="assistant",
        )

    @classmethod
    def reset(cls) -> None:
        cls.seen_models = []


def test_subagent_inherits_host_model_by_default() -> None:
    """Subagents should receive the host model when no override is given."""

    async def _run() -> None:
        agent = build_host_agent()
        ModelCaptureSubAgent.reset()

        tool_name = await agent.register_subagent(
            ModelCaptureSubAgent,
            build_spec("model-default"),
        )

        tool_call = ToolUseBlock(
            type="tool_use",
            id="model-default-1",
            name=tool_name,
            input={"message": "Use inherited model."},
        )

        await invoke_tool(agent, tool_call)

        assert ModelCaptureSubAgent.seen_models == [agent.model]

    asyncio.run(_run())


def test_subagent_explicit_override_model() -> None:
    """Explicit override should win without mutating the host model."""

    async def _run() -> None:
        agent = build_host_agent()
        override_model = TaggedModel("override")
        ModelCaptureSubAgent.reset()

        tool_name = await agent.register_subagent(
            ModelCaptureSubAgent,
            build_spec("model-override"),
            override_model=override_model,
        )

        tool_call = ToolUseBlock(
            type="tool_use",
            id="model-override-1",
            name=tool_name,
            input={"message": "Use override model."},
        )

        await invoke_tool(agent, tool_call)

        assert ModelCaptureSubAgent.seen_models == [override_model]
        assert ModelCaptureSubAgent.seen_models[0] is not agent.model

    asyncio.run(_run())
