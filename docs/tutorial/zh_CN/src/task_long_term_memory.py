# -*- coding: utf-8 -*-
"""
.. _long-term-memory:

长期记忆
========================

AgentScope 提供了抽象基类 ``LongTermMemoryBase``，以及基于 ReMe 的
个人、任务、工具三类长期记忆实现。在 ``easy`` 分支上，ReMe 是长期记忆的
主路线。

结合 :ref:`agent` 章节中的 ``ReActAgent``，AgentScope 支持两种长期记忆模式：

- ``agent_control``：智能体通过工具调用自主管理长期记忆
- ``static_control``：开发者显式控制长期记忆的记录与检索

当然，也可以使用 ``both`` 同时启用这两种模式。

.. hint:: ReMe 长期记忆依赖 ``reme-ai``，并且必须先通过 ``async with``
   启动 app context，之后才能调用 ``record``/``retrieve`` 或工具接口。

使用 ReMe 个人长期记忆
~~~~~~~~~~~~~~~~~~~~~~~~
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
    """构造一个 ReMe 个人长期记忆实例。"""
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
# ``ReMePersonalLongTermMemory`` 仍然提供开发者熟悉的
# ``record`` 与 ``retrieve`` 高层接口，只是它们运行在已经启动的
# ReMe app context 之上。


async def basic_usage() -> None:
    """基本使用示例。"""
    async with build_long_term_memory() as long_term_memory:
        await long_term_memory.record(
            [Msg("user", "我去杭州旅行时通常更喜欢住民宿。", "user")],
        )

        results = await long_term_memory.retrieve(
            Msg("user", "我通常喜欢什么样的住宿？", "user"),
        )
        print(f"检索结果: {results}")


asyncio.run(basic_usage())

# %%
# 与 ReAct 智能体集成
# ----------------------------------------
# ``ReActAgent`` 同时接收 ``long_term_memory`` 与
# ``long_term_memory_mode``。
#
# 如果 ``long_term_memory_mode`` 是 ``agent_control`` 或 ``both``，
# 智能体会把 ``record_to_memory`` 与 ``retrieve_from_memory`` 注册为工具。
#
# 在 ``static_control`` 模式下，AgentScope 会在每轮回复前检索相关记忆，
# 并在回复结束后记录最终回复。


async def react_agent_integration() -> None:
    """在 ReActAgent 中使用 ReMe 个人长期记忆。"""
    async with build_long_term_memory() as long_term_memory:
        agent = ReActAgent(
            name="Friday",
            sys_prompt="你是一个具有长期记忆能力的助手。",
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
                "我去杭州旅行时通常更喜欢住民宿。",
                "user",
            ),
        )

        await agent.memory.clear()
        await agent(
            Msg(
                "user",
                "我通常喜欢什么样的住宿？请简短回答。",
                "user",
            ),
        )


asyncio.run(react_agent_integration())

# %%
# 选择合适的 ReMe 长期记忆
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# AgentScope 当前提供三种 ReMe 长期记忆实现：
#
# .. list-table:: AgentScope 中的 ReMe 长期记忆类
#     :header-rows: 1
#
#     * - 类
#       - 关注点
#       - 说明
#     * - ``ReMePersonalLongTermMemory``
#       - 用户偏好、习惯与个人事实
#       - 适合存储稳定的、用户相关的信息
#     * - ``ReMeTaskLongTermMemory``
#       - 任务经验与执行轨迹
#       - 支持 ``score`` 表示轨迹质量
#     * - ``ReMeToolLongTermMemory``
#       - 工具执行结果与可复用工具指南
#       - 更适合记录 JSON 形式的工具调用结果
#
# 如果内置的 ReMe 变体仍然不够用，开发者也可以继续继承
# ``LongTermMemoryBase`` 自定义长期记忆系统。
#
# 进一步阅读
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# - :ref:`memory` - 基础记忆系统
# - :ref:`agent` - ReAct 智能体
# - :ref:`tool` - 工具系统
