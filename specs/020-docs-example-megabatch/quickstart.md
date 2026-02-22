# Quickstart: 020 docs/example megabatch

## 1) Create branch

```bash
.specify/scripts/bash/create-new-feature.sh --json --number 20 --short-name "docs-example-megabatch" "批量吸收 docs/example/ci/version"
```

## 2) Cherry-pick selected commits

Apply commits in planned order. Resolve conflicts with fixed rules:
- README conflicts: keep easy structure (`ours`) when upstream tries full overwrite.
- Version conflicts: prevent rollback during intermediate bumps.
- Prompt conflicts: preserve active architecture and apply semantic fix.

## 3) Run gates before commit

```bash
pre-commit run --all-files
pre-commit run --all-files
./.venv/bin/python -m ruff check src tests
./.venv/bin/python -m pylint -E src
./.venv/bin/python -m pytest tests/hook_test.py tests/pipeline_test.py tests/react_agent_test.py -q
./.venv/bin/python -m pytest tests/rag_reader_test.py tests/rag_knowledge_test.py tests/rag_store_test.py -q
```

If local `pytest` hits known `-1` no-output issue, fallback:

```bash
./.venv/bin/python -m unittest tests.hook_test tests.pipeline_test tests.react_agent_test -v
./.venv/bin/python -m unittest tests.rag_reader_test tests.rag_knowledge_test tests.rag_store_test -v
```
