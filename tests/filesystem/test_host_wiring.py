# -*- coding: utf-8 -*-
"""Host/Toolkit wiring tests for the filesystem MVP."""
from __future__ import annotations

from typing import Any
from unittest import IsolatedAsyncioTestCase

import agentscope
from agentscope.agent import ReActAgent
from agentscope.filesystem import InMemoryFileSystem
from agentscope.filesystem._service import FileDomainService
from agentscope.formatter import DashScopeChatFormatter
from agentscope.memory import InMemoryMemory
from agentscope.message import TextBlock, ToolUseBlock
from agentscope.model import ChatModelBase, ChatResponse
from agentscope.tool import Toolkit


class SingleToolModel(ChatModelBase):
    """Minimal fake model that emits one tool call, then a final answer."""

    def __init__(
        self,
        tool_name: str,
        tool_input: dict,
        final_text: str = "done",
    ) -> None:
        super().__init__("filesystem-test-model", stream=False)
        self._tool_name = tool_name
        self._tool_input = tool_input
        self._final_text = final_text
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
                        id="tool-1",
                        name=self._tool_name,
                        input=self._tool_input,
                    ),
                ],
            )
        return ChatResponse(
            content=[TextBlock(type="text", text=self._final_text)],
        )


class HostFilesystemWiringTest(IsolatedAsyncioTestCase):
    """Host-level tests for filesystem tool wiring."""

    async def test_agentscope_exports_filesystem_module(self) -> None:
        """`import agentscope` should expose the filesystem public module."""
        assert hasattr(agentscope, "filesystem")
        assert hasattr(agentscope.filesystem, "FileDomainService")

    async def test_host_agent_executes_authorized_workspace_write(
        self,
    ) -> None:
        """A host agent should be able to call the workspace write tool."""
        fs = InMemoryFileSystem()
        service = FileDomainService(
            fs.create_handle(
                [
                    {
                        "prefix": "/workspace/",
                        "ops": {
                            "list",
                            "file",
                            "read_binary",
                            "read_file",
                            "read_re",
                            "write",
                            "delete",
                        },
                    },
                ],
            ),
        )
        toolkit = Toolkit()
        for tool in service.tool_functions():
            toolkit.register_tool_function(
                tool,
                preset_kwargs={"service": service},
            )

        model = SingleToolModel(
            "write_file",
            {"path": "/workspace/out.txt", "content": "payload"},
            final_text="workspace write complete",
        )
        agent = ReActAgent(
            name="Friday",
            sys_prompt="You are a helpful assistant.",
            model=model,
            formatter=DashScopeChatFormatter(),
            memory=InMemoryMemory(),
            toolkit=toolkit,
        )

        msg = await agent()
        assert msg.content[0]["text"] == "workspace write complete"
        assert service.read_text_file("/workspace/out.txt") == "payload"
        assert model.call_count == 2

    async def test_host_agent_surfaces_denied_userinput_write(self) -> None:
        """A denied tool call should surface through the host loop."""
        fs = InMemoryFileSystem()
        service = FileDomainService(
            fs.create_handle(
                [
                    {
                        "prefix": "/userinput/",
                        "ops": {
                            "list",
                            "file",
                            "read_binary",
                            "read_file",
                            "read_re",
                            "write",
                            "delete",
                        },
                    },
                    {
                        "prefix": "/workspace/",
                        "ops": {
                            "list",
                            "file",
                            "read_binary",
                            "read_file",
                            "read_re",
                            "write",
                            "delete",
                        },
                    },
                ],
            ),
        )
        toolkit = Toolkit()
        for tool in service.tool_functions():
            toolkit.register_tool_function(
                tool,
                preset_kwargs={"service": service},
            )

        model = SingleToolModel(
            "write_file",
            {"path": "/userinput/blocked.txt", "content": "nope"},
            final_text="denied path handled",
        )
        memory = InMemoryMemory()
        agent = ReActAgent(
            name="Friday",
            sys_prompt="You are a helpful assistant.",
            model=model,
            formatter=DashScopeChatFormatter(),
            memory=memory,
            toolkit=toolkit,
        )

        await agent()
        messages = await memory.get_memory(prepend_summary=False)
        tool_result_msgs = [
            msg
            for msg in messages
            if msg.role == "system" and isinstance(msg.content, list)
        ]
        assert any(
            "Access denied" in block["output"][0]["text"]
            for msg in tool_result_msgs
            for block in msg.content
        )
