# -*- coding: utf-8 -*-
"""SubAgent tool registration tests."""
from __future__ import annotations

import asyncio
from typing import Any

from agentscope.message import Msg, ToolUseBlock

from ._shared import (
    EchoSubAgentMixin,
    SubAgentInput,
    build_host_agent,
    build_spec,
    invoke_tool,
)


def test_host_registers_and_invokes_subagent_tool() -> None:
    """A host should expose SubAgent V1 through its toolkit."""
    from agentscope.agent._subagent_base import SubAgentBase

    class EchoSubAgent(EchoSubAgentMixin, SubAgentBase):
        """Echo subagent used to verify registration and invocation."""

        InputModel = SubAgentInput

        async def observe(self, msg: Msg | list[Msg] | None) -> None:
            await self.memory.add(msg)

        async def reply(
            self,
            input_obj: SubAgentInput,
            **_: Any,
        ) -> Msg:
            self.__class__.instance_ids.append(id(self))
            self.__class__.memory_sizes.append(await self.memory.size())
            context = getattr(self, "_delegation_context", None)
            if context is not None:
                self.__class__.delegation_payloads.append(context.to_payload())
            return Msg(
                name=self.spec_name,
                content=f"echo:{input_obj.message}",
                role="assistant",
            )

    async def _run() -> None:
        agent = build_host_agent()
        EchoSubAgent.reset()

        tool_name = await agent.register_subagent(
            EchoSubAgent,
            build_spec("echo"),
        )

        await agent.memory.add(
            Msg(
                name="human",
                content="Need an echo.",
                role="user",
            ),
        )

        response = await invoke_tool(
            agent,
            ToolUseBlock(
                type="tool_use",
                id="call-1",
                name=tool_name,
                input={"message": "Repeat the latest request verbatim."},
            ),
        )

        assert response.metadata is not None
        assert response.metadata["subagent"] == "echo"
        assert response.metadata["supervisor"] == agent.name
        payload = response.metadata["delegation_context"]["input_payload"]
        assert payload["message"] == "Repeat the latest request verbatim."
        assert response.content[0]["type"] == "text"
        assert (
            response.content[0]["text"]
            == "echo:Repeat the latest request verbatim."
        )
        assert response.is_last is True
        assert EchoSubAgent.memory_sizes == [1]
        assert len(EchoSubAgent.instance_ids) == 1
        assert await agent.memory.size() == 1
        assert tool_name in agent.toolkit.tools

    asyncio.run(_run())


def test_subagent_validation_error_becomes_tool_response() -> None:
    """Validation errors should be surfaced as tool metadata, not crashes."""
    from agentscope.agent._subagent_base import SubAgentBase
    from pydantic import BaseModel

    class EchoSubAgent(SubAgentBase):
        """Subagent used to verify validation failures stay recoverable."""

        class Input(BaseModel):
            """Strict input model for validation error coverage."""

            message: str

        InputModel = Input

        async def observe(self, msg: Msg | list[Msg] | None) -> None:
            await self.memory.add(msg)

        async def reply(
            self,
            input_obj: Input,
            **_: Any,
        ) -> Msg:
            return Msg(
                name=self.spec_name,
                content=input_obj.message,
                role="assistant",
            )

    async def _run() -> None:
        agent = build_host_agent()
        tool_name = await agent.register_subagent(
            EchoSubAgent,
            build_spec("echo"),
        )

        response = await invoke_tool(
            agent,
            ToolUseBlock(
                type="tool_use",
                id="call-2",
                name=tool_name,
                input={},
            ),
        )

        assert response.metadata is not None
        assert response.metadata["unavailable"] is True
        assert response.metadata["subagent"] == "echo"
        assert response.metadata["supervisor"] == agent.name
        assert response.is_last is True

    asyncio.run(_run())
