# Quickstart: 026 toolkit l1 closeout

## Processing commands

1. `git cherry-pick -x 873cfe2`
2. Attempt `git cherry-pick -x 5bc937a`
3. If conflict includes non-toolkit noise, abort and selectively migrate only
   toolkit fix semantics.

## Validation commands

- `./.venv/bin/python -m unittest tests.toolkit_test -v`
- `./.venv/bin/python -m unittest tests.tool_test -v`
- `pre-commit run --all-files`
- `pre-commit run --all-files`
- `./.venv/bin/python -m ruff check src tests`
- `./.venv/bin/python -m pylint -E src`
