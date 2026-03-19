# Tasks: 033 mainline M2 tracing/model glue merge

**Input**: `specs/033-mainline-m2-tracing-model-glue/spec.md`, `specs/033-mainline-m2-tracing-model-glue/plan.md`

## Phase 1: Setup

- [x] T001 Create branch `033-mainline-m2-tracing-model-glue`
- [x] T002 Initialize M2 change-river docs
- [x] T003 Update local long-horizon ledger to reflect the approved M2 scope

## Phase 2: Runtime Glue

- [x] T004 Add `ChatUsage.metadata` and `ToolUseBlock.raw_input`
- [x] T005 Absorb OpenAI Azure/reasoning/stream-tool-parsing changes
- [x] T006 Absorb DashScope headers/multimodality/stream-tool-parsing changes
- [x] T007 Absorb Anthropic and Gemini parsing compatibility fixes
- [x] T008 Align DashScope formatter empty-content behavior
- [x] T009 Update `docs/model/SOP.md` for the new model constructor surfaces

## Phase 3: Verification

- [x] T010 Add or update focused tests for M2 behavior
- [x] T011 Run long-horizon validator
- [x] T012 Run focused pytest
- [x] T013 Run `pre-commit run --all-files`
- [x] T014 Run `./.venv/bin/python -m ruff check src tests`
- [x] T015 Run `./.venv/bin/python -m pylint -E src`
