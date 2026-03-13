# Data Model: 029 Windows RayEvaluator hard cut

No business-domain model changes are introduced.

## 1) RayPlatformSupportPolicy

- `platform` (string): operating system name from `platform.system()`
- `supported` (bool): whether `RayEvaluator` may proceed
- `guidance` (string): recommended alternative when unsupported

## 2) RayEvaluatorRuntimeGuard

- `check` (callable): validates platform before Ray-specific setup
- `error` (runtime): explains native Windows is unsupported and recommends
  WSL2 or Linux/macOS
