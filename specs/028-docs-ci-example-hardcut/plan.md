# Implementation Plan: 028 docs CI example hardcut

- **Branch**: `028-docs-ci-example-hardcut`
- **Date**: 2026-03-09
**Spec**: `specs/028-docs-ci-example-hardcut/spec.md`

## Summary

Keep real tutorial execution for local manual docs builds, but hard-stop those
examples from entering CI execution by changing Sphinx gallery selection only
when the standard `CI` environment variable is present.

## Implementation Steps

1. Patch English tutorial Sphinx config to derive `IN_CI` from `CI`.
2. Patch Chinese tutorial Sphinx config with the same gating rule.
3. Set gallery `filename_pattern` to match no files in CI and keep the current
   `src/.*\.py` pattern outside CI.
4. Record the policy in `specs/028` so the CI boundary is explicit.

## Validation Gates

1. Confirm current GitHub workflows do not run docs build.
2. Confirm both tutorial configs now branch on `CI`.
3. Run `pre-commit run --all-files`.
4. Run targeted tests only if touched docs config causes collateral failures.
