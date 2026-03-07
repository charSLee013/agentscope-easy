# Feature Specification: Worktree subagent megabatch closeout

- **Feature Branch**: `027-worktree-subagent-megabatch`
- **Base Branch**: `easy`
- **Created**: 2026-02-28
- **Status**: Draft
**Input**: User description: "一次性并行吸收中低风险提交，减少重复劳动"

## User Scenarios & Testing

### User Story 1 - Parallelize batch absorption with isolated lanes (Priority: P1)

As a maintainer, I want multiple low-risk commit lanes to be processed in
parallel with independent worktrees so throughput increases and context-switch
cost drops.

**Why this priority**: This directly addresses repeated tiny-PR churn.

**Independent Test**: Each lane produces a deterministic report with commit
outcomes and validation evidence.

**Acceptance Scenarios**:

1. **Given** four lane branches, **When** each lane runs cherry-pick + checks,
   **Then** each lane emits `reports/lane-*.md` and `reports/lane-*.json`.
2. **Given** a commit already represented by easy baseline, **When** cherry-pick
   is attempted, **Then** it is skipped and recorded explicitly.

---

### User Story 2 - Main agent performs ordered fan-in safely (Priority: P1)

As a maintainer, I want a single integration branch to merge lane results in a
fixed order so cross-lane conflicts are controlled and review remains simple.

**Why this priority**: Ordered fan-in prevents integration chaos.

**Independent Test**: Integration branch contains four merge commits in fixed
order and passes shared validation gates.

**Acceptance Scenarios**:

1. **Given** completed lane branches, **When** fan-in starts, **Then** merges
   happen in order `D -> C -> B -> A`.
2. **Given** merged integration state, **When** quality gates run, **Then**
   pre-commit and ruff pass, and targeted pytest suites pass.

### Edge Cases

- Local environment has intermittent pytest capture-related segfault (`exit 139`).
- Some upstream commits are empty against easy baseline and must be skipped.
- Docs commits may partially overlap existing docs fixes and apply as empty.

## Requirements

### Functional Requirements

- **FR-001**: Create one integration branch and four lane branches using worktree.
- **FR-002**: Process selected low/medium-risk commits per lane with `-x`.
- **FR-003**: Record per-commit outcome (`applied` / `skipped-empty` / `skipped-safe`).
- **FR-004**: Merge lanes into integration branch in fixed order.
- **FR-005**: Run shared quality gates and record evidence.

### Key Entities

- **LaneCommitOutcome**: `sha`, `lane`, `status`, `reason`.
- **LaneReport**: validation results and conflict notes per lane.
- **IntegrationValidation**: combined gate outcomes after fan-in.

## Success Criteria

### Measurable Outcomes

- **SC-001**: Four lane reports generated and committed.
- **SC-002**: Integration fan-in completes with 4 merge commits in fixed order.
- **SC-003**: `pre-commit` and `ruff` pass on integration branch.
- **SC-004**: Targeted pytest suites pass on integration branch (49 tests in this run).
