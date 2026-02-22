# Quickstart: 022 reactagent residual closeout

## Process commands

1. Attempt residual commits in order:
   - `git cherry-pick -x d3c0c1d`
   - `git cherry-pick -x df96805`
   - `git cherry-pick -x dd05db2`
2. For empty cherry-picks, run `git cherry-pick --skip`.
3. For risky conflict against easy-only behavior, run
   `git cherry-pick --abort` and mark conflict-safe-skipped in specs.

## Validation commands

- `pre-commit run --all-files`
- `pre-commit run --all-files`
- `./.venv/bin/python -m ruff check src tests`
- `./.venv/bin/python -m pylint -E src`
- `./.venv/bin/python -m unittest tests.react_agent_test tests.plan_test -v`
