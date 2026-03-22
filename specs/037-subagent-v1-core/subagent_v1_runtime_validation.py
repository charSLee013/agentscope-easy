# -*- coding: utf-8 -*-
"""Real local proof entry for SubAgent V1."""
from __future__ import annotations

import argparse
import asyncio
import json
from pathlib import Path
from typing import Any

from agentscope.agent import ReActAgent, SubAgentSpec, TaskSubAgent
from agentscope.filesystem import DiskFileSystem
from agentscope.filesystem._service import FileDomainService
from agentscope.formatter import DashScopeChatFormatter
from agentscope.memory import InMemoryMemory
from agentscope.message import TextBlock, ToolUseBlock
from agentscope.model import ChatModelBase, ChatResponse
from agentscope.tool import Toolkit


class TaskExecutionModel(ChatModelBase):
    """Deterministic local model used for the SubAgent V1 proof."""

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


async def _invoke_tool(agent: ReActAgent, tool_call: ToolUseBlock) -> Any:
    chunk = None
    response_stream = await agent.toolkit.call_tool_function(tool_call)
    async for chunk in response_stream:
        pass
    assert chunk is not None
    return chunk


async def run_validation(output_dir: Path) -> dict[str, Any]:
    """Run the real local host -> subagent -> filesystem proof chain."""
    output_dir.mkdir(parents=True, exist_ok=True)
    fs_root = output_dir / "fs"
    fs = DiskFileSystem(root_dir=str(fs_root))
    service = FileDomainService(
        fs.create_handle(
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
        ),
    )

    host = ReActAgent(
        name="Supervisor",
        sys_prompt="You are a supervisor.",
        model=TaskExecutionModel(),
        formatter=DashScopeChatFormatter(),
        memory=InMemoryMemory(),
        toolkit=Toolkit(),
    )
    host.filesystem_service = service

    tool_name = await host.register_subagent(
        TaskSubAgent,
        SubAgentSpec(
            name="task_executor",
            description="Execute one delegated task.",
        ),
    )

    response = await _invoke_tool(
        host,
        ToolUseBlock(
            type="tool_use",
            id="proof-1",
            name=tool_name,
            input={
                "task": (
                    "Write delegated output to "
                    "/workspace/subagent/task_result.txt"
                ),
            },
        ),
    )

    workspace_text = service.read_text_file(
        "/workspace/subagent/task_result.txt",
    )
    response_metadata = response.metadata["response_metadata"]
    reply_text = response.content[0]["text"]
    proof = {
        "subagent": response.metadata["subagent"],
        "subagent_tool": tool_name,
        "reply_text": reply_text,
        "output_text": workspace_text,
        "tool_trace": response_metadata["tool_trace"],
        "workspace_file": str(
            fs_root / "workspace" / "subagent" / "task_result.txt",
        ),
    }

    proof_path = output_dir / "proof.json"
    proof_path.write_text(
        json.dumps(proof, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    return proof


def main() -> None:
    """CLI entry for the SubAgent V1 local proof."""
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("artifacts/subagent_v1_runtime"),
    )
    args = parser.parse_args()

    proof = asyncio.run(run_validation(args.output_dir))
    print(json.dumps(proof, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
