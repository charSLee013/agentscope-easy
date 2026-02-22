# Quickstart: 023 l1 fast closeout b

## Commit processing commands

1. `git cherry-pick -x 19cba5c`
2. `git cherry-pick -x 6c25ef0`
3. `git cherry-pick -x 2af3430`
4. `git cherry-pick -x 81490c8`

For empty commits, use `git cherry-pick --skip`.
For context-drift-only conflicts, use `git cherry-pick --skip` and document
conflict-safe skip in specs artifacts.

## Validation commands

- `pre-commit run --all-files`
- `pre-commit run --all-files`
- `./.venv/bin/python -m ruff check src tests`
- `./.venv/bin/python -m pylint -E src`
- `./.venv/bin/python -m unittest tests.formatter_anthropic_test tests.formatter_dashscope_test tests.formatter_openai_test -v`
- `./.venv/bin/python -m unittest tests.model_openai_test tests.model_dashscope_test -v`
