# Implementation Plan: 024 model l1 fix batch

**Branch**: `024-model-l1-fix-batch`
**Date**: 2026-02-22
**Spec**: `specs/024-model-l1-fix-batch/spec.md`

## Summary

Process three model-related L1 fixes in one branch. All are already equivalent
on easy baseline, so this batch closes out duplicate absorption risk with
explicit evidence.

## Selected Commit Set

1. `6bc219a` fix(model): dict-only `_json_loads_with_repair`
2. `3b67178` fix(chatmodel): `OpenAIChatModel` handles `choice.delta=None`
3. `44b6806` fix(deepseek): support `reasoning_content` in input messages

## Observed Outcomes

- Empty-skipped:
  - `6bc219a` (equivalent present as `7645c47`)
  - `3b67178` (equivalent present as `3c74b72`)
  - `44b6806` (equivalent present as `531043c`)

## Conflict Rules

1. Do not force non-essential merges for already equivalent fixes.
2. Keep easy baseline unchanged when no net code delta is needed.

## Validation Gates

1. `pre-commit run --all-files` pass 1
2. `pre-commit run --all-files` pass 2 clean
3. `./.venv/bin/python -m ruff check src tests`
4. `./.venv/bin/python -m pylint -E src`
5. Focused tests:
   - `./.venv/bin/python -m unittest tests.model_openai_test tests.formatter_deepseek_test -v`
   - `./.venv/bin/python -m unittest tests.tool_openai_test tests.tool_dashscope_test -v`
