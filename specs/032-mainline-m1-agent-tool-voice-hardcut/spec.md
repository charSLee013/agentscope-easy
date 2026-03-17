# Feature Specification: Mainline M1 agent/tool/voice hard cut

**Feature Branch**: `032-mainline-m1-agent-tool-voice-hardcut`
**Base Branch**: `easy`
**Created**: 2026-03-17
**Status**: Implemented
**Input**: User description: "保持 easy 独立前提下吸收 main；agent/tool 深度合并，按 main 硬切；语音能力第一波并进；播放默认关闭。"

## User Scenarios & Testing

### User Story 1 - Switch agent/tool public surface to the new mainline direction (Priority: P1)

As a maintainer, I want `easy` to expose the current `main`-style
`agent/tool` surface so later upstream absorption is not blocked by the old
`SubAgent` and search/web export shape.

**Why this priority**: This is the architectural front door for later waves.

**Independent Test**: Import/export checks and focused runtime tests pass.

**Acceptance Scenarios**:

1. **Given** `agentscope.agent`, **When** public exports are inspected,
   **Then** `RealtimeAgent` is available and `SubAgent*` no longer defines
   the public surface.
2. **Given** `agentscope.tool`, **When** public exports are inspected,
   **Then** the surface matches the current `main` direction and does not
   expose the legacy search aggregation entrypoints.

### User Story 2 - Land voice/realtime capability in wave 1 without default playback (Priority: P1)

As a maintainer, I want wave 1 to include realtime and TTS capability so voice
support is not delayed behind later waves, while keeping playback safe by
default.

**Why this priority**: The user explicitly moved voice into the first wave.

**Independent Test**: Realtime/TTS imports work, focused tests pass, and audio
playback remains opt-in.

**Acceptance Scenarios**:

1. **Given** the realtime package, **When** importing `agentscope.realtime`,
   **Then** the realtime model/event surface is available.
2. **Given** audio output blocks, **When** runtime playback is not enabled,
   **Then** playback side effects do not occur.
3. **Given** existing TTS providers and playback gating,
   **When** inspecting the voice stack after the wave-1 port,
   **Then** current TTS behavior remains available without flipping playback
   defaults.

### User Story 3 - Keep easy runtime behavior stable while hard-cutting the surface (Priority: P1)

As a maintainer, I want the public API hard cut without regressing import
safety, runtime gating, or existing focused runtime behavior.

**Why this priority**: Hard-cutting the surface is acceptable, but regressions
in runtime safety are not.

**Independent Test**: Current import-safety and focused runtime checks still
pass after the surface switch.

**Acceptance Scenarios**:

1. **Given** `import agentscope`, **When** optional voice/a2a/realtime deps are
   absent from runtime use paths, **Then** the top-level import remains safe.
2. **Given** toolkit middleware and text-file path handling,
   **When** using the new wave-1 behavior, **Then** they work on `easy`
   without reviving removed legacy surface as public contract.

## Edge Cases

- `easy` still carries internal `SubAgent` implementation; hard cut only
  applies to the public surface in this wave.
- New voice features must not flip `audio_playback_enabled` default behavior.
- Realtime dependencies may be moved into core dependencies; tests must verify
  imports and runtime shims, not only packaging metadata.

## Requirements

### Functional Requirements

- **FR-001**: `agentscope.agent` MUST expose `RealtimeAgent` in wave 1.
- **FR-002**: `agentscope.tool` MUST stop exposing the legacy search aggregate
  functions as public top-level exports.
- **FR-003**: System MUST add the `realtime` runtime package and its required
  runtime glue.
- **FR-004**: System MUST align the OpenAI realtime tool-schema path with the
  current upstream behavior.
- **FR-005**: System MUST keep audio playback disabled by default.
- **FR-006**: System MUST keep top-level import safety intact.
- **FR-007**: System MUST declare the direct dependencies required by the new
  realtime runtime path.

## Success Criteria

### Measurable Outcomes

- **SC-001**: Focused agent/tool/voice tests pass.
- **SC-002**: `pre-commit`, `ruff`, and `pylint -E` pass.
- **SC-003**: Public export checks match the wave-1 hard-cut decision.
- **SC-004**: Playback-gate tests prove default-off audio behavior.
