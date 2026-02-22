# Research Notes: 020 docs/example megabatch

## Batch selection

Selected 16 commits from `git cherry -v easy main` in docs/example/ci/version
lane to increase absorption throughput.

## Conflict hotspots observed

1. `README.md` and `README_zh.md`
- Upstream rewrites conflicted with easy-customized structure.
- Resolution rule: preserve easy layout when full-file overwrite conflicts.

2. `src/agentscope/_version.py`
- Multiple commits touched version; intermediate bumps conflicted.
- Resolution rule: keep stable version during intermediate conflicts and avoid
  rollback; final version remains `1.0.10`.

3. werewolves prompts
- Upstream patch location differed from current prompt architecture.
- Resolution rule: apply semantic fix (`Generate a one-line response.`) in the
  active prompt source.

4. ReMe/tts lanes
- Some files existed in upstream but not in prior easy HEAD.
- Result: conflict resolution introduced related files when commits required it.

## Per-commit status

- Applied: `c2c59e56`, `073d16d3`, `3ca85617`, `654921ff`, `6c25ef07`,
  `a1e681a6`, `0864a8df`, `fd1335fc`, `fa85f38a`, `cb352877`,
  `2d3cbe74`, `81490c88`
- Empty-skipped: `08be504e`, `2af34309`
- Applied then reverted for compatibility: `93938ee7`, `c7b1ff0f`
  (revert commits: `af84463`, `1a60b63`)
