# -*- coding: utf-8 -*-
"""SubAgent model inheritance tests."""
from __future__ import annotations

import asyncio
from typing import Any

from agentscope.message import Msg, ToolUseBlock
from agentscope.model import ChatModelBase, ChatResponse

from ._shared import SubAgentInput, build_host_agent, build_spec, invoke_tool


class TaggedModel(ChatModelBase):
    """Simple model object used to verify identity inheritance."""

    def __init__(self, name: str) -> None:
        super().__init__(name, stream=False)

    async def __call__(
        self,
        _messages: list[dict],
        **kwargs: Any,
    ) -> ChatResponse:
        return ChatResponse(content=[])


def test_subagent_inherits_host_model_by_default() -> None:
    """Subagents should receive the host model when no override is given."""
    from agentscope.agent._subagent_base import SubAgentBase

    class ModelCaptureSubAgent(SubAgentBase):
        """Subagent that records which model object it received."""

        InputModel = SubAgentInput
        seen_models: list[ChatModelBase | None] = []

        @classmethod
        def reset(cls) -> None:
            """Clear captured model references between assertions."""
            cls.seen_models = []

        async def observe(self, msg: Msg | list[Msg] | None) -> None:
            await self.memory.add(msg)

        async def reply(
            self,
            input_obj: SubAgentInput,
            **_: Any,
        ) -> Msg:
            self.__class__.seen_models.append(self.model_override)
            return Msg(
                name=self.spec_name,
                content=input_obj.message,
                role="assistant",
            )

    async def _run() -> None:
        agent = build_host_agent()
        ModelCaptureSubAgent.reset()

        tool_name = await agent.register_subagent(
            ModelCaptureSubAgent,
            build_spec("model-default"),
        )

        await invoke_tool(
            agent,
            ToolUseBlock(
                type="tool_use",
                id="model-default-1",
                name=tool_name,
                input={"message": "use inherited model"},
            ),
        )

        assert ModelCaptureSubAgent.seen_models == [agent.model]

    asyncio.run(_run())


def test_subagent_explicit_override_model() -> None:
    """Explicit override should win without mutating the host model."""
    from agentscope.agent._subagent_base import SubAgentBase

    class ModelCaptureSubAgent(SubAgentBase):
        """Subagent that records explicit override model inheritance."""

        InputModel = SubAgentInput
        seen_models: list[ChatModelBase | None] = []

        @classmethod
        def reset(cls) -> None:
            """Clear captured model references between assertions."""
            cls.seen_models = []

        async def observe(self, msg: Msg | list[Msg] | None) -> None:
            await self.memory.add(msg)

        async def reply(
            self,
            input_obj: SubAgentInput,
            **_: Any,
        ) -> Msg:
            self.__class__.seen_models.append(self.model_override)
            return Msg(
                name=self.spec_name,
                content=input_obj.message,
                role="assistant",
            )

    async def _run() -> None:
        agent = build_host_agent()
        override_model = TaggedModel("override")
        ModelCaptureSubAgent.reset()

        tool_name = await agent.register_subagent(
            ModelCaptureSubAgent,
            build_spec("model-override"),
            override_model=override_model,
        )

        await invoke_tool(
            agent,
            ToolUseBlock(
                type="tool_use",
                id="model-override-1",
                name=tool_name,
                input={"message": "use override model"},
            ),
        )

        assert ModelCaptureSubAgent.seen_models == [override_model]
        assert ModelCaptureSubAgent.seen_models[0] is not agent.model

    asyncio.run(_run())
