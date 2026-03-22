# -*- coding: utf-8 -*-
"""SubAgent lifecycle tests."""
from __future__ import annotations

import asyncio
from typing import Any

import pytest

from pydantic import BaseModel

from agentscope.message import Msg, ToolUseBlock

from ._shared import build_host_agent, build_spec, invoke_tool


def test_subagent_registration_probe_fails_fast() -> None:
    """Registration should abort when export-time construction fails."""
    from agentscope.agent._subagent_base import (
        SubAgentBase,
        SubAgentUnavailable,
    )

    async def _run() -> None:
        agent = build_host_agent()

        class CtorFailSubAgent(SubAgentBase):
            """Subagent that fails during construction."""

            class Input(BaseModel):
                """Minimal input model for constructor-failure tests."""

                message: str = "noop"

            InputModel = Input

            def __init__(self, **kwargs: Any) -> None:
                super().__init__(**kwargs)
                raise RuntimeError("missing dependency")

            async def observe(self, msg: Msg | list[Msg] | None) -> None:
                await self.memory.add(msg)

            async def reply(self, input_obj: Input, **_: Any) -> Msg:
                return Msg("ctor", input_obj.message, "assistant")

        with pytest.raises(SubAgentUnavailable):
            await agent.register_subagent(
                CtorFailSubAgent,
                build_spec("ctorfail"),
            )

    asyncio.run(_run())


def test_subagent_uses_fresh_instance_per_call() -> None:
    """Delegation should construct a new subagent instance each time."""
    from agentscope.agent._subagent_base import SubAgentBase

    class FreshSubAgent(SubAgentBase):
        """Subagent that records a serial number per fresh instance."""

        class Input(BaseModel):
            """Minimal input model for lifecycle checks."""

            message: str = "noop"

        InputModel = Input
        serial_counter: int = 0
        instance_serials: list[int] = []

        @classmethod
        def reset(cls) -> None:
            """Reset instance counters between test runs."""
            cls.serial_counter = 0
            cls.instance_serials = []

        def __init__(self, **kwargs: Any) -> None:
            super().__init__(**kwargs)
            type(self).serial_counter += 1
            self.serial = type(self).serial_counter

        async def observe(self, msg: Msg | list[Msg] | None) -> None:
            await self.memory.add(msg)

        async def reply(self, input_obj: Input, **_: Any) -> Msg:
            self.__class__.instance_serials.append(self.serial)
            return Msg(
                name=self.spec_name,
                content=input_obj.message,
                role="assistant",
            )

    async def _run() -> None:
        agent = build_host_agent()
        tool_name = await agent.register_subagent(
            FreshSubAgent,
            build_spec("fresh"),
        )
        FreshSubAgent.reset()

        for idx in range(2):
            await invoke_tool(
                agent,
                ToolUseBlock(
                    type="tool_use",
                    id=f"fresh-{idx}",
                    name=tool_name,
                    input={"message": f"call-{idx}"},
                ),
            )

        assert FreshSubAgent.instance_serials == [1, 2]

    asyncio.run(_run())


def test_subagent_registration_rejects_parallel_host() -> None:
    """SubAgent V1 should not register on a parallel-tool host."""
    from agentscope.agent._subagent_base import (
        SubAgentBase,
        SubAgentUnavailable,
    )

    class ParallelBlockedSubAgent(SubAgentBase):
        """Subagent used to verify the parallel-host guard."""

        class Input(BaseModel):
            """Minimal input model for parallel-host rejection."""

            message: str = "noop"

        InputModel = Input

        async def observe(self, msg: Msg | list[Msg] | None) -> None:
            await self.memory.add(msg)

        async def reply(self, input_obj: Input, **_: Any) -> Msg:
            return Msg(
                name=self.spec_name,
                content=input_obj.message,
                role="assistant",
            )

    async def _run() -> None:
        agent = build_host_agent(parallel=True)

        with pytest.raises(SubAgentUnavailable):
            await agent.register_subagent(
                ParallelBlockedSubAgent,
                build_spec("parallel-blocked"),
            )

    asyncio.run(_run())
