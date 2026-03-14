# -*- coding: utf-8 -*-
"""
.. _long-term-memory:

Long-Term Memory
========================

AgentScope provides the abstract ``LongTermMemoryBase`` together with
ReMe-backed implementations for personal, task, and tool memories.
ReMe is the primary long-term memory path on ``easy``.

Together with :ref:`agent`, AgentScope supports two long-term memory modes:

- ``agent_control``: the agent manages long-term memory via tool calls
- ``static_control``: the developer explicitly records and retrieves memory

Developers can also use ``both`` to combine the two modes.

.. hint:: ReMe memories require ``reme-ai`` and must be started with
   ``async with`` before calling ``record``/``retrieve`` or the tool-facing
   helper methods.

Using ReMe Personal Memory
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
"""

import asyncio
import os

from agentscope.agent import ReActAgent
from agentscope.embedding import DashScopeTextEmbedding
from agentscope.formatter import DashScopeChatFormatter
from agentscope.memory import InMemoryMemory, ReMePersonalLongTermMemory
from agentscope.message import Msg
from agentscope.model import DashScopeChatModel
from agentscope.tool import Toolkit


def build_long_term_memory() -> ReMePersonalLongTermMemory:
    """Build a ReMe personal memory instance."""
    return ReMePersonalLongTermMemory(
        agent_name="Friday",
        user_name="user_123",
        model=DashScopeChatModel(
            model_name="qwen-max-latest",
            api_key=os.environ.get("DASHSCOPE_API_KEY"),
            stream=False,
        ),
        embedding_model=DashScopeTextEmbedding(
            model_name="text-embedding-v2",
            api_key=os.environ.get("DASHSCOPE_API_KEY"),
        ),
    )


# %%
# ``ReMePersonalLongTermMemory`` provides the same high-level
# ``record`` and ``retrieve`` developer APIs, but runs on top of a started
# ReMe app context.
#
# In the example below, we first store a user preference and then retrieve
# relevant personal memory.


async def basic_usage() -> None:
    """Basic usage example."""
    async with build_long_term_memory() as long_term_memory:
        await long_term_memory.record(
            [
                Msg(
                    "user",
                    "I prefer staying in homestays in Hangzhou.",
                    "user",
                ),
            ],
        )

        results = await long_term_memory.retrieve(
            Msg("user", "What kind of accommodation do I like?", "user"),
        )
        print(f"Retrieval results: {results}")


asyncio.run(basic_usage())

# %%
# Integration with ReAct Agent
# ----------------------------------------
# ``ReActAgent`` accepts both ``long_term_memory`` and
# ``long_term_memory_mode``.
#
# If ``long_term_memory_mode`` is ``agent_control`` or ``both``, the agent
# exposes ``record_to_memory`` and ``retrieve_from_memory`` as toolkit tools.
#
# In ``static_control`` mode, AgentScope retrieves relevant memories before
# each reply and records the final reply after the turn finishes.


async def react_agent_integration() -> None:
    """Use ReMe personal memory with ReActAgent."""
    async with build_long_term_memory() as long_term_memory:
        agent = ReActAgent(
            name="Friday",
            sys_prompt="You are an assistant with long-term memory.",
            model=DashScopeChatModel(
                api_key=os.environ.get("DASHSCOPE_API_KEY"),
                model_name="qwen-max-latest",
            ),
            formatter=DashScopeChatFormatter(),
            toolkit=Toolkit(),
            memory=InMemoryMemory(),
            long_term_memory=long_term_memory,
            long_term_memory_mode="static_control",
        )

        await agent(
            Msg(
                "user",
                "When I travel to Hangzhou, I usually prefer homestays.",
                "user",
            ),
        )

        await agent.memory.clear()
        await agent(
            Msg(
                "user",
                "What accommodation do I usually prefer? Answer briefly.",
                "user",
            ),
        )


asyncio.run(react_agent_integration())

# %%
# Choosing the Right ReMe Memory
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# AgentScope currently provides three ReMe implementations:
#
# .. list-table:: ReMe long-term memory classes in AgentScope
#     :header-rows: 1
#
#     * - Class
#       - Focus
#       - Notes
#     * - ``ReMePersonalLongTermMemory``
#       - User preferences, habits, and personal facts
#       - Best when the agent should remember stable user-specific information
#     * - ``ReMeTaskLongTermMemory``
#       - Task experience and execution trajectories
#       - Supports ``score`` to indicate trajectory quality
#     * - ``ReMeToolLongTermMemory``
#       - Tool execution results and reusable tool guidance
#       - Works best with JSON tool-call records
#
# Developers can still inherit from ``LongTermMemoryBase`` to build custom
# long-term memory systems when the built-in ReMe variants are not enough.
#
# Further Reading
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# - :ref:`memory` - Basic memory system
# - :ref:`agent` - ReAct agent
# - :ref:`tool` - Tool system
