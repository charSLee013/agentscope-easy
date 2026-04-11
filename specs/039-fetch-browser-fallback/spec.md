# Feature Specification: Browser-level fallback for official webpage fetching

**Feature Branch**: `feature/fetch-browser-fallback`
**Base Branch**: `easy`
**Created**: 2026-03-26
**Status**: Draft
**Input**: User direction: "把 Cloudflare/JS challenge 导致的官方网页抓取失败，当成通用能力缺口来补齐；以新的 main/easy 形态交付第一方公共能力，不准用 PDF/白名单绕路。"

## Clarifications

- 本波次是 `039-fetch-browser-fallback`，属于新 trunk 上的 selective rebuild，
  目标是网页抓取鲁棒性，不是完整 browser agent。
- `specs/039-*` 是本波次变更流，不是长期规范源；长期稳定规则仍以
  `docs/*/SOP.md` 为准。
- `git push` 仍由用户执行；本波次只做本地实现、验证、审计和提交准备。
- 用户已明确接受 AGPL 组件作为可选能力落地，但要求清楚划定安装边界。
- 质量门槛必须包含真实浏览器抓取验证与 `038` 回归，而不只是 mock 测试。

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Framework user fetches an official webpage through a public API (Priority: P1)

As a framework user, I want a first-party public module to fetch webpage text
with browser fallback, so I can consume the capability as a library instead of
copying one-off scripts into my app.

**Why this priority**: 用户明确要求 direct public API；如果只修 `038`，
就没有可复用的公共价值。

**Independent Test**:

- 聚焦测试 `agentscope.browser` 的公共导出、基础抓取结果、challenge 检测与
  浏览器兜底触发条件。

**Acceptance Scenarios**:

1. **Given** a normal HTML page without challenge, **When** I call the public
   fetch service, **Then** it returns title / text using the fast HTTP path.
2. **Given** a response with Cloudflare challenge markers, **When** I call the
   same service, **Then** it escalates to a browser backend instead of failing
   immediately.
3. **Given** the browser runtime is unavailable, **When** fallback is required,
   **Then** it raises a readable error with installation guidance instead of an
   import-time crash.

---

### User Story 2 - Maintainer wires browser fetching into Toolkit safely (Priority: P1)

As a maintainer, I want thin tool wrappers over the browser service, so host or
subagent code can register the capability through normal Toolkit wiring.

**Why this priority**: 本轮不仅要提供库级 API，还要能服务 `038` 的真实 agent
链路回归；这里的 tool 面只保留最小 `038` 集成需要，不扩成完整 browser
automation surface。

**Independent Test**:

- 聚焦测试 tool schema、preset kwargs 绑定、ToolResponse 结构与 host wiring。

**Acceptance Scenarios**:

1. **Given** a browser fetch service, **When** its tool function is registered
   with `preset_kwargs={"service": service}`, **Then** the schema does not
   leak the bound `service` parameter.
2. **Given** a successful fetch, **When** the tool is invoked through
   `Toolkit`, **Then** it returns a normal `ToolResponse` text payload.
3. **Given** browser fallback is required but the runtime is missing,
   **When** the tool is invoked, **Then** the caller receives the readable
   dependency failure instead of a silent empty result.

---

### User Story 3 - 038 field validation can fetch the blocked OpenAI page (Priority: P1)

As a maintainer, I want the `038` field validation harness to use the new
public capability, so the real regression target is fixed at the root cause and
can be re-run later.

**Why this priority**: 这是本波次存在的直接原因；如果 038 不回归，就不算真的
修复。

**Independent Test**:

- 真实验证脚本 + `038` 回归脚本，使用真实网络与浏览器链路。

**Acceptance Scenarios**:

1. **Given** the OpenAI article URL that previously returned `403`,
   **When** the runtime validation script uses the new service, **Then** it
   obtains rendered HTML/text through a browser path.
2. **Given** the `038` field validation harness, **When** it is switched to
   the new capability, **Then** the OpenAI source fetch no longer relies on a
   PDF or whitelist workaround.

---

### User Story 4 - Maintainer has auditable selection evidence and closeout proof (Priority: P1)

As a maintainer, I want selection evidence, milestone audits, and a final proof
loop, so this wave lands on real evidence instead of another long-horizon diff
without closure.

**Why this priority**: 用户明确要求长线纪律、每个 major block 审计、以及真实
验证作为卡点。

**Independent Test**:

- 选型报告、每个里程碑的 consistency audit、focused pytest、真实运行脚本、
  pre-commit、finalizer。

**Acceptance Scenarios**:

1. **Given** M2 completes, **When** I inspect the selection artifact, **Then**
   it documents Lightpanda / Playwright real outcomes, not just opinions.
2. **Given** each major block completes, **When** a read-only audit subagent
   compares outputs with the frozen plan, **Then** a report is written under
   `artifacts/consistency_audits/` and drift is resolved before continuing.
3. **Given** the wave is finished, **When** `finalize_long_horizon_run.py`
   runs, **Then** it emits a manifest that includes the new spec/report/runtime
   evidence.

## Edge Cases

- HTML 抓取成功但正文极少时，不自动强制切浏览器；本波次只以 challenge /
  hard failure 为主要触发条件，避免过度设计。
- `Lightpanda` 可执行文件缺失时，不能让整个模块 import 失败；只在真正选择
  该后端或需要 fallback 时抛出清晰错误。
- `Playwright` Python 包已安装但浏览器二进制未安装时，应给出可操作提示。
- base install 允许 `agentscope.browser` 子模块存在，但浏览器依赖缺失时只能
  在“使用浏览器兜底”时失败。

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: 本波次 MUST 创建 tracked
  `specs/039-fetch-browser-fallback/{spec,plan,tasks,report}.md`。
- **FR-002**: 本波次 MUST 创建第一方公共子模块 `agentscope.browser`，
  采用 `service + tools + public exports` 结构。
- **FR-003**: 默认抓取路径 MUST 先走轻量 HTTP，不得默认全量走浏览器。
- **FR-004**: 当响应状态或正文命中 challenge 特征时，系统 MUST 尝试浏览器
  级 fallback。
- **FR-005**: 浏览器后端选择 MUST 以 `Lightpanda-first` 进行探测，并允许
  `Playwright` 作为稳定兜底。
- **FR-006**: 浏览器依赖 MUST 通过 optional extra 暴露；base install
  MUST 保持 `import agentscope` 安全。
- **FR-007**: 缺少浏览器依赖或运行时时，系统 MUST 抛出带安装提示的可读错误，
  而不是 import-time crash 或静默返回空结果。
- **FR-008**: 本波次 MUST 提供最小 tool function，以支持
  `Toolkit.register_tool_function(..., preset_kwargs={"service": service})`
  的接线方式；其范围仅用于 `038` 回归所需的公共能力集成。
- **FR-009**: `specs/038-subagent-v1-field-validation/run_field_validation.py`
  MUST 改为调用该公共能力，而不是继续保留内嵌 `urllib` 网页抓取逻辑。
- **FR-010**: 本波次 MUST NOT 引入 PDF/域名白名单绕路、完整 browser
  automation、MCP browser agent、截图、点击、表单等额外能力。
- **FR-011**: 每个 major block 结束后 MUST 运行 read-only audit subagent，
  并把报告写入 `artifacts/consistency_audits/`。
- **FR-012**: 本波次结束前 MUST 完成 focused tests、真实运行验证、
  `pre-commit run --all-files`、以及 finalizer；但 MUST NOT `git push`。

## Include / Exclude Matrix

| Area | Decision | Notes |
| --- | --- | --- |
| `src/agentscope/browser/*` | include | 第一方公共抓取能力 |
| `docs/browser/SOP.md` | include | 长期规范真相 |
| `pyproject.toml` browser extra | include | 明确安装边界 |
| `tests/browser/*` | include | 守住分层与 fallback 行为 |
| `specs/038-subagent-v1-field-validation/*` | include | 作为真实消费者回归 |
| top-level browser automation / BrowserAgent | exclude | 不进本波次 |
| domain whitelist / PDF substitution | exclude | 明确禁止 |
| browser dependency in base/full | exclude | 保持安装边界清晰 |

## Historical Reference Inputs

- 根因与回归目标来自 `specs/038-subagent-v1-field-validation/report.md`
  和其 `run_field_validation.py` 中的 `fetch_official_page()`。
- 公共能力形态参考 `src/agentscope/filesystem/` 的 service/tool/export 结构。
- 浏览器示例 `examples/agent/browser_agent/` 仅作为“仓库已有 browser 相关经验”
  参考，不直接升级为公共 API。

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: `specs/039-fetch-browser-fallback/spec.md`,
  `plan.md`, `tasks.md`, `report.md` 全部存在。
- **SC-002**: `tests/browser/*` 在实现前失败、实现后通过。
- **SC-003**: `agentscope.browser` 可导入且不把浏览器依赖强塞到 base import。
- **SC-004**: 选型报告明确记录 Lightpanda / Playwright 的真实结果与最终选择。
- **SC-005**: `038` 回归使用新公共能力，且 OpenAI HTML 不再靠 PDF/白名单绕路。
- **SC-006**: `python3 ~/.codex/skills/long-horizon-runner/scripts/validate_long_horizon_docs.py --target .`
  在每个里程碑后都通过。
- **SC-007**: `artifacts/consistency_audits/` 中存在本波次每个 major block 的
  audit 报告且最终 drift 归零。
- **SC-008**: 真实运行验证产物落盘到
  `artifacts/browser_runtime_validation/summary.json`。
