# Tasks: 027 worktree subagent megabatch closeout

**Input**: `specs/027-worktree-subagent-megabatch/spec.md`, `specs/027-worktree-subagent-megabatch/plan.md`

## Phase 1: Topology Setup

- [x] T001 Create integration branch `027-worktree-subagent-megabatch`
- [x] T002 Create lane worktrees and branches:
  - `027-lane-a-runtime-memory`
  - `027-lane-b-model-formatter`
  - `027-lane-c-rag-plan-reader`
  - `027-lane-d-docs-ci-compat`

## Phase 2: Parallel Lane Processing (Fan-out)

- [x] T003 Lane D cherry-pick batch and lane report commit
- [x] T004 Lane C cherry-pick batch and lane report commit
- [x] T005 Lane B cherry-pick batch and lane report commit
- [x] T006 Lane A cherry-pick batch and lane report commit
- [x] T007 Persist lane reports under `specs/027-worktree-subagent-megabatch/reports/`

## Phase 3: Ordered Integration (Fan-in)

- [x] T008 Merge lane D into integration
- [x] T009 Merge lane C into integration
- [x] T010 Merge lane B into integration
- [x] T011 Merge lane A into integration

## Phase 4: Validation

- [x] T012 Run `pre-commit run --all-files`
- [x] T013 Run `python -m ruff check src tests`
- [x] T014 Run targeted `pytest -p no:capture` suites (49 passed)
- [x] T015 Record validation evidence and environment caveats

## Phase 5: Specs Closeout

- [x] T016 Add `spec.md`, `plan.md`, `tasks.md`
- [x] T017 Add `research.md`, `data-model.md`, `quickstart.md`
- [x] T018 Add `contracts/README.md` and checklist
- [x] T019 Add `commit-allocation.csv` for deterministic lane ownership

## Validation Evidence

- `pre-commit run --all-files`: passed.
- `python -m ruff check src tests`: passed.
- `python -m pytest -p no:capture tests/plan_test.py tests/rag_reader_test.py tests/react_agent_test.py -q`: 12 passed.
- `python -m pytest -p no:capture tests/model_openai_test.py tests/model_gemini_test.py -q`: 17 passed.
- `python -m pytest -p no:capture tests/formatter_openai_test.py tests/formatter_gemini_test.py tests/formatter_ollama_test.py tests/formatter_dashscope_test.py -q`: 16 passed.
- `python -m pytest -p no:capture tests/init_import_test.py tests/model_dashscope_test.py tests/search/test_search_schema_contracts.py -q`: 16 passed.
- Local caveat: plain `python -m pytest ... -q` intermittently hits `exit 139`; fallback recorded.
