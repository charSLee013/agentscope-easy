# Feature Specification: Mainline M2 tracing/model glue merge

**Feature Branch**: `033-mainline-m2-tracing-model-glue`
**Base Branch**: `easy`
**Created**: 2026-03-18
**Status**: In Progress
**Input**: User description: "保持 `easy` 分支独立存在前提下继续吸收 `main`；M2 走 tracing/config/model/formatter glue，包含 Azure OpenAI、DashScope multimodality、`stream_tool_parsing`。"

## User Scenarios & Testing

### User Story 1 - Keep provider compatibility aligned with current mainline (Priority: P1)

As a maintainer, I want the OpenAI, DashScope, Anthropic, and Gemini model
adapters on `easy` to understand the newer upstream response shapes so later
waves are not blocked by protocol drift.

**Why this priority**: This is the current compatibility floor for the runtime
front door after M1.

**Independent Test**: Focused model tests cover Azure init, new reasoning
fields, DashScope multimodality/env headers, Anthropic tool-use parsing, and
Gemini compatibility.

**Acceptance Scenarios**:

1. **Given** `OpenAIChatModel`, **when** newer `reasoning` fields or Azure
   client mode are used, **then** the adapter still produces valid
   `ChatResponse` objects.
2. **Given** `DashScopeChatModel`, **when** multimodal routing or env headers
   are needed, **then** the model can be configured without forking the caller.
3. **Given** `AnthropicChatModel` and `GeminiChatModel`, **when** provider
   payloads contain newer tool/thought shapes, **then** parsing stays stable.

### User Story 2 - Make streaming tool parsing controllable without import-time regressions (Priority: P1)

As a maintainer, I want streaming tool-use parsing to be configurable so the
runtime can either expose repaired partial JSON eagerly or wait for the final
tool payload, depending on the caller’s needs.

**Why this priority**: This is the biggest M2 protocol delta and affects all
main chat providers.

**Independent Test**: Streaming tests prove both the default repaired path and
the deferred final-parse path.

**Acceptance Scenarios**:

1. **Given** streaming tool chunks, **when** `stream_tool_parsing=True`,
   **then** partial tool arguments are repaired into stable dicts during the
   stream.
2. **Given** streaming tool chunks, **when** `stream_tool_parsing=False`,
   **then** intermediate tool inputs stay empty and the final yielded tool block
   contains the parsed full input.
3. **Given** any streamed tool-use block, **when** inspecting content blocks,
   **then** the raw provider payload is retained in `raw_input`.

### User Story 3 - Preserve observability and formatter compatibility (Priority: P1)

As a maintainer, I want usage metadata and DashScope formatter edge cases to be
handled consistently so tracing/usage consumers do not lose detail after the
merge.

**Why this priority**: M2 is glue work; losing usage detail or formatter
compatibility defeats the purpose of the wave.

**Independent Test**: Focused formatter/model tests assert `ChatUsage.metadata`
and DashScope empty-content behavior.

**Acceptance Scenarios**:

1. **Given** provider usage payloads, **when** parsing succeeds, **then**
   `ChatUsage.metadata` keeps the provider-native usage object.
2. **Given** DashScope tool-call assistant messages without normal text blocks,
   **when** formatting messages, **then** `content` is `[]` instead of
   `[{"text": None}]`.

## Edge Cases

- Azure OpenAI must be an opt-in client mode on top of the existing
  `OpenAIChatModel`, not a separate model class.
- `stream_tool_parsing=False` must still emit a final tool-use block instead of
  silently dropping parsed input.
- DashScope multimodal routing must allow explicit override even when the model
  name does not imply `-vl`/`qvq`.
- Gemini tool-use ids may need to fall back to `thought_signature`-derived ids
  for Gemini-3-Pro compatibility.

## Requirements

### Functional Requirements

- **FR-001**: `OpenAIChatModel` MUST support `client_type="azure"` and keep
  the existing OpenAI path as default.
- **FR-002**: `OpenAIChatModel` MUST parse both `reasoning_content` and newer
  `reasoning` fields.
- **FR-003**: `ChatUsage` MUST expose an optional `metadata` field carrying the
  provider-native usage payload when available.
- **FR-004**: `OpenAIChatModel`, `AnthropicChatModel`, and
  `DashScopeChatModel` MUST support `stream_tool_parsing`.
- **FR-005**: `ToolUseBlock` MUST support `raw_input`.
- **FR-006**: `DashScopeChatModel` MUST support env-provided headers and an
  explicit `multimodality` switch.
- **FR-007**: `DashScopeChatFormatter` MUST emit `content: []` for assistant
  tool-call messages without valid text/media blocks.
- **FR-008**: `AnthropicChatModel` MUST prefer explicit block type checks over
  loose `text` attribute checks for tool-use parsing.
- **FR-009**: `GeminiChatModel` MUST handle Gemini-3-Pro function-call payloads
  without dropping tool calls.

## Success Criteria

### Measurable Outcomes

- **SC-001**: Focused formatter/model/tracing tests for M2 pass locally.
- **SC-002**: `pre-commit`, `ruff`, and `pylint -E src` pass after the change.
- **SC-003**: The long-horizon docs validate after the milestone ledger update.
- **SC-004**: Public provider constructor surfaces in `docs/model/SOP.md`
  reflect the new M2 parameters.
