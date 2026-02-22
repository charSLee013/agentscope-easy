# Tasks: 021 agent runtime closeout

**Input**: `specs/021-agent-runtime-closeout/spec.md`, `specs/021-agent-runtime-closeout/plan.md`

## Phase 1: Setup

- [x] T001 Create branch `021-agent-runtime-closeout`
- [x] T002 Initialize specs skeleton via `.specify`

## Phase 2: Absorb Runtime Lane

- [x] T003 Attempt `34a8a300` (docs conflicts resolved with easy-first rule)
- [x] T004 Attempt `7f83c1ed`
- [x] T005 Attempt `f4c6b6f0` (resolve `_react_agent.py` overlap)
- [x] T006 Attempt `5a247979`
- [x] T007 Attempt `df968057` (empty-skipped)
- [x] T008 Attempt `dd05db2f` (empty-skipped after conflict-safe resolution)
- [x] T009 Attempt `28547e7c` (resolve `__init__.py` with easy-first rule)
- [x] T010 Attempt `1c9d88b9`

## Phase 3: Validation

- [x] T011 Run `pre-commit run --all-files` (pass 1)
- [x] T012 Run `pre-commit run --all-files` (pass 2 clean)
- [x] T013 Run `./.venv/bin/python -m ruff check src tests`
- [x] T014 Run `./.venv/bin/python -m pylint -E src`
- [x] T015 Run targeted runtime tests and capture results

## Phase 4: Docs Closeout

- [x] T016 Fill `spec.md`
- [x] T017 Add `plan.md`, `research.md`, `data-model.md`, `quickstart.md`
- [x] T018 Add `contracts/README.md` and requirements checklist
- [x] T019 Update checklist with final verification evidence

## Validation Evidence

- `pre-commit run --all-files` (pass 1): all hooks passed.
- `pre-commit run --all-files` (pass 2): all hooks passed; clean rerun.
- `./.venv/bin/python -m ruff check src tests`: passed.
- `./.venv/bin/python -m pylint -E src`: passed.
- Runtime tests:
  - `./.venv/bin/python -m unittest tests.react_agent_test tests.pipeline_test tests.hook_test -v` -> 19 passed.
  - `./.venv/bin/python -m unittest tests.model_openai_test tests.model_dashscope_test tests.model_anthropic_test tests.model_gemini_test -v` -> 34 passed.
  - `./.venv/bin/python -m unittest tests.evaluation_test -v` -> 2 passed.
  - Note: local `pytest` known issue (`exit -1` without output) observed; used documented unittest fallback.
