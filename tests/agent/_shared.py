# -*- coding: utf-8 -*-
"""Shared fixtures and doubles for SubAgent V1 tests."""
from __future__ import annotations

from typing import TYPE_CHECKING, Any

from pydantic import BaseModel

from agentscope.agent import ReActAgent
from agentscope.filesystem import InMemoryFileSystem
from agentscope.filesystem._errors import AccessDeniedError
from agentscope.filesystem._service import FileDomainService
from agentscope.formatter import DashScopeChatFormatter
from agentscope.memory import InMemoryMemory
from agentscope.message import TextBlock, ToolUseBlock
from agentscope.model import ChatModelBase, ChatResponse
from agentscope.tool import Toolkit

if TYPE_CHECKING:  # pragma: no cover
    from agentscope.agent._subagent_tool import SubAgentSpec
    from agentscope.tool import ToolResponse


class StaticModel(ChatModelBase):
    """Deterministic chat model returning a plain text chunk."""

    def __init__(self, name: str = "static") -> None:
        super().__init__(name, stream=False)

    async def __call__(
        self,
        _messages: list[dict],
        **kwargs: Any,
    ) -> ChatResponse:
        return ChatResponse(
            content=[TextBlock(type="text", text=self.model_name)],
        )


def build_host_agent(*, parallel: bool = False) -> ReActAgent:
    """Construct a deterministic host agent for delegation tests."""
    return ReActAgent(
        name="Supervisor",
        sys_prompt="You are a supervisor agent.",
        model=StaticModel(),
        formatter=DashScopeChatFormatter(),
        memory=InMemoryMemory(),
        toolkit=Toolkit(),
        parallel_tool_calls=parallel,
    )


def attach_filesystem(agent: ReActAgent) -> FileDomainService:
    """Attach a narrow filesystem policy to the host agent."""
    fs = InMemoryFileSystem()
    handle = fs.create_handle(
        [
            {
                "prefix": "/workspace/subagent/",
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
    )
    service = FileDomainService(handle)
    agent.filesystem_service = service
    return service


class SubAgentInput(BaseModel):
    """Common input schema used in core SubAgent tests."""

    message: str = "placeholder"
    tag: str | None = None


class EchoSubAgentMixin:
    """Reusable state buckets for echo-like subagent tests."""

    memory_sizes: list[int] = []
    delegation_payloads: list[dict[str, Any]] = []
    instance_ids: list[int] = []

    @classmethod
    def reset(cls) -> None:
        """Clear captured subagent state between assertions."""
        cls.memory_sizes = []
        cls.delegation_payloads = []
        cls.instance_ids = []


def build_spec(name: str) -> "SubAgentSpec":
    """Build a minimal SubAgent spec."""
    from agentscope.agent._subagent_tool import SubAgentSpec

    return SubAgentSpec(name=name)


async def invoke_tool(
    agent: ReActAgent,
    tool_call: ToolUseBlock,
) -> "ToolResponse":
    """Execute a registered tool and return the last response chunk."""
    chunk = None
    response_stream = await agent.toolkit.call_tool_function(tool_call)
    async for chunk in response_stream:
        pass
    assert chunk is not None
    return chunk


def assert_access_denied(error: Exception) -> None:
    """Small helper for filesystem denial assertions."""
    assert isinstance(error, AccessDeniedError)
