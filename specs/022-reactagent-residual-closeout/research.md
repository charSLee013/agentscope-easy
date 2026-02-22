# Research Notes: 022 reactagent residual closeout

## Selection logic

This batch intentionally focuses on ReactAgent residual same-lane fixes only,
so we can close out low-risk runtime leftovers in one branch.

## Hotspot

1. `_react_agent.py`
- All selected commits target this hotspot.
- Conflict policy: easy behavior first, fix intent only, no refactor carry-in.

## Per-commit status

- `d3c0c1d`: empty-skipped (semantic equivalent already present as `4745f5c`).
- `df96805`: empty-skipped (semantic equivalent already present as `ebc7fd7`).
- `dd05db2`: conflict-safe-skipped. Cherry-pick introduced obsolete
  structured-output branch blocks conflicting with easy baseline control flow;
  keeping baseline is lower risk.
