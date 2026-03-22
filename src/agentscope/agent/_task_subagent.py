# -*- coding: utf-8 -*-
"""First-party generic task-execution subagent."""
from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field

from ..message import Msg
from ._subagent_base import SubAgentBase


class TaskSubAgentInput(BaseModel):
    """Input schema for the first-party generic task subagent."""

    task: str = Field(description="The delegated task to execute.")
    success_criteria: str | None = Field(
        default=None,
        description="Optional success criteria for the delegated task.",
    )


class TaskSubAgent(SubAgentBase):
    """A generic delegated worker that executes one task with tools."""

    InputModel = TaskSubAgentInput

    async def observe(self, msg: Msg | list[Msg] | None) -> None:
        """Record observed messages into the subagent-local memory."""
        await self.memory.add(msg)

    async def reply(
        self,
        input_obj: TaskSubAgentInput,
        **_: Any,
    ) -> Msg:
        """Execute the delegated task through an internal ReAct loop."""
        if self.model_override is None:
            raise RuntimeError(
                "TaskSubAgent requires an inherited host model.",
            )
        if self.formatter_override is None:
            raise RuntimeError(
                "TaskSubAgent requires an inherited host formatter.",
            )

        from ._react_agent import ReActAgent

        worker = ReActAgent(
            name=f"{self.spec_name}_worker",
            sys_prompt=self._build_worker_prompt(),
            model=self.model_override,
            formatter=self.formatter_override,
            toolkit=self.toolkit,
            memory=self.memory,
            max_iters=6,
        )
        reply_msg = await worker.reply(
            Msg(
                name=self.permissions.supervisor_name,
                content=self._build_task_message(input_obj),
                role="user",
            ),
        )

        tool_trace = await self._collect_tool_trace()
        metadata = dict(reply_msg.metadata or {})
        metadata["tool_trace"] = tool_trace
        reply_msg.metadata = metadata
        return reply_msg

    def _build_worker_prompt(self) -> str:
        """Build the system prompt for the delegated worker."""
        prompt = [
            "You are a delegated task executor.",
            "Complete the assigned task using the available tools.",
            "Stay within inherited filesystem permissions.",
        ]
        if self.filesystem_service is not None and hasattr(
            self.filesystem_service,
            "describe_permissions_markdown",
        ):
            prompt.append(
                "Filesystem grants:\n"
                + self.filesystem_service.describe_permissions_markdown(),
            )
        return "\n".join(prompt)

    def _build_task_message(
        self,
        input_obj: TaskSubAgentInput,
    ) -> str:
        """Build the delegated task message."""
        lines = [f"Task:\n{input_obj.task}"]
        if input_obj.success_criteria:
            lines.append(
                f"Success criteria:\n{input_obj.success_criteria}",
            )
        if self._delegation_context is not None:
            if self._delegation_context.workspace_pointers:
                lines.append(
                    "Visible filesystem roots: "
                    + ", ".join(self._delegation_context.workspace_pointers),
                )
            if self._delegation_context.recent_events:
                preview = self._delegation_context.recent_events[0].get(
                    "preview",
                    "",
                )
                lines.append(f"Recent context preview: {preview}")
        return "\n\n".join(lines)

    async def _collect_tool_trace(self) -> list[str]:
        """Collect tool names executed during this delegated task."""
        memory_messages = await self.memory.get_memory(prepend_summary=False)
        tool_trace: list[str] = []
        for msg in memory_messages:
            if msg.role != "system" or not isinstance(msg.content, list):
                continue
            for block in msg.content:
                if block.get("type") == "tool_result" and block.get("name"):
                    tool_trace.append(str(block["name"]))
        return tool_trace
