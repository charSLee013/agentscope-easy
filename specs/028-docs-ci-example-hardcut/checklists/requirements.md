# Specification Quality Checklist: 028-docs-ci-example-hardcut

- **Purpose**: Validate CI hardcut for real tutorial example execution
- **Created**: 2026-03-09
**Feature**: `specs/028-docs-ci-example-hardcut/spec.md`

## Scope and Safety

- [x] CI-only gating is applied in both tutorial configs
- [x] Local manual docs execution remains available
- [x] No tutorial example source files were rewritten
- [x] No runtime public API changed

## Verification

- [x] `pre-commit run --all-files` passed
- [x] Workflow scan confirms no docs build job executes examples

## Notes

- This change fixes the CI boundary instead of mocking all tutorial examples.
- The remaining independent CI stability item is Windows + Ray behavior.
