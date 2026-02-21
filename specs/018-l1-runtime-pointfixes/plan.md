# Implementation Plan: L1 runtime point fixes

**Branch**: `018-l1-runtime-pointfixes`
**Date**: 2026-02-20
**Spec**: `specs/018-l1-runtime-pointfixes/spec.md`

## Summary

Absorb a low-conflict runtime batch by cherry-picking:
- `a2bf80e` plan hook typing fix
- `224e8a3` stream printing output fix
- `9d4cefa` stream printing pipeline fix

Then restore unintended test deletion (`tests/token_huggingface_test.py`) and
validate with strict local gates.

## Scope

- `src/agentscope/plan/_plan_notebook.py`
- `src/agentscope/agent/_react_agent.py`
- `src/agentscope/agent/_agent_base.py`
- `examples/evaluation/ace_bench/main.py`
- `tests/token_huggingface_test.py` (restore only)

## Quality Gates

- `pre-commit run --all-files` twice
- `./.venv/bin/python -m ruff check src tests`
- `./.venv/bin/python -m pylint -E src`
- focused runtime tests with fallback to unittest if local pytest is unstable
