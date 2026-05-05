# -*- coding: utf-8 -*-
"""The main entry point of the agent skill example."""
import asyncio
import os
import tempfile

from agentscope.agent import ReActAgent
from agentscope.filesystem import (
    DiskFileSystem,
    FileDomainService,
    read_text_file,
)
from agentscope.formatter import DashScopeChatFormatter
from agentscope.memory import InMemoryMemory
from agentscope.message import Msg
from agentscope.model import DashScopeChatModel
from agentscope.tool import Toolkit, execute_shell_command, execute_python_code


async def main() -> None:
    """The main entry point for the ReAct agent example."""
    toolkit = Toolkit()

    # To use agent skills, your agent must be equipped with text file viewing
    # tools.
    toolkit.register_tool_function(execute_shell_command)
    toolkit.register_tool_function(execute_python_code)

    # Setup filesystem service
    skill_dir = os.path.join(
        os.path.dirname(__file__),
        "skill",
        "analyzing-agentscope-library",
    )
    fs = DiskFileSystem(
        root_dir=tempfile.mkdtemp(prefix="agentscope-skill-fs-"),
        internal_dir=os.path.join(os.path.dirname(__file__), "skill"),
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
            {
                "prefix": "/internal/",
                "ops": {"list", "file", "read_binary", "read_file"},
            },
        ],
    )
    service = FileDomainService(handle)
    toolkit.register_tool_function(
        read_text_file,
        preset_kwargs={"service": service},
    )

    # Register the agent skill
    toolkit.register_agent_skill(
        skill_dir,
        logical_dir="/internal/analyzing-agentscope-library",
    )

    agent = ReActAgent(
        name="Friday",
        sys_prompt="""You are a helpful assistant named Friday.

# IMPORTANT
- Don't make any assumptions. All your knowledge about AgentScope library must come from your equipped skills.
""",  # noqa: E501
        model=DashScopeChatModel(
            api_key=os.environ.get("DASHSCOPE_API_KEY"),
            model_name="qwen3-max",
            enable_thinking=False,
            stream=True,
        ),
        formatter=DashScopeChatFormatter(),
        toolkit=toolkit,
        memory=InMemoryMemory(),
    )

    # First, let's take a look at the agent's system prompt
    print("\033[1;32mAgent System Prompt:\033[0m")
    print(agent.sys_prompt)
    print("\n")

    print(
        "\033[1;32mResponse to Question 'What skills do you have?':\033[0m",
    )
    # We prepare two questions
    await agent(
        Msg("user", "What skills do you have?", "user"),
    )

    print(
        "\n\033[1;32mResponse to Question 'How to create my own tool function "
        "for the agent in agentscope?':\033[0m",
    )
    # The second question
    await agent(
        Msg(
            "user",
            "How to custom tool function for the agent in agentscope?",
            "user",
        ),
    )


asyncio.run(main())
