# Feature Specification: Windows RayEvaluator hard cut

**Feature Branch**: `029-windows-ray-hardcut`  
**Base Branch**: `easy` (do not use `main/master` as mainline)  
**Created**: 2026-03-10  
**Status**: Draft  
**Input**: User description: "明确放弃 Windows 原生 RayEvaluator 支持，统一测试文档和运行时口径"

## User Scenarios & Testing

### User Story 1 - Native Windows fails fast with clear guidance (Priority: P1)

As a maintainer, I want `RayEvaluator` to reject native Windows immediately so
CI and users do not hit unstable Ray startup behavior.

**Why this priority**: This is the remaining CI platform debt after the docs
example hard cut.

**Independent Test**: Instantiate `RayEvaluator` under a mocked Windows
platform and verify it raises a clear runtime error mentioning `WSL2`.

**Acceptance Scenarios**:

1. **Given** native Windows, **When** `RayEvaluator` is constructed,
   **Then** it raises a clear error that native Windows is unsupported.
2. **Given** Linux/macOS or WSL2, **When** `RayEvaluator` is constructed,
   **Then** existing behavior remains unchanged.

---

### User Story 2 - Tests reflect the real support contract (Priority: P1)

As a maintainer, I want evaluation tests to describe native Windows as
unsupported rather than merely flaky.

**Why this priority**: Test messaging must match the actual product boundary.

**Independent Test**: Run `tests/evaluation_test.py` and verify the Windows
skip path references unsupported native Windows rather than CI instability.

**Acceptance Scenarios**:

1. **Given** native Windows, **When** the Ray evaluator test is reached,
   **Then** it is skipped with an unsupported-platform reason.

---

### User Story 3 - Docs recommend WSL2 instead of implying support (Priority: P2)

As a developer, I want evaluation docs to say that Ray-based evaluation should
run on WSL2 or non-Windows platforms so setup expectations are unambiguous.

**Why this priority**: Docs currently imply broader platform support than we
actually want to maintain.

**Independent Test**: Read the evaluation SOP and tutorial pages and confirm
they state native Windows is unsupported for `RayEvaluator`.

**Acceptance Scenarios**:

1. **Given** a reader on Windows, **When** they open the evaluation docs,
   **Then** they see guidance to use WSL2 or Linux/macOS for `RayEvaluator`.

### Edge Cases

- WSL2 should not be blocked because it reports as Linux rather than Windows.
- `GeneralEvaluator` must remain available on native Windows.
- Missing `ray` installation must still raise the existing import guidance on
  supported platforms.

## Requirements

### Functional Requirements

- **FR-001**: `RayEvaluator` must reject native Windows before trying to start
  Ray workers.
- **FR-002**: The runtime error must explicitly recommend `WSL2` or
  Linux/macOS.
- **FR-003**: `tests/evaluation_test.py` must describe native Windows as an
  unsupported platform.
- **FR-004**: Evaluation docs must state native Windows is unsupported for
  `RayEvaluator`.
- **FR-005**: No behavior change is allowed for `GeneralEvaluator`.

### Key Entities

- **RayPlatformSupportPolicy**: the rule that native Windows is unsupported for
  `RayEvaluator`.
- **RayEvaluatorRuntimeGuard**: the runtime platform check performed before
  Ray-specific work begins.

## Success Criteria

### Measurable Outcomes

- **SC-001**: Native Windows construction of `RayEvaluator` fails fast with a
  stable, explicit error.
- **SC-002**: Evaluation tests and docs use the same unsupported-platform
  wording.
- **SC-003**: Targeted evaluation tests pass after the policy change.
