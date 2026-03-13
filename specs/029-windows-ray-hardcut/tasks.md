# Tasks: 029 Windows RayEvaluator hard cut

**Input**: `specs/029-windows-ray-hardcut/spec.md`, `specs/029-windows-ray-hardcut/plan.md`

## Phase 1: Runtime Guard

- [x] T001 Add native-Windows guard to `RayEvaluator`
- [x] T002 Preserve existing missing-Ray import guidance on supported platforms

## Phase 2: Tests and Docs

- [x] T003 Update Windows skip wording in `tests/evaluation_test.py`
- [x] T004 Add targeted runtime-guard coverage for native Windows
- [x] T005 Update evaluation tutorial docs
- [x] T006 Update `docs/evaluate/SOP.md`

## Phase 3: Validation

- [x] T007 Run targeted evaluation tests
- [x] T008 Run `pre-commit run --all-files`
