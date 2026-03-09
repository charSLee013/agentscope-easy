# Tasks: 028 docs CI example hardcut

**Input**: `specs/028-docs-ci-example-hardcut/spec.md`, `specs/028-docs-ci-example-hardcut/plan.md`

## Phase 1: Config Gating

- [x] T001 Patch `docs/tutorial/en/conf.py` for CI detection
- [x] T002 Patch `docs/tutorial/zh_CN/conf.py` for CI detection
- [x] T003 Disable gallery example matching only when `CI` is set

## Phase 2: Specs Closeout

- [x] T004 Add `spec.md`, `plan.md`, `tasks.md`
- [x] T005 Add `research.md`, `data-model.md`, `quickstart.md`
- [x] T006 Add contracts note and requirements checklist

## Phase 3: Validation

- [x] T007 Run `pre-commit run --all-files`
- [x] T008 Confirm no docs workflow executes tutorial examples
