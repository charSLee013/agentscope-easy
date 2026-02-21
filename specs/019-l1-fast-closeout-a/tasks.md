# Tasks: L1 fast closeout A

**Input**: `specs/019-l1-fast-closeout-a/spec.md`, `specs/019-l1-fast-closeout-a/plan.md`

## Phase 1: Setup

- [x] T001 Create branch `019-l1-fast-closeout-a` from `easy`
- [x] T002 Initialize feature spec via `.specify` branch script

## Phase 2: Absorb Upstream Batch

- [x] T003 [US1] Attempt cherry-pick `62aa639` in order
- [x] T004 [US1] Attempt cherry-pick `6bc219a` in order
- [x] T005 [US1] Attempt cherry-pick `28547e7` in order
- [x] T006 [US1] Resolve conflicts conservatively and skip empty-equivalent commits

## Phase 3: Verification

- [x] T007 [US1] Run `pre-commit run --all-files` (pass 1)
- [x] T008 [US1] Run `pre-commit run --all-files` (pass 2 clean)
- [x] T009 [US1] Run `./.venv/bin/python -m ruff check src tests`
- [x] T010 [US1] Run `./.venv/bin/python -m pylint -E src`
- [x] T011 [US1] Run focused model tests and record outcome

## Phase 4: Documentation Closeout

- [x] T012 [US2] Fill `spec.md` with no-op absorption rationale
- [x] T013 [US2] Add `plan.md`, `research.md`, `data-model.md`, `quickstart.md`
- [x] T014 [US2] Add checklist and contracts notes under `specs/019-l1-fast-closeout-a`
- [x] T015 [US2] Update checklist with final gate results
