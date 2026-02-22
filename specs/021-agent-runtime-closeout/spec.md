# Feature Specification: Agent runtime closeout batch

**Feature Branch**: `021-agent-runtime-closeout`
**Base Branch**: `easy`
**Created**: 2026-02-22
**Status**: Draft
**Input**: User description: "agent runtime 同类修复找齐后一次合并，减少反复扯皮"

## User Scenarios & Testing

### User Story 1 - Absorb agent runtime fixes in one batch (Priority: P1)

As a maintainer, I want to absorb all same-lane runtime fixes together so we
avoid repeated branch churn and reduce review/merge overhead.

**Why this priority**: This directly improves throughput while keeping risk
bounded to the same module lane.

**Independent Test**: Process all selected commits with explicit status
(`applied` or `empty-skipped`) and no unresolved conflicts.

**Acceptance Scenarios**:

1. **Given** selected runtime commits, **When** ordered cherry-pick runs,
   **Then** each commit outcome is recorded and branch is conflict-free.
2. **Given** overlapping changes in `_react_agent.py`, **When** conflicts are
   resolved, **Then** runtime fix semantics are preserved without importing
   unrelated refactor behavior.

---

### User Story 2 - Stabilize tool choice and interruption behavior (Priority: P1)

As a maintainer, I want deterministic tool-choice handling and interruption
path fixes so runtime behavior is predictable under structured output and
cancel scenarios.

**Why this priority**: These are user-visible runtime reliability paths.

**Independent Test**: Run ReActAgent and model tests covering tool-choice,
interrupt handling, and deep research example flow.

**Acceptance Scenarios**:

1. **Given** structured output is required, **When** agent reasons,
   **Then** tool-choice constraints are applied correctly.
2. **Given** interruption during tool execution, **When** cancellation happens,
   **Then** cancellation path and follow-up behavior remain consistent.

### Edge Cases

- Some commits in this lane are empty-equivalent on current baseline and should
  be skipped without forcing changes.
- `__init__.py` may conflict due old upstream package layout; must preserve
  easy lazy-import structure.
- `_react_agent.py` conflict chunks may mix fix and refactor contexts; only fix
  intent should be merged.

## Requirements

### Functional Requirements

- **FR-001**: Attempt and record all selected agent runtime commits in one batch.
- **FR-002**: Preserve easy architecture in `__init__.py` conflict resolution.
- **FR-003**: Preserve runtime fix intent in `_react_agent.py` conflict
  resolution without introducing unrelated refactor logic.
- **FR-004**: Keep deep research example fix included in this batch.
- **FR-005**: Pass local quality gates before handoff.

### Key Entities

- **BatchCommit**: selected commit plus outcome status.
- **ConflictRule**: predefined rule for hotspot files and merge strategy.
- **ValidationEvidence**: gate/test command outputs used for acceptance.

## Success Criteria

### Measurable Outcomes

- **SC-001**: Selected runtime lane commits are fully processed with zero unresolved conflicts.
- **SC-002**: `pre-commit` second run is clean.
- **SC-003**: `ruff` and `pylint -E` pass.
- **SC-004**: Targeted runtime tests pass (or documented fallback passes if local pytest issue occurs).
