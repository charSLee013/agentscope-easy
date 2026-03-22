# -*- coding: utf-8 -*-
"""Built-in TaskSubAgent tests."""
from __future__ import annotations

import asyncio
from typing import Any

import agentscope

from agentscope.message import TextBlock, ToolUseBlock
from agentscope.model import ChatModelBase, ChatResponse

from ._shared import attach_filesystem, build_host_agent, invoke_tool


class TaskExecutionModel(ChatModelBase):
    """Deterministic model that writes once, then returns a final reply."""

    def __init__(self) -> None:
        super().__init__("task-execution-model", stream=False)
        self.call_count = 0

    async def __call__(
        self,
        _messages: list[dict],
        **kwargs: Any,
    ) -> ChatResponse:
        self.call_count += 1
        if self.call_count == 1:
            return ChatResponse(
                content=[
                    ToolUseBlock(
                        type="tool_use",
                        id="task-write-1",
                        name="write_file",
                        input={
                            "path": "/workspace/subagent/task_result.txt",
                            "content": "delegated output",
                        },
                    ),
                ],
            )
        return ChatResponse(
            content=[
                TextBlock(
                    type="text",
                    text="delegated task complete",
                ),
            ],
        )


def test_builtin_task_subagent_is_public_and_executes_task() -> None:
    """The built-in task subagent should be public and usable."""
    from agentscope.agent import SubAgentSpec, TaskSubAgent

    async def _run() -> None:
        assert hasattr(agentscope.agent, "TaskSubAgent")
        assert hasattr(agentscope.agent, "TaskSubAgentInput")
        assert hasattr(agentscope.agent, "SubAgentSpec")
        assert not hasattr(agentscope, "TaskSubAgent")

        host = build_host_agent()
        host.model = TaskExecutionModel()
        service = attach_filesystem(host)

        tool_name = await host.register_subagent(
            TaskSubAgent,
            SubAgentSpec(
                name="task_executor",
                description="Execute a delegated task.",
            ),
        )

        response = await invoke_tool(
            host,
            ToolUseBlock(
                type="tool_use",
                id="task-subagent-1",
                name=tool_name,
                input={
                    "task": (
                        "Write delegated output to "
                        "/workspace/subagent/task_result.txt"
                    ),
                },
            ),
        )

        assert (
            service.read_text_file(
                "/workspace/subagent/task_result.txt",
            )
            == "delegated output"
        )
        assert response.metadata is not None
        assert response.metadata["subagent"] == "task_executor"
        assert response.metadata["response_metadata"]["tool_trace"] == [
            "write_file",
        ]

    asyncio.run(_run())
