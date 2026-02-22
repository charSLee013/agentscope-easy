# Implementation Plan: 025 version deps closeout b

**Branch**: `025-version-deps-closeout-b`
**Date**: 2026-02-22
**Spec**: `specs/025-version-deps-closeout-b/spec.md`

## Summary

Close out upstream dependency/version lane with easy-first rules. Existing easy
baseline already includes dependency floors/ceilings and a higher version.

## Selected Commit Set

1. `2984902` fix(mem0): pin `mem0ai<=0.1.116`
2. `7df0148` fix(opentelemetry): fix OTel versions
3. `08be504` fix(version): update version to `1.0.9`

## Observed Outcomes

- Empty-skipped:
  - `2984902` (equivalent in easy via `17b4b08`)
  - `7df0148` (equivalent in easy via `17b4b08`)
- Conflict-safe-skipped:
  - `08be504` (conflicts with baseline `1.0.10`; applying would downgrade)

## Conflict Rules

1. Keep easy baseline version when upstream commit is older.
2. Keep current pyproject dependency constraints when already equivalent.

## Validation Gates

1. `pre-commit run --all-files` pass 1
2. `pre-commit run --all-files` pass 2 clean
3. `./.venv/bin/python -m ruff check src tests`
4. `./.venv/bin/python -m pylint -E src`
5. Focused tests:
   - `./.venv/bin/python -m unittest tests.packaging_contract_test -v`
   - `./.venv/bin/python -m unittest tests.init_import_test -v`
