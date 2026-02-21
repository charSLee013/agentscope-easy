# Tasks: L1 runtime point fixes

**Input**: `specs/018-l1-runtime-pointfixes/spec.md`, `specs/018-l1-runtime-pointfixes/plan.md`

## Phase 1: Setup

- [x] T001 Create branch `018-l1-runtime-pointfixes` from `easy`
- [x] T002 Confirm candidates with `git apply --check`

## Phase 2: Implement

- [x] T003 [US2] Cherry-pick `a2bf80e`
- [x] T004 [US1] Cherry-pick `224e8a3`
- [x] T005 [US1] Cherry-pick `9d4cefa`
- [x] T006 [US1] Restore `tests/token_huggingface_test.py` to avoid accidental coverage loss

## Phase 3: Verify

- [x] T007 Run `pre-commit run --all-files` (pass 1)
- [x] T008 Run `pre-commit run --all-files` (pass 2 clean)
- [x] T009 Run `./.venv/bin/python -m ruff check src tests`
- [x] T010 Run `./.venv/bin/python -m pylint -E src`
- [x] T011 Run focused runtime tests and record results (`pytest` exits -1 locally; fallback `python -m unittest tests.pipeline_test tests.react_agent_test tests.plan_test -v` passed: 19 tests)

## Phase 4: Closeout

- [x] T012 Update checklist evidence
