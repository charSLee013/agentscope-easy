# -*- coding: utf-8 -*-
"""The main entry point of the ReAct agent example."""
import asyncio
import os
import tempfile

from agentscope.agent import ReActAgent, UserAgent
from agentscope.filesystem import (
    DiskFileSystem,
    FileDomainService,
    read_text_file,
)
from agentscope.formatter import DashScopeChatFormatter
from agentscope.memory import InMemoryMemory
from agentscope.model import DashScopeChatModel
from agentscope.tool import Toolkit, execute_shell_command, execute_python_code
from agentscope.tts import DashScopeRealtimeTTSModel


async def main() -> None:
    """The main entry point for the ReAct agent example."""
    toolkit = Toolkit()
    toolkit.register_tool_function(execute_shell_command)
    toolkit.register_tool_function(execute_python_code)

    # Setup filesystem service
    fs = DiskFileSystem(
        root_dir=tempfile.mkdtemp(prefix="agentscope-tts-fs-"),
    )
    handle = fs.create_handle(
        [
            {
                "prefix": "/workspace/",
                "ops": {
                    "list",
                    "file",
                    "read_binary",
                    "read_file",
                    "write",
                    "delete",
                },
            },
        ],
    )
    service = FileDomainService(handle)
    toolkit.register_tool_function(
        read_text_file,
        preset_kwargs={"service": service},
    )

    agent = ReActAgent(
        name="Friday",
        sys_prompt="You are a helpful assistant named Friday.",
        model=DashScopeChatModel(
            api_key=os.environ.get("DASHSCOPE_API_KEY"),
            model_name="qwen3-max",
            enable_thinking=False,
            stream=True,
        ),
        formatter=DashScopeChatFormatter(),
        toolkit=toolkit,
        memory=InMemoryMemory(),
        # Specify the TTS model for real-time speech synthesis
        tts_model=DashScopeRealtimeTTSModel(
            model_name="qwen3-tts-flash-realtime",
            api_key=os.environ.get("DASHSCOPE_API_KEY"),
            voice="Cherry",
            stream=False,
        ),
    )
    user = UserAgent("User")

    msg = None
    while True:
        msg = await user(msg)
        if msg.get_text_content() == "exit":
            break
        msg = await agent(msg)


asyncio.run(main())
