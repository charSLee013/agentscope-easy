# Research Notes: 026 toolkit l1 closeout

## Selection logic

Chose toolkit same-lane fixes with direct correctness impact and bounded risk.

## Per-commit status

- `873cfe2`: applied via cherry-pick.
- `5bc937a`: applied via conflict-safe selective migration.
  - Included: `src/agentscope/tool/_toolkit.py` behavior fix.
  - Included: update existing `tests/toolkit_test.py` meta-tool expectations and
    deactivation coverage.
  - Excluded as non-scope noise: `src/agentscope/_version.py`,
    `src/agentscope/_utils/_common.py`, docs typo, test-file split artifacts.

## Risk decision

Keeping scope strictly in toolkit behavior fixes avoids pulling unrelated
changes into this closeout lane.
