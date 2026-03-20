# Design: `easy-next` Phase 1 Filesystem MVP

## Summary

本设计定义 `easy-next` 的第一波重建目标：在最新 `main` 上正式引入
`agentscope.filesystem`，交付一个可发布的 Filesystem MVP，而不是继续
延长 `easy -> main` 的吸收战线。

本波只做四层能力：

1. 逻辑文件系统内核
2. `FileDomainService`
3. 受控 filesystem 工具与权限诊断
4. Host/Toolkit 最小 wiring

明确不做：`SubAgent` 恢复、raw OS 文本 I/O、search、RAG extras、旧 easy
兼容层。

## Frozen Decisions

- 基础分支：当前 `main` HEAD
- 工作分支：`034-easy-next-filesystem-mvp`
- 风格基准：最新 `main`
- 公开形态：`agentscope.filesystem` 为正式公开模块
- Agent 集成：Host/Toolkit only
- 审查协议：每个大块操作后必须由 subagent 审查设计一致性

## Architecture

### 1. Filesystem Kernel

目标是提供一个纯逻辑路径空间，而不是复刻 OS 文件系统。

核心对象：

- `FileSystemBase`
- `FsHandle`
- `Grant` / `EntryMeta` / path validation
- `InMemoryFileSystem`
- `DiskFileSystem`

语义原则：

- 所有路径都是逻辑绝对路径
- 所有权限都通过 grants 判定
- 外部只能经由 handle 访问
- 不暴露宿主真实路径给模型

### 2. FileDomainService

`FileDomainService` 是 Filesystem MVP 的服务层，负责：

- 将 Host 的 handle 能力整理为稳定、受控的服务接口
- 在 service 层表达目录角色和权限策略
- 给 tool 层提供稳定依赖，避免 tool 直接依赖底层 handle

本波保留的 service 能力：

- 列目录
- 文件信息
- 读取文本
- 多文件读取
- 写文件
- 编辑文件
- 删除文件
- 导出权限 markdown

Phase 1 对 `/internal/` 的固定规则是：它不进入默认目录发现入口，但
若调用方已经持有显式 `/internal/...` 路径且 handle 已授予权限，
service/tool 仍允许执行该显式访问；其中 `/internal/` 允许显式读/写、
默认不可删。

### 3. Tool Surface

公开的 tool-facing 能力只允许来自受控 filesystem 工具集。

必须满足：

- tool schema 不暴露注入的 `service`
- 工具名称与行为保持稳定
- 诊断工具（权限 markdown）属于计划内能力

本波明确禁止：

- raw OS 文本工具
- `AGENTSCOPE_DANGEROUS_TEXT_IO`
- 任何绕过 `FileDomainService` 的 tool-facing 接口

### 4. Host Wiring

第一波只做到 Host/Toolkit 可用：

- Host agent 可注册 filesystem 工具
- 工具在授权路径内工作
- 越权路径稳定失败
- `/internal/` 不通过默认目录发现暴露，但显式授权路径读/写仍可工作，删除默认拒绝

第一波不做：

- `SubAgent` 文件系统能力继承
- `filesystem_service` 自动透传
- 子代理命名空间约束链路

## Implementation Shape

### Public APIs

计划引入或恢复以下公开面：

- `agentscope.filesystem`
- 其中的基础类型、错误、handle、base、两个 backend

计划引入或恢复以下半公开/集成面：

- `FileDomainService`
- 受控 filesystem 工具函数

### Explicit Exclusions

以下内容即使在旧 `easy` 中存在，本波也不实现：

- `SubAgent` 相关 filesystem 自动继承
- raw text I/O 工具与其护栏
- 旧 easy 命名或兼容包装

## Test Plan

### Module Tests

- path validation
- grants/permission enforcement
- handle read/write/delete/list
- overwrite / not-found / access-denied semantics
- `InMemory` 与 `Disk` 后端行为

### Service/Tool Tests

- `FileDomainService` 核心接口
- toolkit 注册后 schema 不暴露 `service`
- 权限 markdown 输出
- `/internal/` 不出现在默认目录发现，但显式授权路径读/写可通过，删除默认拒绝

### Host Wiring Tests

- Host agent 可调用 filesystem 工具
- 授权内成功
- 越权失败
- 默认目录发现不泄露 `/internal/`，但显式授权 `/internal/...` 读/写可成功，删除默认拒绝

### Negative Scope Tests

- 不出现 raw OS 文本工具公开入口
- 不出现 `SubAgent` filesystem 自动继承契约

## Review Protocol

每个大块操作后必须运行一次 subagent 审查，审查只回答四件事：

1. 是否符合冻结设计
2. 是否混入计划外逻辑
3. 是否引入了 Phase 2/3 内容
4. 是否需要清理或回退

审查失败即暂停主流程，先清理后继续。

## Success Criteria

- Filesystem MVP 在最新 `main` 上落地并可验证
- 公开面、测试、SOP、长线文档一致
- 没有把 `SubAgent` 恢复偷带进第一波
- 最终 proof loop 成功并生成 manifest
