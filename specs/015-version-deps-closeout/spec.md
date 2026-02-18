# Feature Specification: Close out version/dependency L1 picks (08be504 + 7df0148 + 2984902)

**Feature Branch**: `015-version-deps-closeout`
**Base Branch**: `easy` (do not use `main/master` as mainline)
**Created**: 2026-02-17
**Status**: Draft
**Input**: User description: "低风险依赖版控批次，遵循 specs 方式继续推进"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Maintainers avoid duplicate dependency/version changes (Priority: P1)

As a maintainer, I want to verify whether selected upstream version/dependency
commits are already reflected in easy, so we avoid redundant edits and reduce
merge noise.

**Why this priority**: Duplicate dependency churn creates unnecessary risk and
review overhead with little value.

**Independent Test**: Evidence confirms whether each target commit is already
absorbed or superseded, with no runtime code diff required.

**Acceptance Scenarios**:

1. **Given** target commits `7df0148` and `2984902`, **When** dependency config
   is inspected, **Then** equivalent constraints are already present in
   `pyproject.toml`.
2. **Given** target commit `08be504`, **When** current version is compared,
   **Then** easy's version is newer and no downgrade is applied.

---

### User Story 2 - specs traceability is preserved for no-op closure (Priority: P2)

As a maintainer, I want a complete `spec -> plan -> tasks` trail even when no
source change is needed, so future batching decisions remain auditable.

**Why this priority**: Process consistency is required for long-running
absorption work.

**Independent Test**: `specs/015-version-deps-closeout/*` contains complete
artifacts and explicit mapping from target commits to current easy state.

**Acceptance Scenarios**:

1. **Given** the 015 branch diff, **When** compared with easy,
   **Then** only `specs/015-version-deps-closeout/*` files differ.
2. **Given** review of `research.md`, **When** checking each target commit,
   **Then** the status is clearly marked as absorbed or superseded.

### Edge Cases

- A target version bump is older than current easy version and must be skipped
  to prevent downgrade.
- Dependency constraints appear in multiple optional dependency groups and must
  be consistently checked.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The feature MUST evaluate commits `08be504`, `7df0148`, and
  `2984902` against current easy state before any code changes.
- **FR-002**: The feature MUST avoid applying lower-version updates when easy
  already has a higher version.
- **FR-003**: The feature MUST record per-commit evidence and status
  (absorbed/superseded) in `research.md`.
- **FR-004**: The feature MUST complete full speckit artifacts under
  `specs/015-version-deps-closeout/`.

### Key Entities *(include if feature involves data)*

- **Target Commit**: Upstream commit selected for this batch.
- **Status Decision**: Per-commit outcome (`already-absorbed`, `superseded`).
- **Evidence Record**: File/line and history proof linking decision to repo
  state.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: `pre-commit run --all-files` passes.
- **SC-002**: `git diff --name-only easy...HEAD` contains only
  `specs/015-version-deps-closeout/*`.
- **SC-003**: All three target commits have explicit evidence and decision
  entries in `research.md`.
