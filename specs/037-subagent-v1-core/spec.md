# Feature Specification: Rebuild SubAgent V1 core on the new `easy` trunk

**Feature Branch**: `037-subagent-v1-core`
**Base Branch**: `easy`
**Created**: 2026-03-22
**Status**: Draft
**Input**: User direction: "把 `easy` 历史里仍有杠杆效应的 SubAgent 能力，以当前最新 `main`/`easy` 代码形态重新实现一次；只保留现在仍值得存在的部分。"

## Clarifications

- 本波次是长线 selective rebuild 的 `SubAgent V1` 主波次，地位与 tracing 并列，不再作为 tracing 的附属能力。
- 本波次目标不是“恢复旧 easy 全量 SubAgent”，而是只交付当前最新 `easy` 上仍然有价值、且能真实运行证明的最小可用核心。
- `docs/*/SOP.md` 仍是长期规范唯一源；`specs/037-*` 只记录本次变更流、任务与验收。
- 远端 `git push` 仍由用户执行；本波次只做本地实现、验证、审计与本地提交准备。
- 质量门槛必须包含真实运行证明：至少完成一次 host → subagent → tool/filesystem 的真实本地链路验证，不能只停留在静态 diff 或伪模型口头闭环。

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Maintainer registers a subagent through `ReActAgent` (Priority: P1)

As a maintainer, I want `ReActAgent.register_subagent(...)` to expose a
subagent as a toolkit tool, so delegation becomes a first-class core runtime
path instead of ad-hoc private glue.

**Why this priority**: 如果没有稳定的 host 注册入口，SubAgent V1 就不具备公共可用性。

**Independent Test**:

- 聚焦测试覆盖成功注册、输入校验失败、以及 fresh instance per call。

**Acceptance Scenarios**:

1. **Given** a `SubAgentBase` subclass and a `SubAgentSpec`, **When** I call
   `await host.register_subagent(...)`, **Then** the returned tool name is
   registered in the host toolkit and its schema is visible to the model.
2. **Given** invalid tool input, **When** the host invokes the subagent tool,
   **Then** the result is a wrapped `ToolResponse` with validation diagnostics
   instead of an import-time or runtime crash.
3. **Given** two delegations to the same registered subagent, **When** both
   calls finish, **Then** each call used a fresh subagent instance rather than
   reusing mutable in-memory state.

---

### User Story 2 - Subagent inherits host resources without privilege expansion (Priority: P1)

As a maintainer, I want SubAgent V1 to inherit only the host's existing model,
delegation context, filesystem policy, and a read-only memory snapshot, so the
delegated path is useful without silently widening capability boundaries.

**Why this priority**: 这是本波次最核心的边界要求；如果资源继承做错，后续 tracing 与安全口径都会被污染。

**Independent Test**:

- 聚焦测试覆盖 host model inheritance、filesystem policy inheritance、以及 host memory non-mutation。

**Acceptance Scenarios**:

1. **Given** a host with a `FileDomainService`, **When** a subagent is
   delegated, **Then** it can use the same granted filesystem scope but cannot
   write outside that existing policy.
2. **Given** a host memory history, **When** the host delegates to a
   subagent, **Then** the subagent receives a snapshot-style delegation
   context without mutating the host's stored messages.
3. **Given** no explicit override model, **When** the subagent is exported,
   **Then** it inherits the host model by default.

---

### User Story 3 - Maintainer gets one first-party generic task subagent (Priority: P1)

As a maintainer, I want one built-in generic task-execution subagent to ship
with V1, so the feature is proven by a real public example instead of just a
framework skeleton.

**Why this priority**: 用户明确要求“底座 + 一方样例子 agent”，否则 V1 只有框架感没有能力证明。

**Independent Test**:

- 聚焦测试覆盖公共导出、实际执行、以及通过工具/filesystem 完成任务。

**Acceptance Scenarios**:

1. **Given** a host agent with a filesystem toolset, **When** I register the
   built-in task subagent, **Then** it is available from `agentscope.agent`
   and can complete a delegated task through the normal ReAct tool loop.
2. **Given** the built-in task subagent uses filesystem tools, **When** it
   writes inside the allowed workspace, **Then** the host can observe the real
   artifact and the call returns a normal tool result payload.

---

### User Story 4 - Maintainer has an auditable proof chain for SubAgent V1 (Priority: P1)

As a maintainer, I want a repo-local proof entry and milestone audits, so the
wave can be accepted on real execution evidence rather than branch folklore.

**Why this priority**: 这个项目已经被“长线无产出”伤过，V1 必须把证据链写死。

**Independent Test**:

- 长线文档校验、focused pytest、真实 proof script、以及 milestone consistency audits。

**Acceptance Scenarios**:

1. **Given** the 037 worktree, **When** I run the focused SubAgent test suite,
   **Then** the core registration/inheritance/example tests all pass.
2. **Given** the repo-local proof script, **When** it runs with the local
   deterministic model and real filesystem workspace, **Then** it emits
   machine-readable evidence showing host → subagent → filesystem success.
3. **Given** each major milestone is complete, **When** a read-only audit
   subagent compares current output against the long-horizon docs, **Then** an
   audit report is written under `artifacts/consistency_audits/` and all
   differences are resolved before continuing.

## Edge Cases

- V1 明确不支持并行 subagent 调度；若 host 未来支持并行，这是后续波次范围。
- V1 允许 tracing 打最小元信息钩子，但不等待完整 tracing wave 落地。
- V1 不把 `SubAgent` 导出到顶层 `agentscope`，只进入 `agentscope.agent`。
- V1 的 memory 方向只做“读快照/上下文压缩输入”，不做共享可写 memory，也不引入 ReMe runtime 集成。
- easy 既有能力允许“可重塑”，不要求与历史实现逐行一致；只保留当前代码结构下仍然最合理的实现。

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: 本波次 MUST 创建 tracked `specs/037-subagent-v1-core/{spec,plan,tasks}.md`。
- **FR-002**: 本波次 MUST 在当前 `easy` 代码结构下新增 SubAgent V1 运行时，而不是整包拷贝旧 easy 文件状态。
- **FR-003**: `ReActAgent` MUST 提供 `register_subagent(...)` 作为主公共注册入口。
- **FR-004**: 每次 delegation MUST 构造新的 subagent 实例，不允许跨调用复用易变内存实例。
- **FR-005**: SubAgent V1 MUST 默认继承 host model；内建通用任务子 agent 还 MUST 继承 host formatter 以驱动内部 ReAct 执行。
- **FR-006**: 若 host 提供 `filesystem_service`，SubAgent V1 MUST 继承该 service 的既有策略，不得扩权，不得新建更宽的 grant。
- **FR-007**: SubAgent V1 MUST 只读取 host memory snapshot / delegation context，不得回写或篡改 host memory 中既有消息。
- **FR-008**: 本波次 MUST 交付一个第一方 generic task-execution subagent，并从 `agentscope.agent` 公共导出面暴露。
- **FR-009**: 本波次 MUST NOT 实现 subagent parallel dispatch、共享可写 memory、完整 tracing wave、TTS/audio、search/web、或顶层 `agentscope` 导出。
- **FR-010**: 每个 major block 结束后 MUST 发起一次 read-only consistency audit，并把报告写入 `artifacts/consistency_audits/`。
- **FR-011**: 本波次 MUST 提供一个 repo-local proof entry，真实执行 host → subagent → filesystem/tool 链路，并落盘机器可读证据 `artifacts/subagent_v1_runtime/proof.json`。
- **FR-012**: 本波次结束前 MUST 完成本地 focused tests、`pre-commit run --all-files`、长线文档 finalizer；但 MUST NOT `git push`。

## Include / Exclude Matrix

| Area | Decision | Notes |
| --- | --- | --- |
| `agent/_subagent_base.py`, `_subagent_tool.py` | include | SubAgent V1 core runtime |
| `agent/_react_agent.py` `register_subagent` | include | 主公共入口 |
| built-in generic task subagent | include | V1 必需样例 |
| `docs/agent/SOP.md`, `docs/filesystem/SOP.md`, `docs/tool/SOP.md` | include | 仅补齐长期规范真相 |
| minimal tracing metadata | include | 只做最小必要元信息 |
| parallel subagent dispatch | exclude | 明确不进 V1 |
| shared writable memory / ReMe runtime | exclude | 后续波次 |
| audio / TTS / realtime | exclude | 后续波次 |
| top-level `agentscope` export | exclude | 只在 `agentscope.agent` 暴露 |

## Historical Reference Inputs

- 历史参考实现来源：`033-mainline-m2-tracing-model-glue` 分支中的
  `src/agentscope/agent/_subagent_base.py`,
  `src/agentscope/agent/_subagent_tool.py`,
  以及 `tests/agent/test_subagent_*`。
- 这些历史文件只作为行为线索，不作为逐文件拷贝目标；当前 `easy`
  的代码形态、filesystem MVP、以及最新 SOP 口径优先。

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: `specs/037-subagent-v1-core/spec.md`,
  `specs/037-subagent-v1-core/plan.md`, and
  `specs/037-subagent-v1-core/tasks.md` all exist.
- **SC-002**: Focused SubAgent tests fail before implementation and pass after
  implementation.
- **SC-003**: `agentscope.agent` public exports include the built-in generic
  task subagent and exclude any new top-level `agentscope` export.
- **SC-004**: Filesystem inheritance tests prove “same policy, no privilege
  expansion”.
- **SC-005**: Host memory snapshot tests prove no host-message mutation during
  delegation.
- **SC-006**: `python3 ~/.codex/skills/long-horizon-runner/scripts/validate_long_horizon_docs.py --target .`
  passes after each milestone.
- **SC-007**: `artifacts/consistency_audits/` contains one audit report per
  completed major block and each report resolves to zero outstanding drift.
- **SC-008**: The repo-local proof entry succeeds and emits machine-readable
  evidence for a real host → subagent → filesystem/tool run at
  `artifacts/subagent_v1_runtime/proof.json`.
