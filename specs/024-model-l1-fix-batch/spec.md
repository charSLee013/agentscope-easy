# Feature Specification: Model L1 fix batch

**Feature Branch**: `024-model-l1-fix-batch`
**Base Branch**: `easy`
**Created**: 2026-02-22
**Status**: Draft
**Input**: User description: "模型L1修复聚合，一次吸收同类点修"

## User Scenarios & Testing

### User Story 1 - Batch-handle model L1 fixes (Priority: P1)

As a maintainer, I want to process model-layer L1 fixes in one batch so we can
remove repeated back-and-forth merges.

**Why this priority**: These fixes directly improve model robustness with
limited architectural risk.

**Independent Test**: Every selected commit is attempted and assigned explicit
status (`applied`, `empty-skipped`, `conflict-safe-skipped`).

**Acceptance Scenarios**:

1. **Given** selected model L1 commits, **When** cherry-picks are attempted,
   **Then** each outcome is recorded with rationale.
2. **Given** equivalent fixes already exist in easy, **When** commit is
   attempted, **Then** it is empty-skipped and traceably documented.

---

### User Story 2 - Keep baseline stable and verifiable (Priority: P1)

As a maintainer, I want this batch to remain API-neutral and pass all local
quality gates before PR.

**Why this priority**: Prevent regressions and CI-only rework.

**Independent Test**: Run double pre-commit, lint checks, and focused tests.

**Acceptance Scenarios**:

1. **Given** no net code deltas are required, **When** quality gates run,
   **Then** all checks pass cleanly.
2. **Given** focused formatter/model suites, **When** tests run,
   **Then** all targeted tests pass.

### Edge Cases

- Cherry-picks can be empty if equivalent patches already landed under
different commit hashes.
- "No-op batch" still needs full evidence to avoid future duplicate effort.

## Requirements

### Functional Requirements

- **FR-001**: Attempt and classify the selected model L1 commits in one batch.
- **FR-002**: Keep easy behavior unchanged when commits are already equivalent.
- **FR-003**: Document per-commit status and validation evidence.
- **FR-004**: Complete local verification gates before handoff.

### Key Entities

- **BatchCommit**: hash + title + status + rationale.
- **ValidationEvidence**: command + result + notes.

## Success Criteria

### Measurable Outcomes

- **SC-001**: All selected commits are processed with explicit outcomes.
- **SC-002**: `pre-commit` second run is clean.
- **SC-003**: `ruff` and `pylint -E` pass.
- **SC-004**: Focused model/formatter tests pass.
