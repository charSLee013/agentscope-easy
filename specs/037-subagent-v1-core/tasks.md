---

description: "Rebuild SubAgent V1 core on the new easy trunk"

---

# Tasks: Rebuild SubAgent V1 core on the new `easy` trunk

**Input**: `specs/037-subagent-v1-core/spec.md`, `specs/037-subagent-v1-core/plan.md`
**Base Branch**: `easy`
**Branch**: `037-subagent-v1-core`

## Constitution Gates (applies to all tasks)

- 本波次不实现 parallel subagent dispatch、shared writable memory、full tracing wave、audio/TTS/realtime、search/web。
- `docs/*/SOP.md` 仍是长期规范唯一源；`specs/037-*` 不能越权成为规范裁决源。
- 每个 major block 结束后都要发起 read-only audit subagent，并把结果落盘到 `artifacts/consistency_audits/`。
- 不在看见失败测试之前写生产代码。
- 不执行 `git push`。

## Phase 1: Freeze wave docs (P1)

- [x] T001 Create `.codex/long-horizon/{Prompt,Plan,Implement,Documentation}.md` for this wave.
- [x] T002 Create `specs/037-subagent-v1-core/{spec,plan,tasks}.md`.
- [x] T003 Record the frozen V1 scope, non-goals, and audit contract.
- [x] T004 Validate long-horizon docs with `validate_long_horizon_docs.py`.
- [x] T005 Run a read-only docs audit subagent and write `artifacts/consistency_audits/m1-docs-audit.md`.

---

## Phase 2: Core runtime block (P1)

- [x] T006 Write fail-first tests for subagent registration, lifecycle, model inheritance, memory snapshot, and filesystem inheritance.
- [x] T007 Run the targeted SubAgent core tests and observe the intended failures.
- [x] T008 Implement the minimum SubAgent V1 runtime changes to make those tests pass.
- [x] T009 Re-run the targeted SubAgent core tests until green.
- [x] T010 Run a read-only core-runtime audit subagent and write `artifacts/consistency_audits/m2-core-runtime-audit.md`.

---

## Phase 3: Built-in example and proof (P1)

- [x] T011 Write fail-first tests for the built-in generic task subagent and proof helpers.
- [x] T012 Run those targeted tests and observe the intended failures.
- [x] T013 Implement the built-in generic task subagent, public export, SOP updates, and repo-local proof entry.
- [x] T014 Re-run the built-in example tests and the proof script until green.
- [x] T015 Run a read-only example/proof audit subagent and write `artifacts/consistency_audits/m3-example-proof-audit.md`.

---

## Phase 4: Final verification and closeout (P1)

- [x] T016 Refresh `Documentation.md` to the real M4 closeout state.
- [x] T017 Run the final focused SubAgent pytest bundle.
- [x] T018 Run `pre-commit run --all-files`.
- [x] T019 Run a read-only final audit subagent and write `artifacts/consistency_audits/m4-final-verification-audit.md`.
- [x] T020 Run the final proof loop with `finalize_long_horizon_run.py`.
