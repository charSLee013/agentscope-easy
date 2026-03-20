# Implementation Plan: Rebuild core agent/tool + MCP runtime on the new `easy` trunk

**Branch**: `036-core-agent-tool-mcp-runtime` | **Date**: 2026-03-21 | **Spec**: `specs/036-core-agent-tool-mcp-runtime/spec.md`
**Input**: Feature specification from `specs/036-core-agent-tool-mcp-runtime/spec.md`

## Summary

This wave rebuilds the core agent/tool path on top of the new `easy` trunk.
It deliberately stops at the stable center: toolkit contracts, MCP runtime glue,
and the critical ReActAgent loop fixes that do not depend on later waves.

## Technical Context

**Language/Version**: Python 3.10+
**Primary Dependencies**: current repo `.venv`, existing `mcp`/`pydantic` toolchain
**Testing**: targeted `pytest -p no:capture`, then `pre-commit run --all-files`
**Target Platform**: local macOS worktree
**Project Type**: Python library repo with ignored local `.codex` and tracked `specs/`

## Scope

In scope:

- Create `specs/036-core-agent-tool-mcp-runtime/{spec,plan,tasks}.md`
- Rebuild core toolkit/tool registration contracts
- Rebuild core MCP runtime glue
- Rebuild selected ReActAgent loop fixes
- Add/update minimal SOP files for touched modules if still missing
- Record milestone-by-milestone subagent review results

Out of scope:

- `SubAgent`
- `RealtimeAgent`, TTS/audio, memory/ReMe
- `search`, `web`, raw text I/O side tool families
- Broad docs/tutorial/example cleanup
- `git push`

## Milestones

### M1 - Freeze wave docs and test targets

- Create `specs/036` and fill `.codex/long-horizon/*`
- Record include/exclude matrix and candidate legacy commits
- Confirm baseline targeted tests

### M2 - Tool/MCP core block

- Add/port failing tests for toolkit and MCP contracts
- Implement the minimum runtime changes to pass them
- Run a read-only subagent review against `Prompt.md`, `Plan.md`, and the current diff

### M3 - ReActAgent core block

- Add/port failing tests for the selected ReActAgent loop fixes
- Implement the minimum runtime changes to pass them
- Run another read-only subagent review against the long-horizon docs and current diff

### M4 - Minimal SOP + final verification

- Add/update only the minimal long-term module rules needed in `docs/agent/SOP.md`, `docs/tool/SOP.md`, and `docs/mcp/SOP.md` if absent
- Run targeted tests, `pre-commit run --all-files`, and final proof loop
- Commit locally

## Verification

- Baseline:
  - `PYTHONPATH=src /Users/charslee/Repo/private/agentscope-easy/.venv/bin/pytest -p no:capture tests/toolkit_basic_test.py tests/react_agent_test.py tests/mcp_streamable_http_client_test.py -q`
- Tool/MCP block:
  - `PYTHONPATH=src /Users/charslee/Repo/private/agentscope-easy/.venv/bin/pytest -p no:capture tests/toolkit_basic_test.py tests/toolkit_meta_tool_test.py tests/mcp_client_test.py tests/mcp_streamable_http_client_test.py -q`
- ReAct block:
  - `PYTHONPATH=src /Users/charslee/Repo/private/agentscope-easy/.venv/bin/pytest -p no:capture tests/react_agent_test.py -q`
- Final:
  - `PYTHONPATH=src /Users/charslee/Repo/private/agentscope-easy/.venv/bin/pytest -p no:capture tests/toolkit_basic_test.py tests/toolkit_meta_tool_test.py tests/mcp_client_test.py tests/mcp_streamable_http_client_test.py tests/react_agent_test.py -q`
  - `/Users/charslee/Repo/private/agentscope-easy/.venv/bin/pre-commit run --all-files`
  - `python3 ~/.codex/skills/long-horizon-runner/scripts/finalize_long_horizon_run.py --target . --require-path specs/036-core-agent-tool-mcp-runtime/spec.md --require-path specs/036-core-agent-tool-mcp-runtime/plan.md --require-path specs/036-core-agent-tool-mcp-runtime/tasks.md`

## Commit Target

- `feat(agent-tool): rebuild core toolkit mcp and react loop on easy`
