# Quickstart: 025 version deps closeout b

## Processing commands

1. `git cherry-pick -x 2984902`
2. `git cherry-pick -x 7df0148`
3. `git cherry-pick -x 08be504`

For empty picks, run `git cherry-pick --skip`.
For stale-version conflict (downgrade), run `git cherry-pick --skip` and
record conflict-safe-skip rationale.

## Validation commands

- `pre-commit run --all-files`
- `pre-commit run --all-files`
- `./.venv/bin/python -m ruff check src tests`
- `./.venv/bin/python -m pylint -E src`
- `./.venv/bin/python -m unittest tests.packaging_contract_test -v`
- `./.venv/bin/python -m unittest tests.init_import_test -v`
