# Quickstart Validation

1. Verify branch commits:
   - `git log --oneline easy..HEAD`
2. Run gates:
   - `pre-commit run --all-files` twice
   - `./.venv/bin/python -m ruff check src tests`
   - `./.venv/bin/python -m pylint -E src`
3. Run focused runtime checks and record results.
