# Feature Specification: docs CI example hardcut

- **Feature Branch**: `028-docs-ci-example-hardcut`
- **Base Branch**: `easy`
- **Created**: 2026-03-09
- **Status**: Draft
**Input**: User description: "非 ruff / pytest 的真实外部示例不参与 CI/CD"

## User Scenarios & Testing

### User Story 1 - CI avoids real tutorial example execution (Priority: P1)

As a maintainer, I want CI to skip tutorial example execution so external API
keys and network availability do not control PR health.

**Why this priority**: This removes the largest remaining CI instability source.

**Independent Test**: When `CI=true`, tutorial Sphinx config selects no
gallery examples for execution.

**Acceptance Scenarios**:

1. **Given** a CI environment, **When** Sphinx loads tutorial config, **Then**
   `src/*.py` gallery examples are not selected for execution.
2. **Given** a local manual docs build, **When** Sphinx loads tutorial config,
   **Then** tutorial examples still use the existing execution pattern.

### Edge Cases

- CI providers may set `CI=1` or `CI=true`.
- Local developers may still want real example execution with valid secrets.
- No current GitHub workflow runs docs build, but config must stay safe if one
  is added later.

## Requirements

### Functional Requirements

- **FR-001**: Tutorial Sphinx configs must detect standard CI environment.
- **FR-002**: Tutorial gallery example execution must be disabled in CI only.
- **FR-003**: Local manual docs builds must preserve current example execution.
- **FR-004**: No tutorial example source file should require rewriting for this
  policy change.

### Key Entities

- **CiExecutionMode**: whether Sphinx is running under `CI`.
- **GallerySelectionPolicy**: filename matching rule used by tutorial gallery.

## Success Criteria

### Measurable Outcomes

- **SC-001**: Both tutorial Sphinx configs gate example selection on `CI`.
- **SC-002**: Existing CI workflows remain limited to lint/test/pre-commit.
- **SC-003**: Manual docs builds remain capable of real example execution.
