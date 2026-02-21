# Feature Specification: Absorb L1 runtime point fixes in one batch

**Feature Branch**: `018-l1-runtime-pointfixes`
**Base Branch**: `easy`
**Created**: 2026-02-20
**Status**: Draft
**Input**: Continue low-risk bulk absorption with minimum conflict and reduced branch overhead

## User Scenarios & Testing

### User Story 1 - Stabilize stream printing behavior (Priority: P1)

As a maintainer, I want stream printing to avoid incorrect or duplicated tool-use
output, so runtime console output matches real agent state.

**Independent Test**: Existing pipeline/react-agent checks pass and no regressions
are introduced in stream output flow.

### User Story 2 - Improve plan hook typing compatibility (Priority: P1)

As a maintainer, I want `plan_change_hook` typing to support awaitables, so async
hooks type-check and integrate correctly.

**Independent Test**: Plan-related tests and lint checks pass after typing update.

## Requirements

### Functional Requirements

- **FR-001**: Absorb `a2bf80e` (PlanNotebook hook typing update with awaitable support).
- **FR-002**: Absorb `224e8a3` and `9d4cefa` (stream printing related runtime fixes).
- **FR-003**: Preserve existing token test coverage; accidental deletion of
  `tests/token_huggingface_test.py` must be reverted.
- **FR-004**: Scope remains limited to target runtime/plan files and this specs batch.

### Edge Cases

- `msg_queue` references must not mutate unexpectedly during stream printing.
- Structured output path still returns final message correctly after stream path changes.

## Success Criteria

- **SC-001**: Three target commits are absorbed with no unresolved conflicts.
- **SC-002**: `pre-commit run --all-files` second pass is fully clean.
- **SC-003**: `ruff` and `pylint -E src` pass.
- **SC-004**: Focused runtime regressions checks pass.
