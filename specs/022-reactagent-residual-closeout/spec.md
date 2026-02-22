# Feature Specification: ReactAgent residual closeout batch

**Feature Branch**: `022-reactagent-residual-closeout`
**Base Branch**: `easy`
**Created**: 2026-02-22
**Status**: Draft
**Input**: User description: "继续低风险快收口，尽可能同类一次处理"

## User Scenarios & Testing

### User Story 1 - Batch-handle residual ReactAgent fixes (Priority: P1)

As a maintainer, I want to process the remaining ReactAgent same-lane commits
in one branch so we avoid repeated tiny PR cycles.

**Why this priority**: This directly reduces merge churn on the hottest runtime
path while preserving easy stability.

**Independent Test**: Attempt each selected commit and record exact outcome
(`applied` / `empty-skipped` / `conflict-safe-skipped`).

**Acceptance Scenarios**:

1. **Given** selected ReactAgent residual commits, **When** they are attempted
   in order, **Then** each commit has an explicit status and rationale.
2. **Given** conflict against easy-only architecture, **When** conflict appears,
   **Then** we keep easy behavior and skip risky structural import.

---

### User Story 2 - Keep runtime behavior stable (Priority: P1)

As a maintainer, I want no regression in ReActAgent runtime behavior after this
closeout branch.

**Why this priority**: `_react_agent.py` is high-impact and regression-prone.

**Independent Test**: Run lint/quality gates and focused runtime tests.

**Acceptance Scenarios**:

1. **Given** current easy baseline, **When** closeout is complete,
   **Then** pre-commit second run is clean.
2. **Given** focused ReActAgent + plan tests, **When** test suite runs,
   **Then** all targeted tests pass.

### Edge Cases

- A target commit may already be semantically present under another hash.
- A target commit may conflict because upstream context contains older
  structured-output branch logic no longer used by easy.
- Empty cherry-pick results must be explicitly recorded, not silently ignored.

## Requirements

### Functional Requirements

- **FR-001**: Process selected residual commit set in one batch.
- **FR-002**: Preserve easy-first behavior in `_react_agent.py` conflict cases.
- **FR-003**: Record per-commit outcome and skip reason in specs artifacts.
- **FR-004**: Pass local quality gates before handoff.

### Key Entities

- **BatchCommit**: commit hash, type, status, and rationale.
- **ConflictRule**: easy-first merge constraints for hotspot files.
- **ValidationEvidence**: local command outputs used for acceptance.

## Success Criteria

### Measurable Outcomes

- **SC-001**: All selected commits are processed with explicit outcome records.
- **SC-002**: `pre-commit run --all-files` second run is clean.
- **SC-003**: `ruff` and `pylint -E` pass.
- **SC-004**: Focused runtime tests pass.
