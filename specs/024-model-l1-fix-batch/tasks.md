# Tasks: 024 model l1 fix batch

**Input**: `specs/024-model-l1-fix-batch/spec.md`, `specs/024-model-l1-fix-batch/plan.md`

## Phase 1: Setup

- [x] T001 Create branch `024-model-l1-fix-batch`
- [x] T002 Initialize specs skeleton

## Phase 2: Commit Processing

- [x] T003 Attempt `6bc219a` -> empty-skipped
- [x] T004 Attempt `3b67178` -> empty-skipped
- [x] T005 Attempt `44b6806` -> empty-skipped
- [x] T006 Record equivalent commit evidence from easy history

## Phase 3: Validation

- [x] T007 Run `pre-commit run --all-files` (pass 1)
- [x] T008 Run `pre-commit run --all-files` (pass 2 clean)
- [x] T009 Run `./.venv/bin/python -m ruff check src tests`
- [x] T010 Run `./.venv/bin/python -m pylint -E src`
- [x] T011 Run focused model/formatter/tool tests

## Phase 4: Docs Closeout

- [x] T012 Add `spec.md`, `plan.md`, `research.md`, `data-model.md`, `quickstart.md`
- [x] T013 Add `contracts/README.md` and quality checklist
- [x] T014 Update checklist and validation evidence

## Validation Evidence

- `pre-commit run --all-files` (pass 1): all hooks passed.
- `pre-commit run --all-files` (pass 2): all hooks passed; clean rerun.
- `./.venv/bin/python -m ruff check src tests`: passed.
- `./.venv/bin/python -m pylint -E src`: passed.
- `./.venv/bin/python -m unittest tests.model_openai_test tests.formatter_deepseek_test -v`: 9 passed.
- `./.venv/bin/python -m pytest -q tests/tool_openai_test.py tests/tool_dashscope_test.py`: local known pytest issue (`exit -1`, no output).
- `./.venv/bin/python -m unittest tests.tool_test -v`: 5 passed.
- `./.venv/bin/python -m unittest tests.toolkit_test -v`: 11 passed.
