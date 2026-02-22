# Quickstart: 024 model l1 fix batch

## Processing commands

1. `git cherry-pick -x 6bc219a`
2. `git cherry-pick -x 3b67178`
3. `git cherry-pick -x 44b6806`

For empty picks, use `git cherry-pick --skip` and document equivalent commit
hashes from easy history.

## Validation commands

- `pre-commit run --all-files`
- `pre-commit run --all-files`
- `./.venv/bin/python -m ruff check src tests`
- `./.venv/bin/python -m pylint -E src`
- `./.venv/bin/python -m unittest tests.model_openai_test tests.formatter_deepseek_test -v`
- `./.venv/bin/python -m unittest tests.tool_openai_test tests.tool_dashscope_test -v`
