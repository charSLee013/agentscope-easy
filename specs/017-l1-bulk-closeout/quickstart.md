# Quickstart Validation

1. Verify selected commits are on branch:
   - `git log --oneline easy..HEAD`
2. Run pre-commit twice:
   - `pre-commit run --all-files`
   - `pre-commit run --all-files`
3. Run static checks:
   - `./.venv/bin/python -m ruff check src docs examples tests`
   - `./.venv/bin/python -m pylint -E src`
4. Run focused runtime checks and record results.
