# Tasks: 032 mainline M1 agent/tool/voice hard cut

**Input**: `specs/032-mainline-m1-agent-tool-voice-hardcut/spec.md`, `specs/032-mainline-m1-agent-tool-voice-hardcut/plan.md`

## Phase 1: Setup

- [x] T001 Create branch `032-mainline-m1-agent-tool-voice-hardcut`
- [x] T002 Initialize specs skeleton
- [x] T003 Update local long-horizon working docs to reflect the new wave-1 decisions

## Phase 2: Runtime and Surface

- [x] T004 Add `realtime` runtime package and `RealtimeAgent`
- [x] T005 Hard-cut `agentscope.agent` public exports toward main
- [x] T006 Hard-cut `agentscope.tool` public exports toward main
- [x] T007 Absorb the missing realtime runtime fix (OpenAI tool formatting)
- [x] T008 Align dependencies for the wave-1 realtime runtime

## Phase 3: Tests and Cleanup

- [x] T009 Add or port focused tests for realtime/voice/public-surface behavior
- [x] T010 Update legacy tests that still assert the old public surface
- [x] T011 Run focused unittests
- [x] T012 Run `pre-commit run --all-files`
- [x] T013 Run `./.venv/bin/python -m ruff check src tests`
- [x] T014 Run `./.venv/bin/python -m pylint -E src`
