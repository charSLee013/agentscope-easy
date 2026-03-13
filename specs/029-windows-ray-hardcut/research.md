# Research Notes: 029 Windows RayEvaluator hard cut

## Why this approach

The objective is not to make Ray stable on native Windows. The objective is to
stop pretending we support that platform combination when the intended local
path is WSL2 and the CI path already needs Windows-specific avoidance.

## Practical observations

1. `easy` already skips the Ray evaluator test on Windows.
2. `main` still attempts the Windows path with no explicit hard cut.
3. Evaluation docs currently describe Ray-based evaluation without any native
   Windows limitation note.

## Policy choice

- Native Windows: unsupported for `RayEvaluator`
- WSL2: supported through the Linux execution path
- `GeneralEvaluator`: unchanged on all platforms
