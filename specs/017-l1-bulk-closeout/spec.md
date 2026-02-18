# Feature Specification: L1 bulk closeout absorption

**Feature Branch**: `017-l1-bulk-closeout`
**Base Branch**: `easy`
**Created**: 2026-02-18
**Status**: Draft
**Input**: User instruction to absorb as many low-risk upstream commits as possible in one batch and avoid repeated labor

## User Scenarios & Testing

### User Story 1 - Absorb low-risk docs/example fixes in one batch (Priority: P1)

As a maintainer, I want to absorb multiple low-risk upstream fixes in one branch,
so we reduce repeated branch/PR overhead while keeping easy stable.

**Independent Test**: Selected commits are absorbed without conflict and the
branch passes local quality gates before PR.

**Acceptance Scenarios**:

1. Given selected low-risk commits, when they are cherry-picked, then no manual
   conflict resolution is required.
2. Given the absorbed batch, when local validation runs, then pre-commit and
   static checks pass.

### User Story 2 - Keep high-conflict items deferred (Priority: P2)

As a maintainer, I want conflict-heavy items to be explicitly deferred, so this
batch ships quickly and safely.

**Independent Test**: Deferred commits are documented with reasons in specs.

## Requirements

### Functional Requirements

- **FR-001**: Absorb the following low-risk commits in this batch:
  - `9f7c410` tutorial conf refine
  - `b56c4dd` tutorial studio port fix
  - `c635281` browser-use example hotfix
  - `340510f` AlibabaCloud API MCP OAuth example
  - `5c3a770` msghub docstring typo fix
- **FR-002**: Do not include high-conflict or high-risk commits in this batch.
- **FR-003**: Keep runtime behavior unchanged except for targeted fixes/examples.
- **FR-004**: Record deferred items and rationale for the next batch.

### Edge Cases

- Pre-commit may auto-fix formatting on first run; second run must be clean.
- Local pytest may be unstable in this environment; fallback checks must be
  recorded when used.

## Success Criteria

- **SC-001**: All 5 selected commits are present on branch history.
- **SC-002**: `pre-commit run --all-files` passes on second run.
- **SC-003**: `ruff` and `pylint -E src` pass.
- **SC-004**: Deferred set is explicitly documented in `specs/017-*` docs.

## Assumptions

- Fast, low-conflict absorption is prioritized over maximum scope per batch.
- Conflict-heavy commits are intentionally delayed to save cycle time.
