# -*- coding: utf-8 -*-
"""Manual specification plan example."""
import asyncio
import os
import tempfile

from agentscope.agent import ReActAgent, UserAgent
from agentscope.filesystem import (
    DiskFileSystem,
    FileDomainService,
    read_text_file,
    write_file,
    edit_file,
    list_directory,
)
from agentscope.formatter import DashScopeChatFormatter
from agentscope.message import Msg
from agentscope.model import DashScopeChatModel
from agentscope.plan import PlanNotebook, SubTask
from agentscope.tool import Toolkit, execute_shell_command, execute_python_code

plan_notebook = PlanNotebook()


async def main() -> None:
    """The main entry point for the manual plan example."""

    # Create the plan manually
    await plan_notebook.create_plan(
        name="Comprehensive Report on AgentScope",
        description="Study the code of AgentScope and write a comprehensive "
        "report about this framework.",
        expected_outcome="A markdown format report summarizing the features, "
        "architecture, advantages/disadvantages, and "
        "potential improvements of AgentScope.",
        subtasks=[
            SubTask(
                name="Clone the repository",
                description="Clone the AgentScope GitHub repository from "
                "agentscope-ai/agentscope, and ensure it's the "
                "latest version.",
                expected_outcome="A local copy of the AgentScope repository.",
            ),
            SubTask(
                name="View the documentation",
                description="View the documentation of AgentScope in the "
                "repository.",
                expected_outcome="A comprehensive understanding of the "
                "features and usage of AgentScope.",
            ),
            SubTask(
                name="Study the code",
                description="Study the code of AgentScope, focusing on the "
                "core modules and their interactions.",
                expected_outcome="A deep understanding of the architecture "
                "and implementation of AgentScope.",
            ),
            SubTask(
                name="Summarize the findings",
                description="Summarize the findings from the documentation "
                "and code study, and write a comprehensive report "
                "in markdown format.",
                expected_outcome="A markdown format report",
            ),
        ],
    )

    # Setup filesystem service
    fs = DiskFileSystem(
        root_dir=tempfile.mkdtemp(prefix="agentscope-plan-fs-"),
    )
    handle = fs.create_handle(
        [
            {
                "prefix": "/workspace/",
                "ops": {"list", "file", "read_binary", "read_file", "write", "delete"},
            },
        ],
    )
    service = FileDomainService(handle)

    # Add basic tools
    toolkit = Toolkit()
    toolkit.register_tool_function(execute_shell_command)
    toolkit.register_tool_function(execute_python_code)
    toolkit.register_tool_function(
        read_text_file,
        preset_kwargs={"service": service},
    )
    toolkit.register_tool_function(
        write_file,
        preset_kwargs={"service": service},
    )
    toolkit.register_tool_function(
        edit_file,
        preset_kwargs={"service": service},
    )
    toolkit.register_tool_function(
        list_directory,
        preset_kwargs={"service": service},
    )

    # Create the agent
    agent = ReActAgent(
        name="Friday",
        sys_prompt="You're a helpful assistant named Friday. Your target is "
        "to finish the given task with careful planning.",
        model=DashScopeChatModel(
            model_name="qwen3-max-preview",
            api_key=os.environ["DASHSCOPE_API_KEY"],
        ),
        formatter=DashScopeChatFormatter(),
        toolkit=toolkit,
        plan_notebook=plan_notebook,
    )
    user = UserAgent(name="user")

    msg = Msg(
        "user",
        "Now start to finish the task by the given plan",
        "user",
    )
    while True:
        msg = await agent(msg)
        msg = await user(msg)
        if msg.get_text_content() == "exit":
            break


asyncio.run(main())
