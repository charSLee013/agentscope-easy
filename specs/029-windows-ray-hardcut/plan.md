# Implementation Plan: 029 Windows RayEvaluator hard cut

- **Branch**: `029-windows-ray-hardcut`
- **Date**: 2026-03-10
**Spec**: `specs/029-windows-ray-hardcut/spec.md`

## Summary

Make the platform contract explicit: native Windows does not support
`RayEvaluator`. Enforce that contract in runtime code, test messaging, and
evaluation docs, while keeping `GeneralEvaluator` unchanged and preserving WSL2
through the normal Linux path.

## Implementation Steps

1. Add a native-Windows guard in `RayEvaluator` before Ray availability or
   worker startup logic.
2. Update evaluation tests so the Windows skip reason reflects unsupported
   platform status and add a targeted runtime-guard test.
3. Update evaluation SOP and tutorial docs to recommend WSL2 or Linux/macOS
   for Ray-based evaluation.
4. Record the decision and validation evidence in `specs/029`.

## Validation Gates

1. Run targeted evaluation tests.
2. Run `pre-commit run --all-files`.
3. Confirm doc wording now aligns with the runtime and test behavior.
