# -*- coding: utf-8 -*-
"""SubAgent filesystem inheritance tests."""
from __future__ import annotations

import asyncio
from typing import Any

from agentscope.message import Msg, ToolUseBlock

from ._shared import (
    SubAgentInput,
    assert_access_denied,
    attach_filesystem,
    build_host_agent,
    build_spec,
    invoke_tool,
)


def test_subagent_inherits_host_filesystem_without_expansion() -> None:
    """Subagent should receive the host filesystem service as-is."""
    from agentscope.agent._subagent_base import SubAgentBase

    class FilesystemSubAgent(SubAgentBase):
        """Subagent that writes inside the inherited filesystem grant."""

        InputModel = SubAgentInput
        captured_ids: list[int] = []
        errors: list[str] = []

        @classmethod
        def reset(cls) -> None:
            """Reset captured filesystem state between test runs."""
            cls.captured_ids = []
            cls.errors = []

        async def observe(self, msg: Msg | list[Msg] | None) -> None:
            await self.memory.add(msg)

        async def reply(
            self,
            input_obj: SubAgentInput,
            **_: Any,
        ) -> Msg:
            assert self.filesystem_service is not None
            self.__class__.captured_ids.append(id(self.filesystem_service))
            self.filesystem_service.write_file(
                "/workspace/subagent/out.txt",
                input_obj.message,
            )

            try:
                self.filesystem_service.write_file(
                    "/workspace/outside.txt",
                    "blocked",
                )
            except Exception as error:  # noqa: BLE001
                assert_access_denied(error)
                self.__class__.errors.append(type(error).__name__)

            return Msg(
                name=self.spec_name,
                content="fs-ok",
                role="assistant",
            )

    async def _run() -> None:
        agent = build_host_agent()
        service = attach_filesystem(agent)
        FilesystemSubAgent.reset()

        tool_name = await agent.register_subagent(
            FilesystemSubAgent,
            build_spec("fs"),
        )

        await invoke_tool(
            agent,
            ToolUseBlock(
                type="tool_use",
                id="fs-1",
                name=tool_name,
                input={"message": "payload"},
            ),
        )

        assert FilesystemSubAgent.captured_ids == [id(service)]
        assert FilesystemSubAgent.errors == ["AccessDeniedError"]
        assert (
            service.read_text_file("/workspace/subagent/out.txt") == "payload"
        )

    asyncio.run(_run())
