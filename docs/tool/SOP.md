# SOP：`agentscope.tool` 核心工具运行时

## 1. 功能定义

- `agentscope.tool` 提供 AgentScope 的统一工具注册、schema 暴露与结果封装能力。
- 核心公共契约是：
  - `Toolkit`
  - `ToolResponse`
- 其它具体工具族可以存在，但它们都必须服从 `Toolkit` / `ToolResponse` 这一层的统一契约。

## 2. 文件映射

- `src/agentscope/tool/__init__.py`：公共导出面。
- `src/agentscope/tool/_toolkit.py`：工具注册、分组、meta tool、调用执行与 middleware 主入口。
- `src/agentscope/tool/_types.py`：`RegisteredToolFunction`、`ToolGroup`、`AgentSkill` 等核心类型。
- `src/agentscope/tool/_response.py`：`ToolResponse` 统一返回类型。
- `src/agentscope/tool/_async_wrapper.py`：同步/异步函数与生成器包装。

## 3. 对外规则

- 所有模型可见工具都必须通过 `Toolkit.register_tool_function()` 或 MCP 注册链进入 toolkit。
- `ToolResponse` 是工具结果的统一承载面；tool loop 不直接约定裸字符串或裸字典。
- duplicate tool name 的冲突处理只允许通过 `namesake_strategy` 明确声明。
- tool group 的启停只通过 group 状态和 `reset_equipped_tools` 协调，不在 schema 外维护第二套隐藏开关。
- `extended_model` 只用于扩展 tool schema；若字段与原函数 schema 冲突，应直接报错。
- agent skill 信息由 toolkit 聚合进 system prompt，不在 agent 层复制维护第二份技能注册真相。
- SubAgent wrapper 注册进 toolkit 后，仍然只是普通 tool function；它不能绕开 toolkit 获得“隐藏并行能力”或额外权限。

## 4. 交互调用链

- Agent / Host → `Toolkit`
- `Toolkit` → 已注册函数 / MCP callable / middleware
- 工具执行 → `ToolResponse`
- `ToolResponse` → `ToolResultBlock` → Agent memory / final reply

## 5. 验收与守门

- `tests/toolkit_basic_test.py` 守护：
  - duplicate registration / rename / `func_name`
  - nested `$defs` merge
  - postprocess / middleware / 分组行为
- `tests/toolkit_meta_tool_test.py` 守护 `reset_equipped_tools` 与 group 激活/失活链路。
