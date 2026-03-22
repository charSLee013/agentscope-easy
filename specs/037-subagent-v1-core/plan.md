# Implementation Plan: Rebuild SubAgent V1 core on the new `easy` trunk

**Branch**: `037-subagent-v1-core` | **Date**: 2026-03-22 | **Spec**: `specs/037-subagent-v1-core/spec.md`
**Input**: Feature specification from `specs/037-subagent-v1-core/spec.md`

## Summary

本波次把历史 easy 中仍有价值的 SubAgent 能力，以当前 `easy` 的
runtime 结构重新实现为一个最小可用的 `V1`：

- `ReActAgent.register_subagent(...)` 作为公共入口
- host model / formatter / delegation context / filesystem 的最小继承
- per-call fresh instance
- read-only memory snapshot
- 一个第一方 generic task subagent
- 一条真实 proof chain

## Technical Context

**Language/Version**: Python 3.10+
**Primary Dependencies**: current repo `.venv`, current `pydantic`, `pytest`, `pre-commit`
**Testing**: targeted `pytest -p no:capture`, then `pre-commit run --all-files`
**Target Platform**: local macOS worktree
**Project Type**: Python library repo with ignored local `.codex` and `artifacts/`

## Scope

In scope:

- Create `specs/037-subagent-v1-core/{spec,plan,tasks}.md`
- Create and maintain `.codex/long-horizon/*` for this wave
- Add SubAgent V1 runtime files
- Add `ReActAgent.register_subagent(...)`
- Add built-in generic task subagent exposed from `agentscope.agent`
- Add/update minimal SOP truth for agent/filesystem/tool
- Add focused tests for registration, inheritance, fresh-instance lifecycle,
  built-in example, and proof helpers
- Add one repo-local real proof entry and milestone consistency audits

Out of scope:

- parallel subagent dispatch
- shared writable memory / ReMe runtime integration
- full tracing migration
- realtime / TTS / audio
- top-level `agentscope` export
- `git push`

## Milestones

### M1 - Freeze wave docs and audit contract

- 目标：创建 037 的 `.codex/long-horizon/*` 与 `specs/037-*`，把已冻结决策写死，并明确 audit 证据链要求。
- 验收标准：
  - `.codex/long-horizon/{Prompt,Plan,Implement,Documentation}.md` 全部存在且无模板占位
  - `specs/037-subagent-v1-core/{spec,plan,tasks}.md` 全部存在
  - audit artifact 目录与命名规则被记录到文档
- 验证命令：
  - `python3 ~/.codex/skills/long-horizon-runner/scripts/validate_long_horizon_docs.py --target .`
- 风险：
  - 规格写得过宽会重新落回“战线拉长、没有交付”
  - 若不把审计要求写死，后续容易只做代码不做对账

### M2 - Core runtime block

- 目标：用 fail-first tests 驱动 SubAgent V1 运行时底座落地，包括注册入口、fresh instance、inheritance、memory snapshot。
- 验收标准：
  - 核心测试先红后绿
  - `ReActAgent.register_subagent(...)` 可注册并执行 subagent tool
  - filesystem 继承与 no privilege expansion 被测试写死
  - 产出通过一次 read-only consistency audit
- 验证命令：
  - `PYTHONPATH=src /Users/charslee/Repo/private/agentscope-easy/.venv/bin/pytest -p no:capture tests/agent/test_subagent_tool.py tests/agent/test_subagent_lifecycle.py tests/agent/test_subagent_model_inheritance.py tests/agent/test_subagent_memory_snapshot.py tests/agent/test_subagent_filesystem_inheritance.py -q`
  - `python3 ~/.codex/skills/long-horizon-runner/scripts/validate_long_horizon_docs.py --target .`
- 风险：
  - 容易把旧 easy 的并行/共享 memory 逻辑一起带回
  - 容易误改 host memory 以“标注 delegation metadata”

### M3 - Built-in example and proof block

- 目标：交付第一方 generic task subagent、最小 SOP 更新、真实 proof script 与第二次审计。
- 验收标准：
  - built-in task subagent 从 `agentscope.agent` 可导入
  - host → subagent → filesystem/tool proof script 成功
  - `artifacts/subagent_v1_runtime/proof.json` 落盘
  - SOP truth 与实现一致
  - 审计报告确认无计划外噪声
- 验证命令：
  - `PYTHONPATH=src /Users/charslee/Repo/private/agentscope-easy/.venv/bin/pytest -p no:capture tests/agent/test_subagent_builtin_task_agent.py -q`
  - `PYTHONPATH=src /Users/charslee/Repo/private/agentscope-easy/.venv/bin/python specs/037-subagent-v1-core/subagent_v1_runtime_validation.py`
  - `python3 ~/.codex/skills/long-horizon-runner/scripts/validate_long_horizon_docs.py --target .`
- 风险：
  - built-in example 如果只是空壳，会失去“能力证明”意义
  - proof script 若只输出 exit code 而无机器可读证据，会回到伪闭环

### M4 - Final verification and proof loop

- 目标：跑 focused pytest、proof refresh、`pre-commit`、M4 final audit、finalizer，并准备本地提交。
- 验收标准：
  - focused tests 全绿
  - proof script 刷新成功且 `proof.json` 为当前运行结果
  - `pre-commit run --all-files` 全绿
  - `artifacts/consistency_audits/m4-final-verification-audit.md` 确认无计划外漂移
  - finalizer 成功并生成 `artifacts/final-manifest.json`
- 验证命令：
  - `PYTHONPATH=src /Users/charslee/Repo/private/agentscope-easy/.venv/bin/pytest -p no:capture tests/agent/test_subagent_tool.py tests/agent/test_subagent_lifecycle.py tests/agent/test_subagent_model_inheritance.py tests/agent/test_subagent_memory_snapshot.py tests/agent/test_subagent_filesystem_inheritance.py tests/agent/test_subagent_builtin_task_agent.py -q`
  - `PYTHONPATH=src /Users/charslee/Repo/private/agentscope-easy/.venv/bin/python specs/037-subagent-v1-core/subagent_v1_runtime_validation.py`
  - `/Users/charslee/Repo/private/agentscope-easy/.venv/bin/pre-commit run --all-files`
  - `python3 ~/.codex/skills/long-horizon-runner/scripts/finalize_long_horizon_run.py --target . --require-path specs/037-subagent-v1-core/spec.md --require-path specs/037-subagent-v1-core/plan.md --require-path specs/037-subagent-v1-core/tasks.md --require-path specs/037-subagent-v1-core/subagent_v1_runtime_validation.py --require-path artifacts/subagent_v1_runtime/proof.json --require-path artifacts/consistency_audits/m1-docs-audit.md --require-path artifacts/consistency_audits/m2-core-runtime-audit.md --require-path artifacts/consistency_audits/m3-example-proof-audit.md --require-path artifacts/consistency_audits/m4-final-verification-audit.md`
- 风险：
  - `pre-commit` 会改写文件，需要回写 tasks 完成态并重跑
  - finalizer 如果 require-path 列表不全，会产生“退出 0 但证据缺失”的假成功

## Verification

- Core runtime:
  - `PYTHONPATH=src /Users/charslee/Repo/private/agentscope-easy/.venv/bin/pytest -p no:capture tests/agent/test_subagent_tool.py tests/agent/test_subagent_lifecycle.py tests/agent/test_subagent_model_inheritance.py tests/agent/test_subagent_memory_snapshot.py tests/agent/test_subagent_filesystem_inheritance.py -q`
- Built-in example:
  - `PYTHONPATH=src /Users/charslee/Repo/private/agentscope-easy/.venv/bin/pytest -p no:capture tests/agent/test_subagent_builtin_task_agent.py -q`
  - `PYTHONPATH=src /Users/charslee/Repo/private/agentscope-easy/.venv/bin/python specs/037-subagent-v1-core/subagent_v1_runtime_validation.py`
- Final:
  - `PYTHONPATH=src /Users/charslee/Repo/private/agentscope-easy/.venv/bin/pytest -p no:capture tests/agent/test_subagent_tool.py tests/agent/test_subagent_lifecycle.py tests/agent/test_subagent_model_inheritance.py tests/agent/test_subagent_memory_snapshot.py tests/agent/test_subagent_filesystem_inheritance.py tests/agent/test_subagent_builtin_task_agent.py -q`
  - `PYTHONPATH=src /Users/charslee/Repo/private/agentscope-easy/.venv/bin/python specs/037-subagent-v1-core/subagent_v1_runtime_validation.py`
  - `/Users/charslee/Repo/private/agentscope-easy/.venv/bin/pre-commit run --all-files`
  - `python3 ~/.codex/skills/long-horizon-runner/scripts/finalize_long_horizon_run.py --target . ...`
