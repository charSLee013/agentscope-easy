# Implementation Plan: L1 bulk closeout absorption

**Branch**: `017-l1-bulk-closeout`
**Date**: 2026-02-18
**Spec**: `specs/017-l1-bulk-closeout/spec.md`

## Summary

Absorb a low-risk multi-commit bundle from `main` into `easy` in one branch,
then validate locally to minimize CI rework. Keep conflict-heavy items deferred
for dedicated follow-up batches.

## Selected Upstream Commits

- `9f7c410` Refine tutorial
- `b56c4dd` fix tutorial studio port
- `c635281` browser-use agent example hotfix
- `340510f` add AlibabaCloud API MCP OAuth example
- `5c3a770` docstring typo fix in MsgHub module

## Deferred Commits (this batch)

- `6c25ef0` docs image update (binary assets and README conflicts)
- `0864a8d` werewolves prompt fix (conflict)
- `6bc219a` `_json_loads_with_repair` fix (conflict)
- `df96805` ReActAgent handle_interrupt fix (conflict)
- Other conflict-heavy candidates validated by `git apply --check`

## Quality Gates

- `pre-commit run --all-files` twice (second run must be fully clean)
- `./.venv/bin/python -m ruff check src docs examples tests`
- `./.venv/bin/python -m pylint -E src`
- Focused runtime checks (document fallback if pytest is unstable)
