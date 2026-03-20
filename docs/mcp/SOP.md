# SOP：`agentscope.mcp` MCP 运行时桥接

## 1. 功能定义

- `agentscope.mcp` 负责把 MCP server tool 暴露为 AgentScope 可调用函数。
- 当前公共导出面包含：
  - `MCPClientBase`
  - `MCPToolFunction`
  - `StatefulClientBase`
  - `StdIOStatefulClient`
  - `HttpStatelessClient`
  - `HttpStatefulClient`

## 2. 文件映射

- `src/agentscope/mcp/__init__.py`：公共导出面。
- `src/agentscope/mcp/_client_base.py`：MCP 客户端抽象契约与内容块转换。
- `src/agentscope/mcp/_mcp_function.py`：MCP tool callable 包装。
- `src/agentscope/mcp/_stateful_client_base.py`：stateful client 基类、connect/close/list_tools/get_callable_function。
- `src/agentscope/mcp/_stdio_stateful_client.py`：stdio stateful client。
- `src/agentscope/mcp/_http_stateless_client.py`：HTTP stateless client。
- `src/agentscope/mcp/_http_stateful_client.py`：HTTP stateful client。

## 3. 对外规则

- 所有 MCP client 的 callable 入口都统一为 `get_callable_function(func_name, wrap_tool_result=True, execution_timeout=None)`。
- `execution_timeout` 是显式契约；只要调用方传入值，就必须被保留，包含 `0`。
- stateful client 必须显式 `connect()` / `close()`；`close(ignore_errors=True)` 是默认清理策略。
- `wrap_tool_result=True` 时，MCP 内容必须转换为 AgentScope blocks 并封装成 `ToolResponse`。
- Embedded text resource 必须转换成 `TextBlock`；不支持的 MCP 内容类型只能跳过并记录日志，不能静默伪装成别的类型。

## 4. 交互调用链

- `Toolkit` / 调用方 → MCP client
- MCP client → `MCPToolFunction`
- `MCPToolFunction` → MCP session / disposable client → `call_tool`
- MCP result → `_convert_mcp_content_to_as_blocks()` → `ToolResponse`（若 `wrap_tool_result=True`）

## 5. 验收与守门

- `tests/mcp_client_test.py` 守护：
  - 抽象签名与具体实现的 `execution_timeout` 对齐
  - `execution_timeout=0` 保留
  - stateful cleanup 的 raise / swallow 语义
- `tests/mcp_streamable_http_client_test.py` 守护 streamable HTTP 和 embedded content 转换。
