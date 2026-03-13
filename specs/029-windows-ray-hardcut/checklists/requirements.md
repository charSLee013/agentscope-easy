# Specification Quality Checklist: 029-windows-ray-hardcut

- **Purpose**: Validate native Windows hard cut for `RayEvaluator`
- **Created**: 2026-03-10
**Feature**: `specs/029-windows-ray-hardcut/spec.md`

## Scope and Safety

- [x] Runtime rejects native Windows before Ray startup
- [x] `GeneralEvaluator` remains unaffected
- [x] Docs recommend WSL2 or Linux/macOS
- [x] Tests reflect unsupported native Windows contract

## Verification

- [x] Targeted evaluation tests passed
- [x] `pre-commit run --all-files` passed
