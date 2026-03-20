# Feature Specification: Rebuild core agent/tool + MCP runtime on the new `easy` trunk

**Feature Branch**: `036-core-agent-tool-mcp-runtime`
**Base Branch**: `easy`
**Created**: 2026-03-21
**Status**: Draft
**Input**: User direction: "按长线方式逐步把旧 easy 中真正关键有价值的东西重新合并进新的 easy；第一波选方案 A：core agent/tool + mcp runtime。"

## Clarifications

- This is the first runtime rebuild wave after the trunk reset and filesystem
  MVP. It rebuilds the **core** agent/tool path only.
- The branch starts from current `easy` (`801f564...`), not from `035`.
  `035` is a reference truth source, not an implementation base.
- `docs/*/SOP.md` remains the only long-term normative source. `specs/036`
  records this wave's change flow, tasking, and acceptance only.
- Remote updates remain user-owned. This branch may commit locally but must not
  run `git push`.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Maintainer gets a stable core tool registration path (Priority: P1)

As a maintainer, I want `Toolkit` and tool registration behavior on the new
`easy` trunk to include the legacy fixes that still matter, so the core
tool-calling path is stable before higher-level features return.

**Why this priority**: If `Toolkit` contracts are unstable, every later wave
(`SubAgent`, search, memory, tracing) sits on a shaky base.

**Independent Test**:

- Focused toolkit tests cover duplicate registration, rename behavior,
  extended-model schema merging, and meta-tool group flow.

**Acceptance Scenarios**:

1. **Given** duplicate tool names, **When** I register tools in the toolkit,
   **Then** the toolkit behaves according to the frozen duplicate/rename policy
   and tests prove it.
2. **Given** a tool with nested Pydantic models, **When** I extend its schema,
   **Then** nested `$defs` merge without breaking JSON schema generation.

---

### User Story 2 - Maintainer gets stable MCP runtime glue in the core path (Priority: P1)

As a maintainer, I want MCP callable-function and cleanup contracts aligned
with the legacy value that still matters, so toolkit-level MCP usage is stable
before we think about bigger integrations.

**Why this priority**: MCP sits directly on the tool path; if timeout or cleanup
contracts are wrong, core tool execution is incomplete.

**Independent Test**:

- Targeted MCP tests cover callable timeout propagation, cleanup behavior, and
  streamable HTTP result conversion.

**Acceptance Scenarios**:

1. **Given** a stateful or stateless MCP client, **When** I request a callable
   function with an execution timeout, **Then** that timeout is preserved.
2. **Given** a streamable HTTP MCP response with embedded content, **When**
   AgentScope wraps it, **Then** the result becomes the expected tool blocks.

---

### User Story 3 - Maintainer gets the critical ReActAgent loop fixes without dragging in later waves (Priority: P1)

As a maintainer, I want the ReActAgent main loop to absorb only the core fixes
that matter now, so the main agent path becomes stable without accidentally
pulling in realtime, TTS/audio, memory, or SubAgent scope.

**Why this priority**: ReActAgent is the center of the first runtime wave, but
it is also the easiest place for later-wave scope to leak in.

**Independent Test**:

- Focused ReActAgent tests cover structured-output `tool_choice`,
  finish-tool direct-reply convergence, structured metadata carry-over, and
  core loop regressions.

**Acceptance Scenarios**:

1. **Given** structured output is required, **When** the agent reasons, **Then**
   `tool_choice` is forced as expected and tested.
2. **Given** the finish tool succeeds, **When** it returns either a direct
   `response` text or only structured metadata for a follow-up text turn,
   **Then** the final assistant reply preserves the expected text/metadata
   behavior without introducing unrelated wave-2/wave-3 logic.

## Edge Cases

- Legacy diffs in `agent/` contain `RealtimeAgent`, `SubAgent`, and audio/TTS
  work that is not part of this wave.
- Legacy diffs in `tool/` contain `search`, `web`, and raw text-file policy
  work that is not part of this wave.
- The current `easy` snapshot lacks tracked `specs/` and minimal
  `docs/agent|tool|mcp` normative files, so this wave must create them without
  turning specs into the normative source.
- Some legacy fixes were absorbed from upstream main and some were easy-only;
  this wave must prefer the current codebase shape and port behavior, not copy
  old file states blindly.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: This wave MUST create tracked
  `specs/036-core-agent-tool-mcp-runtime/{spec,plan,tasks}.md`.
- **FR-002**: This wave MUST rebuild the core `Toolkit` / tool registration
  path using the current `easy` file structure, not by wholesale copying old
  `easy` files.
- **FR-003**: This wave MUST include the legacy-value fixes in the core toolkit
  path for:
  - duplicate registration handling
  - original-name preservation on rename
  - nested `$defs` / extended-model schema merge correctness
  - meta-tool group deactivation flow
  - custom `func_name` registration compatibility if still missing on current `easy`
- **FR-004**: This wave MUST include the legacy-value fixes in the MCP runtime
  path for callable timeout propagation, cleanup behavior, and streamable HTTP
  content conversion where still missing on current `easy`.
- **FR-005**: This wave MUST include only the core ReActAgent fixes that are
  independent of SubAgent, realtime, TTS/audio, and memory waves.
- **FR-006**: This wave MUST NOT introduce `SubAgent` runtime, `search/web`
  tool families, raw text I/O guard work, `RealtimeAgent`, or TTS/audio changes.
- **FR-007**: After each major implementation block, the branch MUST run a
  read-only subagent review against the long-horizon docs and current diff, and
  record whether to `continue` or `fix`.
- **FR-008**: This wave MUST end with local verification and a local commit,
  but MUST NOT perform `git push`.

## Include / Exclude Matrix

| Area | Decision | Notes |
| --- | --- | --- |
| `tool/_toolkit.py`, registration/types/wrappers | include | Core of wave 1 |
| `mcp/_client_base.py`, `_stateful_client_base.py`, `_http_stateless_client.py`, `_mcp_function.py` | include | Core MCP runtime glue |
| `agent/_react_agent.py` and minimal supporting agent helpers | include | Only core loop fixes |
| `agent/_subagent_*` | exclude | Later wave |
| `agent/_realtime_agent.py` | exclude | Audio/TTS/realtime wave |
| `tool/_search/*` | exclude | Later wave |
| `tool/_web/*` | exclude | Later wave |
| `tool/_text_file/*` raw policy changes | exclude | Filesystem-centric direction kept |

## Candidate Legacy Commits For This Wave

- `817c718` - mainline toolkit and MCP runtime fixes
- `ac55c20` - custom `func_name` support
- `5de906a` - preserve original tool names on rename
- `a69211f` - duplicate registration handling
- `674ab7d` - nested `$defs` merge when extending schema
- `1b1bb96` - meta tool group deactivation flow
- `ebc7fd7`, `4745f5c`, `21cc8cb`, `133e5cd`, `8eec847`, `9559097` - core ReActAgent loop fixes

## Explicitly Deferred Legacy Commits

- `aad8644`, `d78b089` and all `agent/_subagent_*` related work
- `67bb506` portions that are purely realtime/audio/TTS
- `b9cdd37` and all `tool/_search/*`
- `0f9cb0c` and raw text I/O guard policy

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: `specs/036-core-agent-tool-mcp-runtime/spec.md`,
  `plan.md`, and `tasks.md` all exist.
- **SC-002**: The core toolkit/MCP tests added or updated for this wave fail
  before implementation and pass after implementation.
- **SC-003**: `tests/react_agent_test.py` covers the selected core ReActAgent
  fixes and passes after implementation.
- **SC-004**: Every major implementation block has a recorded subagent review
  result in `Documentation.md`.
- **SC-005**: `python3 ~/.codex/skills/long-horizon-runner/scripts/validate_long_horizon_docs.py --target .`
  passes after each milestone.
- **SC-006**: Final targeted tests and `pre-commit run --all-files` pass before
  local commit.
