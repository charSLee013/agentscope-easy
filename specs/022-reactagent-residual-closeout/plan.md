# Implementation Plan: 022 reactagent residual closeout

**Branch**: `022-reactagent-residual-closeout`
**Date**: 2026-02-22
**Spec**: `specs/022-reactagent-residual-closeout/spec.md`

## Summary

Close out remaining low-risk ReactAgent same-lane fixes in one pass, with
conflict-safe policy that preserves easy-only runtime behavior.

## Selected Commit Set

1. `d3c0c1d` fix(ReActAgent): filter `None` values when joining retrieval text
2. `df96805` fix(ReActAgent): fix `handle_interrupt` parameters
3. `dd05db2` fix(ReActAgent): invoke `record_to_memory` before returning reply

## Observed Outcomes

- Empty-skipped (already equivalent on easy):
  - `d3c0c1d` (equivalent already present as `4745f5c`)
  - `df96805` (equivalent already present as `ebc7fd7`)
- Conflict-safe skipped:
  - `dd05db2` (cherry-pick conflicts with obsolete upstream
    structured-output branch blocks; kept easy baseline behavior)

## Conflict Rules

1. `src/agentscope/agent/_react_agent.py`: do not import unrelated upstream
   branch-flow refactor blocks.
2. Keep easy baseline control flow and memory lifecycle unchanged unless the
   patch is strictly isolated and behavior-preserving.

## Validation Gates

1. `pre-commit run --all-files` pass 1
2. `pre-commit run --all-files` pass 2 clean
3. `./.venv/bin/python -m ruff check src tests`
4. `./.venv/bin/python -m pylint -E src`
5. Focused tests:
   - `./.venv/bin/python -m unittest tests.react_agent_test tests.plan_test -v`
