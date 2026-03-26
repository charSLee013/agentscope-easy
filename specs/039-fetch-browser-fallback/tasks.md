---

description: "Add browser-level fallback for official webpage fetching"

---

# Tasks: Browser-level fallback for official webpage fetching

**Input**: `specs/039-fetch-browser-fallback/spec.md`, `specs/039-fetch-browser-fallback/plan.md`
**Base Branch**: `easy`
**Branch**: `feature/fetch-browser-fallback`

## Constitution Gates (applies to all tasks)

- 本波次只解决“网页抓取被 challenge 拦截时的浏览器级兜底”，不扩展到完整 browser automation。
- 禁止 PDF/白名单/特定 URL 替换这类业务绕路 patch。
- 浏览器依赖必须保持 optional extra 边界，不得污染 base install。
- 每个 major block 结束后都要发起 read-only audit subagent，并把结果落盘到 `artifacts/consistency_audits/`。
- 不在看见失败测试之前写生产代码。
- 不执行 `git push`。

## Phase 1: Freeze wave docs (P1)

- [x] T001 完成 `.codex/long-horizon/{Prompt,Plan,Implement,Documentation}.md` 的 frozen 内容。
- [x] T002 创建 `specs/039-fetch-browser-fallback/{spec,plan,tasks}.md`。
- [x] T003 记录 Lightpanda-first / Playwright fallback / optional extra / no-whitelist 的冻结决策。
- [x] T004 运行 `validate_long_horizon_docs.py`。
- [x] T005 运行 M1 docs audit subagent 并写入 `artifacts/consistency_audits/m1-docs-audit.md`。

---

## Phase 2: Selection experiment and fail-first tests (P1)

- [x] T006 以真实网络完成 Lightpanda / Playwright 对比实验，并写入 `artifacts/tech_research/browser_fallback_selection.md`。
- [x] T007 新增 `tests/browser/*`，先覆盖 challenge 检测、fallback 触发、缺依赖报错、tool wiring。
- [x] T008 运行聚焦测试并观察预期失败。
- [x] T009 运行 M2 selection audit subagent 并写入 `artifacts/consistency_audits/m2-selection-audit.md`。

---

## Phase 3: Implement public browser capability (P1)

- [x] T010 实现 `src/agentscope/browser/` 公共模块与 tool/service 接线。
- [x] T011 更新 `pyproject.toml`、`docs/browser/SOP.md`、必要的公共导出与安装说明。
- [x] T012 把 `specs/038-subagent-v1-field-validation/run_field_validation.py` 改为调用公共能力。
- [x] T013 重跑聚焦测试直到全部通过。
- [x] T014 运行 M3 implementation audit subagent 并写入 `artifacts/consistency_audits/m3-implementation-audit.md`。

---

## Phase 4: Runtime validation and closeout (P1)

- [x] T015 完成 `specs/039-fetch-browser-fallback/browser_runtime_validation.py` 与 `specs/039-fetch-browser-fallback/report.md`。
- [x] T016 运行 039 真实验证与 038 回归验证，刷新 `artifacts/browser_runtime_validation/summary.json`。
- [x] T017 运行 `pre-commit run --all-files` 并修复格式/静态检查问题。
- [x] T018 运行 M4 final audit subagent 并写入 `artifacts/consistency_audits/m4-final-audit.md`。
- [x] T019 回填 `.codex/long-horizon/Documentation.md` 与本 tasks 完成态。
- [x] T020 运行 finalizer，生成 `artifacts/final-manifest.json`。
