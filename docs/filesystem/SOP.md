# SOP：`agentscope.filesystem` Phase 1 Filesystem MVP

## 1. 功能定义

- `agentscope.filesystem` 提供受控的逻辑文件系统 MVP，服务于 Host/Toolkit 下的文件读写能力。
- 本期只交付：
  - 路径校验与授权模型
  - `InMemoryFileSystem` / `DiskFileSystem`
  - `FileDomainService`
  - 受控 tool functions 与权限诊断
  - Host/Toolkit 最小 wiring
- 本期明确不交付：
  - search / RAG / builtin filesystem
  - raw OS 文本 I/O
  - `AGENTSCOPE_DANGEROUS_TEXT_IO`

## 2. 文件映射

- `src/agentscope/filesystem/_types.py`：路径、授权、元信息类型。
- `src/agentscope/filesystem/_errors.py`：filesystem MVP 异常。
- `src/agentscope/filesystem/_base.py`：逻辑文件系统抽象基类。
- `src/agentscope/filesystem/_handle.py`：授权句柄与路径校验。
- `src/agentscope/filesystem/_memory.py`：内存后端。
- `src/agentscope/filesystem/_disk.py`：磁盘后端。
- `src/agentscope/filesystem/_service.py`：`FileDomainService` 域策略与工具装配入口。
- `src/agentscope/filesystem/_tools.py`：受控工具函数。
- `src/agentscope/filesystem/__init__.py`：公共导出面。

## 3. 对外规则

- 所有模型可调用的文件能力必须通过 `FileDomainService` 暴露。
- `FileDomainService` Phase 1 固定域策略：
  - `/userinput/`：可读、不可写、不可删。
  - `/workspace/`：可读、可写、可删。
  - `/internal/`：默认不在目录发现结果中展示；显式授权路径可读写，不可删。
- 工具注入方式固定为：
  - `Toolkit.register_tool_function(tool, preset_kwargs={"service": service})`
- 工具 schema 不得暴露绑定后的 `service` 参数。
- SubAgent V1 若继承 `filesystem_service`，只能继承 host 已有 `FileDomainService` 策略，不得扩权，不得创建更宽的 grant。
- 第一方 `TaskSubAgent` 使用的 filesystem 工具也必须来自继承的 `FileDomainService.tool_functions()`。

## 4. 交互调用链

- Host/Agent → `Toolkit` → tool function → `FileDomainService` → `FsHandle` → backend
- `FsHandle` 负责：
  - 路径合法性校验
  - grant 授权判定
  - 通过 backend snapshot 获取当前可见视图
- backend 只负责逻辑路径对应的数据读写，不直接暴露给模型。

## 5. 验收与守门

- `import agentscope.filesystem` 可用，且 `import agentscope` 暴露 `filesystem` 子模块。
- Host agent 可经 `Toolkit` 成功调用授权内 filesystem 工具。
- 越权写 `/userinput/` 时，错误通过 host tool loop 反馈，而不是直接崩溃。
- `/internal/` 不进入默认目录发现，但显式授权路径可访问。
- 文件切片读取必须保留原始源码行号。
