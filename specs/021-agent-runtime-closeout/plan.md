# Implementation Plan: 021 agent runtime closeout

**Branch**: `021-agent-runtime-closeout`
**Date**: 2026-02-22
**Spec**: `specs/021-agent-runtime-closeout/spec.md`

## Summary

Absorb the agent-runtime same-lane fixes in a single branch to reduce repeated
small-batch friction, while preserving easy-specific architecture during
conflicts.

## Selected Commit Set

1. `34a8a300` fix(agent) CancelError on interruption
2. `7f83c1ed` fix(agent) separate `enable_meta_tool` and `plan_notebook`
3. `f4c6b6f0` fix(agent) set `tool_choice=required` for structured output
4. `5a247979` fix(ReActAgent) `enable_meta_tool` argument
5. `df968057` fix(ReActAgent) `handle_interrupt` params
6. `dd05db2f` fix(ReActAgent) record_to_memory before return
7. `28547e7c` fix(tool_choice) warning once
8. `1c9d88b9` fix(deepresearch) response error

## Observed Outcomes

- Applied: `34a8a300`, `7f83c1ed`, `f4c6b6f0`, `5a247979`,
  `28547e7c`, `1c9d88b9`
- Empty-skipped: `df968057`, `dd05db2f`

## Conflict Rules

1. `README*`: not touched in this batch.
2. `src/agentscope/__init__.py`: preserve easy lazy-import structure.
3. `src/agentscope/agent/_react_agent.py`: merge only fix semantics and avoid
   importing unrelated refactor-only blocks.

## Validation Gates

1. `pre-commit run --all-files` pass 1
2. `pre-commit run --all-files` pass 2 clean
3. `./.venv/bin/python -m ruff check src tests`
4. `./.venv/bin/python -m pylint -E src`
5. Targeted tests:
   - `./.venv/bin/python -m pytest tests/react_agent_test.py tests/pipeline_test.py tests/hook_test.py -q`
   - `./.venv/bin/python -m pytest tests/model_openai_test.py tests/model_dashscope_test.py tests/model_anthropic_test.py tests/model_gemini_test.py -q`
   - `./.venv/bin/python -m pytest tests/evaluation_test.py -q`
   - fallback to `unittest` if local pytest known `-1` issue appears.
