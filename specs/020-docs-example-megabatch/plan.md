# Implementation Plan: 020 docs/example megabatch

**Branch**: `020-docs-example-megabatch`
**Date**: 2026-02-21
**Spec**: `specs/020-docs-example-megabatch/spec.md`

## Summary

Absorb one large "same-lane" batch from upstream (`docs/example/ci/version`)
to speed up convergence while keeping easy-specific behavior stable.

## Scope

- 16 target commits were attempted in fixed order.
- Conflict hotspots were resolved with explicit rules:
  - `README.md`: keep easy structure (`ours`) when full-file overwrite occurs.
  - `src/agentscope/_version.py`: keep current stable version during
    intermediate conflicts; final remains `1.0.10`.
  - werewolves prompt conflict: preserve current prompt architecture and apply
    semantic one-line response fix.

## Target Commits

1. `c2c59e56`
2. `073d16d3`
3. `3ca85617`
4. `654921ff`
5. `6c25ef07`
6. `a1e681a6`
7. `0864a8df`
8. `fd1335fc`
9. `fa85f38a`
10. `cb352877`
11. `93938ee7`
12. `c7b1ff0f`
13. `2d3cbe74`
14. `81490c88`
15. `08be504e`
16. `2af34309`

## Validation Gates

1. `pre-commit run --all-files` pass 1
2. `pre-commit run --all-files` pass 2 clean
3. `./.venv/bin/python -m ruff check src tests`
4. `./.venv/bin/python -m pylint -E src`
5. Targeted tests for touched lanes:
   - `./.venv/bin/python -m pytest tests/hook_test.py tests/pipeline_test.py tests/react_agent_test.py -q`
   - `./.venv/bin/python -m pytest tests/rag_reader_test.py tests/rag_knowledge_test.py tests/rag_store_test.py -q`
   - fallback to `unittest` if local pytest returns known `-1` issue.

## Compatibility Correction

- During validation, commits `93938ee7` and `c7b1ff0f` reintroduced ReMe
  modules that triggered pylint hard errors on this baseline.
- Correction applied: both commits were reverted (`af84463`, `1a60b63`) to keep
  the batch mergeable while retaining the rest of the megabatch.
