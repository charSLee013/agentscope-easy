# Contracts Notes

This change keeps the public API surface intact but tightens the platform
contract for `RayEvaluator`.

Touched behavior surfaces:

- `RayEvaluator` construction on native Windows
- evaluation tutorial wording
- evaluation test messaging

Contract policy:

- native Windows is not supported for `RayEvaluator`;
- WSL2 and non-Windows platforms retain the normal path;
- `GeneralEvaluator` remains available on native Windows.
