---

description: "Close out version/dependency L1 picks with no-op evidence"

---

# Tasks: Close out version/dependency L1 picks

**Input**: `specs/015-version-deps-closeout/spec.md`, `specs/015-version-deps-closeout/plan.md`
**Base Branch**: `easy` (do not use `main/master` as mainline)
**Branch**: `015-version-deps-closeout`

## Constitution Gates (applies to all tasks)

- Do not downgrade package version.
- Keep branch specs-only if all targets are absorbed/superseded.

## Phase 1: Discovery

- [x] T001 Inspect target commits `08be504`, `7df0148`, `2984902` and touched files
- [x] T002 Verify current easy version and dependency constraints in `pyproject.toml`
- [x] T003 Classify each target as `already-absorbed` or `superseded`

## Phase 2: Documentation

- [x] T004 [US1] Write evidence mapping for all targets in `research.md`
- [x] T005 [US2] Generate complete speckit artifacts under `specs/015-version-deps-closeout/`
- [x] T006 [US2] Explicitly state no runtime code/API change in contracts/data-model

## Phase 3: Verification

- [x] T007 Verify branch diff is specs-only (`git diff --name-only easy...HEAD`)
- [x] T008 Run `pre-commit run --all-files`
- [x] T009 Commit docs-only closure batch
