# Feature Specification: Docs/example megabatch absorption

**Feature Branch**: `020-docs-example-megabatch`
**Base Branch**: `easy`
**Created**: 2026-02-21
**Status**: Draft
**Input**: User description: "020-l1-docs-example-closeout 批量提速，尽可能并全同类提交"

## User Scenarios & Testing

### User Story 1 - Bulk absorb docs/example lane in one shot (Priority: P1)

As a maintainer, I want to absorb a larger docs/example/ci/version batch in one
branch so upstream convergence speed is improved without repeated branch churn.

**Why this priority**: Directly addresses throughput bottleneck from overly
small batches.

**Independent Test**: Attempt all target commits in order and ensure each has
recorded status (`applied` or `empty-skipped`) with no unresolved conflicts.

**Acceptance Scenarios**:

1. **Given** 16 target commits, **When** ordered cherry-pick runs,
   **Then** each commit is either absorbed or skipped as empty with evidence.
2. **Given** repeated version-file conflicts, **When** conflict resolution is
   applied, **Then** final version remains `1.0.10` and no version rollback occurs.

---

### User Story 2 - Preserve easy-specific behavior during upstream sync (Priority: P1)

As a maintainer, I want conflicts to be resolved with `easy` architecture first
so upstream sync does not regress easy-specific docs/runtime behavior.

**Why this priority**: Prevents hidden technical debt from accidental rollback.

**Independent Test**: Confirm key conflict hotspots (`README*`,
`src/agentscope/_version.py`, werewolves prompts) keep expected easy semantics.

**Acceptance Scenarios**:

1. **Given** upstream README conflicts, **When** resolving, **Then** easy fork
   notices and structure are preserved.
2. **Given** werewolves prompt conflicts, **When** resolving, **Then** prompt
   behavior remains compatible and includes the one-line response fix.

### Edge Cases

- Commits that touched files removed in `easy` (e.g. reme/tts examples) may
  reintroduce files via conflict resolution.
- Older upstream README rewrites may conflict with customized `easy` README
  layout and TOC.
- Version bumps across multiple commits may become empty or conflict repeatedly.

## Requirements

### Functional Requirements

- **FR-001**: Absorb the 16 selected docs/example/ci/version commits in one
  branch with ordered cherry-pick.
- **FR-002**: Record per-commit outcome (`applied` or `empty-skipped`) in
  tasks/checklist artifacts.
- **FR-003**: Preserve easy-specific behavior where upstream conflicts attempt
  full-file rollback.
- **FR-004**: Keep final `src/agentscope/_version.py` at `1.0.10`.
- **FR-005**: Run complete local quality gates before handoff.

### Key Entities

- **BatchCommit**: one target SHA plus outcome and conflict notes.
- **ConflictResolutionRule**: fixed strategy for README/version/prompt hotspots.
- **ValidationEvidence**: command outcomes from pre-commit, lint, and tests.

## Success Criteria

### Measurable Outcomes

- **SC-001**: All 16 target commits are processed with zero unresolved conflicts.
- **SC-002**: Local gates pass: pre-commit (two runs), ruff, pylint.
- **SC-003**: No version rollback; final version string remains `1.0.10`.
- **SC-004**: Specs package for `020` is complete and auditable.
