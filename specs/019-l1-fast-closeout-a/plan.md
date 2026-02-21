# Implementation Plan: L1 fast closeout A

**Branch**: `019-l1-fast-closeout-a`
**Date**: 2026-02-21
**Spec**: `specs/019-l1-fast-closeout-a/spec.md`

## Summary

Absorb low-risk upstream batch:
- `62aa639` (`py.typed`)
- `6bc219a` (`_json_loads_with_repair` contract tightening)
- `28547e7` (`tool_choice` deprecated warning once)

Execution result is expected to be no-op if current `easy` already contains
equivalent semantics. We still preserve full spec evidence and quality gates.

## Scope

- Cherry-pick operation and conflict resolution only
- `specs/019-l1-fast-closeout-a/*` documentation artifacts
- No intentional source behavior changes if commits are empty-equivalent

## Technical Context

- Language: Python 3.10+ (project requirement)
- Tooling: `pre-commit`, `ruff`, `pylint`, `pytest/unittest`
- Branch strategy: base `easy`, never `main/master`
- Risk profile: low-risk point fixes, no L3 refactor

## Constitution Check

- [x] Branch base is `easy`
- [x] Work follows `spec -> plan -> tasks`
- [x] No schema/API expansion beyond upstream-equivalent behavior
- [x] Security boundary unchanged (no new secrets/I/O surface)
- [x] Local quality gates required before commit

## Validation Gates

1. `pre-commit run --all-files` (pass 1)
2. `pre-commit run --all-files` (pass 2 clean)
3. `./.venv/bin/python -m ruff check src tests`
4. `./.venv/bin/python -m pylint -E src`
5. Focused tests:
   - `./.venv/bin/python -m pytest tests/model_openai_test.py tests/model_dashscope_test.py -q`
   - fallback to `unittest` only if local pytest is unstable

## Implementation Notes

- If cherry-pick conflicts with modernized files (`__init__.py`,
  `src/agentscope/agent/_react_agent.py`), resolve with minimal merge and do
  not roll back current architecture.
- If patch becomes empty after resolution, use `git cherry-pick --skip` and
  record evidence.
