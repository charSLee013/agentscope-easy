# Research Notes: 028 docs CI example hardcut

## Why this approach

The instability is not that tutorial examples use real APIs. The instability is
that executable tutorial examples can be pulled into CI and then inherit all
external dependencies: secrets, network, and upstream service health.

## Practical observations

1. Current GitHub workflows run unit tests and pre-commit checks, not docs
   builds.
2. Tutorial Sphinx configs still select `src/*.py` examples for execution.
3. A future docs workflow could reintroduce CI flakes unless config is CI-safe.

## Policy choice

- Keep local/manual docs builds fully functional.
- Disable tutorial example execution only in CI.
- Avoid rewriting 34 tutorial example files for a policy problem.
