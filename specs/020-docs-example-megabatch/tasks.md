# Tasks: 020 docs/example megabatch

**Input**: `specs/020-docs-example-megabatch/spec.md`, `specs/020-docs-example-megabatch/plan.md`

## Phase 1: Setup

- [x] T001 Create branch `020-docs-example-megabatch` from `easy`
- [x] T002 Initialize feature skeleton via `.specify` script

## Phase 2: Bulk Absorption

- [x] T003 Attempt `c2c59e56`
- [x] T004 Attempt `073d16d3` (resolve README conflict using easy-first rule)
- [x] T005 Attempt `3ca85617` (resolve README conflict)
- [x] T006 Attempt `654921ff` (resolve README conflict)
- [x] T007 Attempt `6c25ef07` (resolve README conflict)
- [x] T008 Attempt `a1e681a6`
- [x] T009 Attempt `0864a8df` (map prompt fix to active file)
- [x] T010 Attempt `fd1335fc`
- [x] T011 Attempt `fa85f38a` (keep version stable)
- [x] T012 Attempt `cb352877` (keep prompt/version architecture)
- [x] T013 Attempt `93938ee7`
- [x] T014 Attempt `c7b1ff0f`
- [x] T015 Attempt `2d3cbe74` (keep version stable)
- [x] T016 Attempt `81490c88`
- [x] T017 Attempt `08be504e` (empty-skipped)
- [x] T018 Attempt `2af34309` (empty-skipped)

## Phase 3: Validation

- [x] T019 Run `pre-commit run --all-files` (pass 1)
- [x] T020 Run `pre-commit run --all-files` (pass 2 clean)
- [x] T021 Run `./.venv/bin/python -m ruff check src tests`
- [x] T022 Run `./.venv/bin/python -m pylint -E src`
- [x] T023 Run targeted tests and record results

## Phase 3.5: Risk Correction

- [x] T023A Revert `2e3bd1e` and `a0ff269` due pylint hard-fail from reintroduced ReMe files

## Phase 4: Docs Closeout

- [x] T024 Fill `spec.md`
- [x] T025 Add `plan.md`, `research.md`, `data-model.md`, `quickstart.md`
- [x] T026 Add `contracts/README.md` and `checklists/requirements.md`
- [x] T027 Update checklist with validation evidence
