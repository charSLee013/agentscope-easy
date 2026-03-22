# -*- coding: utf-8 -*-
"""SubAgent memory snapshot tests."""
from __future__ import annotations

import asyncio
from typing import Any

from agentscope.message import Msg, ToolUseBlock

from ._shared import SubAgentInput, build_host_agent, build_spec, invoke_tool


def test_subagent_uses_memory_snapshot_without_mutating_host_memory() -> None:
    """Delegation context should not mutate host-stored messages."""
    from agentscope.agent._subagent_base import SubAgentBase

    class RecordingSubAgent(SubAgentBase):
        """Subagent that returns the received delegation metadata."""

        InputModel = SubAgentInput

        async def observe(self, msg: Msg | list[Msg] | None) -> None:
            await self.memory.add(msg)

        async def reply(
            self,
            input_obj: SubAgentInput,
            **_: Any,
        ) -> Msg:
            context = getattr(self, "_delegation_context", None)
            return Msg(
                name=self.spec_name,
                content=input_obj.message,
                role="assistant",
                metadata={
                    "delegation_context": (
                        context.to_payload() if context is not None else {}
                    ),
                },
            )

    async def _run() -> None:
        agent = build_host_agent()
        tool_name = await agent.register_subagent(
            RecordingSubAgent,
            build_spec("recorder"),
        )

        user_msg = Msg(
            name="human",
            content="Summarize the latest updates.",
            role="user",
        )
        await agent.memory.add(user_msg)

        response = await invoke_tool(
            agent,
            ToolUseBlock(
                type="tool_use",
                id="snapshot-1",
                name=tool_name,
                input={"message": "Summarize the latest updates."},
            ),
        )

        refreshed_history = await agent.memory.get_memory()
        assert "delegation_context" not in (
            refreshed_history[-1].metadata or {}
        )
        assert response.metadata is not None
        recent_events = response.metadata["delegation_context"][
            "recent_events"
        ]
        assert recent_events[0]["preview"] == "Summarize the latest updates."

    asyncio.run(_run())
