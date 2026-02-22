# Feature Specification: Toolkit L1 closeout

**Feature Branch**: `026-toolkit-l1-closeout`
**Base Branch**: `easy`
**Created**: 2026-02-23
**Status**: Draft
**Input**: User description: "工具链L1收口，继续批量吸收同类修复"

## User Scenarios & Testing

### User Story 1 - Close toolkit same-lane fixes in one batch (Priority: P1)

As a maintainer, I want to absorb toolkit L1 fixes together so we reduce
repeated branch churn and avoid reopening the same conflict area.

**Why this priority**: These fixes improve tool execution correctness with low
architecture risk.

**Independent Test**: Process both selected commits with explicit outcomes and
no unresolved conflicts.

**Acceptance Scenarios**:

1. **Given** selected toolkit commits, **When** processing finishes,
   **Then** each commit has a traceable final status.
2. **Given** the meta tool changes, **When** activating/deactivating groups,
   **Then** inactive tools become unavailable immediately.

---

### User Story 2 - Preserve compatibility while fixing behavior (Priority: P1)

As a maintainer, I want toolkit fixes without API contract breakage.

**Why this priority**: We need safety in easy baseline while removing known
runtime/tool-control errors.

**Independent Test**: Run toolkit-focused tests and standard quality gates.

**Acceptance Scenarios**:

1. **Given** nested model extension in tool schema,
   **When** schema is merged,
   **Then** `$defs` entries are merged safely and conflicts are detected.
2. **Given** a tool in inactive group,
   **When** called,
   **Then** toolkit returns `FunctionInactiveError` response.

### Edge Cases

- Upstream commit may contain unrelated file changes; only toolkit-scope fix
  semantics should be migrated.
- Existing tests may require expectation updates due corrected response text.

## Requirements

### Functional Requirements

- **FR-001**: Absorb `$defs` merge fix for extended tool schema.
- **FR-002**: Ensure inactive-group tool call is blocked with explicit error.
- **FR-003**: Ensure `reset_equipped_tools` resets to absolute group state.
- **FR-004**: Record per-commit status and conflict-resolution strategy.
- **FR-005**: Pass quality gates and toolkit-focused tests.

### Key Entities

- **BatchCommit**: selected commit and final status.
- **ConflictRule**: easy-first rule for non-toolkit file noise.
- **ValidationEvidence**: command results used for acceptance.

## Success Criteria

### Measurable Outcomes

- **SC-001**: Both selected commits are processed with explicit status records.
- **SC-002**: `pre-commit` second run clean.
- **SC-003**: `ruff` and `pylint -E` pass.
- **SC-004**: toolkit-focused tests pass.
