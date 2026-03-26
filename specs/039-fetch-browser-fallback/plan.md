# Implementation Plan: Browser-level fallback for official webpage fetching

**Branch**: `feature/fetch-browser-fallback` | **Date**: 2026-03-26 | **Spec**: `specs/039-fetch-browser-fallback/spec.md`
**Input**: Feature specification from `specs/039-fetch-browser-fallback/spec.md`

## Summary

本波次只围绕一个核心问题推进：当官方网页被 Cloudflare/JS challenge
拦截时，AgentScope 需要有一个第一方、可复用、可验证的浏览器级抓取兜底。

交付重点：

- `agentscope.browser` 公共子模块
- `Lightpanda-first` + `Playwright` 兜底的后端选择
- optional extra 的依赖边界
- `038` 真实回归与报告

## Technical Context

**Language/Version**: Python 3.10+
**Primary Dependencies**: current repo `.venv`, `requests`, `playwright`
**Testing**: targeted `pytest -p no:capture`, runtime validation scripts, `pre-commit`
**Target Platform**: local macOS worktree
**Project Type**: Python library repo with ignored local `.codex` and `artifacts/`

## Scope

In scope:

- Create `specs/039-fetch-browser-fallback/{spec,plan,tasks,report}.md`
- Create and maintain `.codex/long-horizon/*` for this wave
- Add `src/agentscope/browser/` public module
- Add browser optional extra and docs/SOP truth
- Add focused tests for challenge detection, runtime fallback, import safety,
  and toolkit wiring
- Update `038` field validation to use the public browser service
- Add runtime validation script and selection artifact
- Produce milestone consistency audits and final proof bundle

Out of scope:

- general BrowserAgent / automation workflow
- screenshots / clicks / forms / MCP browser orchestration
- PDF or whitelist workaround
- pushing to GitHub

## Milestones

### M1 - Freeze docs and audit contract

- 目标：冻结范围、非目标、安装边界、以及 M1-M4 的证据链要求。
- 验收标准：
  - `.codex/long-horizon/*` 无模板占位
  - `specs/039-fetch-browser-fallback/{spec,plan,tasks}.md` 存在
  - `validate_long_horizon_docs.py` 通过
  - M1 docs audit 落盘
- 验证命令：
  - `python3 ~/.codex/skills/long-horizon-runner/scripts/validate_long_horizon_docs.py --target .`
- 风险：
  - 误把 scope 扩成通用浏览器代理
  - 未提前写死 optional extra 边界

### M2 - Selection experiment and fail-first tests

- 目标：完成 Lightpanda/Playwright 实测，并写出失败测试锁定契约。
- 验收标准：
  - `artifacts/tech_research/browser_fallback_selection.md` 落盘
  - 新增 `tests/browser/*`，先观察到失败
  - M2 audit 落盘
- 验证命令：
  - `PYTHONPATH=src /Users/charslee/Repo/private/agentscope-easy/.venv/bin/pytest -p no:capture tests/browser/test_service.py tests/browser/test_tools.py tests/browser/test_host_wiring.py -q`
  - `python3 ~/.codex/skills/long-horizon-runner/scripts/validate_long_horizon_docs.py --target .`
- 风险：
  - Lightpanda 在当前平台集成成本过高
  - 测试不够聚焦，误依赖真实浏览器环境

### M3 - Implement public browser capability and 038 wiring

- 目标：实现 `agentscope.browser`、更新 pyproject/docs，并完成 038 接线。
- 验收标准：
  - 公共导出明确，base import 安全
  - 缺依赖时只在使用路径报错
  - `038` 改为调用公共能力
  - M3 audit 落盘
- 验证命令：
  - `PYTHONPATH=src /Users/charslee/Repo/private/agentscope-easy/.venv/bin/pytest -p no:capture tests/browser/test_service.py tests/browser/test_tools.py tests/browser/test_host_wiring.py tests/init_import_test.py -q`
  - `python3 ~/.codex/skills/long-horizon-runner/scripts/validate_long_horizon_docs.py --target .`
- 风险：
  - 可选依赖处理不当，引入 import-time 炸点
  - 038 改造时顺手破坏原有验证链

### M4 - Real runtime validation and closeout

- 目标：做真实浏览器抓取验证、刷新报告、跑 pre-commit/finalizer，并准备本地提交。
- 验收标准：
  - `specs/039-fetch-browser-fallback/browser_runtime_validation.py` 成功
  - `specs/038-subagent-v1-field-validation/run_field_validation.py` 回归通过
  - `pre-commit run --all-files` 全绿
  - `artifacts/final-manifest.json` 存在
- 验证命令：
  - `PYTHONPATH=src /Users/charslee/Repo/private/agentscope-easy/.venv/bin/python specs/039-fetch-browser-fallback/browser_runtime_validation.py`
  - `PYTHONPATH=src /Users/charslee/Repo/private/agentscope-easy/.venv/bin/python specs/038-subagent-v1-field-validation/run_field_validation.py`
  - `/Users/charslee/Repo/private/agentscope-easy/.venv/bin/pre-commit run --all-files`
  - `python3 ~/.codex/skills/long-horizon-runner/scripts/finalize_long_horizon_run.py --target . --require-path specs/039-fetch-browser-fallback/spec.md --require-path specs/039-fetch-browser-fallback/plan.md --require-path specs/039-fetch-browser-fallback/tasks.md --require-path specs/039-fetch-browser-fallback/report.md --require-path specs/039-fetch-browser-fallback/browser_runtime_validation.py --require-path artifacts/tech_research/browser_fallback_selection.md --require-path artifacts/browser_runtime_validation/summary.json --require-path artifacts/consistency_audits/m1-docs-audit.md --require-path artifacts/consistency_audits/m2-selection-audit.md --require-path artifacts/consistency_audits/m3-implementation-audit.md --require-path artifacts/consistency_audits/m4-final-audit.md`
- 风险：
  - 真实浏览器环境初始化较慢，验证脚本波动
  - pre-commit 改写文件后若不回填任务态会造成 closeout 漂移

## Verification

- Docs:
  - `python3 ~/.codex/skills/long-horizon-runner/scripts/validate_long_horizon_docs.py --target .`
- Focused tests:
  - `PYTHONPATH=src /Users/charslee/Repo/private/agentscope-easy/.venv/bin/pytest -p no:capture tests/browser/test_service.py tests/browser/test_tools.py tests/browser/test_host_wiring.py -q`
- Runtime:
  - `PYTHONPATH=src /Users/charslee/Repo/private/agentscope-easy/.venv/bin/python specs/039-fetch-browser-fallback/browser_runtime_validation.py`
  - `PYTHONPATH=src /Users/charslee/Repo/private/agentscope-easy/.venv/bin/python specs/038-subagent-v1-field-validation/run_field_validation.py`
- Final:
  - `/Users/charslee/Repo/private/agentscope-easy/.venv/bin/pre-commit run --all-files`
  - `python3 ~/.codex/skills/long-horizon-runner/scripts/finalize_long_horizon_run.py --target . ...`
