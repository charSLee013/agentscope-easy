# SOP：`agentscope.agent` 核心运行时

## 1. 功能定义

- `agentscope.agent` 提供 AgentScope 的 agent 运行时入口与生命周期抽象。
- 当前公共导出面包含：
  - `AgentBase`
  - `ReActAgentBase`
  - `ReActAgent`
  - `SubAgentBase`
  - `SubAgentSpec`
  - `TaskSubAgent` / `TaskSubAgentInput`
  - `UserInputBase` / `UserInputData` / `TerminalUserInput` / `StudioUserInput`
  - `UserAgent`
  - `A2AAgent`
  - `RealtimeAgent`
- `ReActAgent` 是当前通用的工具调用型 agent 主循环实现。

## 2. 文件映射

- `src/agentscope/agent/__init__.py`：公共导出面。
- `src/agentscope/agent/_agent_base.py`：通用 agent 基类与打印/回复基础能力。
- `src/agentscope/agent/_agent_meta.py`：hook 与元编程包装。
- `src/agentscope/agent/_react_agent_base.py`：ReAct 系基类。
- `src/agentscope/agent/_react_agent.py`：`ReActAgent` 主循环、structured output、tool/memory/RAG 集成入口。
- `src/agentscope/agent/_subagent_base.py`：SubAgent V1 skeleton、delegation context、tool-response folding。
- `src/agentscope/agent/_subagent_tool.py`：SubAgent toolkit wrapper、registration probe、host snapshot collection。
- `src/agentscope/agent/_task_subagent.py`：第一方通用任务执行子 agent。
- `src/agentscope/agent/_user_input.py`：用户输入抽象与终端/Studio 实现。
- `src/agentscope/agent/_user_agent.py`：用户代理。
- `src/agentscope/agent/_a2a_agent.py`：A2A agent。
- `src/agentscope/agent/_realtime_agent.py`：实时 agent。
- `src/agentscope/agent/_utils.py`：agent 侧辅助工具。

## 3. 对外规则

- `ReActAgent.reply()` 是工具调用型 agent 的主回复入口。
- `ReActAgent.register_subagent()` 是 SubAgent V1 的主公共注册入口。
- `structured_model` 仅在本次 `reply()` 调用内生效；其产出的结构化结果固定落在最终 `Msg.metadata`。
- 当 `structured_model` 生效时，reasoning 调用必须强制 `tool_choice="required"`，直到 finish tool 满足结构化输出需求。
- `finish_function_name` 固定为 `generate_response`。
- 当 finish tool 成功且输入中显式包含 `response` 时，该文本就是最终 assistant 回复文本。
- 当本次 `reply()` 未要求 structured output 时，`generate_response` 不应继续保留在 toolkit 可调用面中。
- agent 与工具链的交互必须走 `Toolkit`，不直接绕过 `Toolkit` 执行模型可见工具。
- SubAgent V1 只支持串行 delegation；`parallel_tool_calls=True` 的 host 不得注册 subagent。
- SubAgent V1 的 host memory 只以 snapshot/delegation context 形式进入 subagent，不得回写 host 原消息。
- 第一方 `TaskSubAgent` 通过内部 `ReActAgent` 执行委派任务，并把执行过的工具名写入回复 metadata 的 `tool_trace`。

## 4. 交互调用链

- `AgentBase/ReActAgent` → `Formatter` → `Model`
- `Model` → `Toolkit.call_tool_function()` → tool / MCP callable
- tool 返回 `ToolResponse`
- `ReActAgent` 将 tool 结果折叠为 `ToolResultBlock`、structured metadata 或最终 `Msg`
- Host `ReActAgent.register_subagent()` → subagent tool wrapper → fresh `SubAgentBase` instance → delegated `ReActAgent` / internal logic → `ToolResponse`

## 5. 验收与守门

- `tests/react_agent_test.py` 守护：
  - ReAct hook 基本链路
  - structured output 的 required tool-choice 路径
  - finish tool 直接回复文本与 metadata 透传
- `tests/agent/test_subagent_*.py` 守护：
  - registration / lifecycle / parallel-host rejection
  - model inheritance / memory snapshot / filesystem inheritance
  - built-in `TaskSubAgent` 可用性
- `tests/session_test.py` 继续守护 agent/session 基本集成。
