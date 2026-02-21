# Quickstart: 019 L1 fast closeout A

## 1. Create branch

```bash
.specify/scripts/bash/create-new-feature.sh --json --number 19 --short-name "l1-fast-closeout-a" "低风险快收口 A"
```

## 2. Attempt ordered cherry-pick

```bash
git cherry-pick 62aa63919f6b8f814b6a7aee6e8c7aec1e51bced
git cherry-pick 6bc219acbe4b1eda2cd4da40b8fb81287ff38cea
git cherry-pick 28547e7c83673cc9196f353dd550f89463581042
```

If conflict appears on modernized files, keep current architecture and continue
or skip if empty:

```bash
git checkout --ours src/agentscope/__init__.py src/agentscope/agent/_react_agent.py
git add src/agentscope/__init__.py src/agentscope/agent/_react_agent.py
git cherry-pick --continue || git cherry-pick --skip
```

## 3. Run local gates

```bash
pre-commit run --all-files
pre-commit run --all-files
./.venv/bin/python -m ruff check src tests
./.venv/bin/python -m pylint -E src
./.venv/bin/python -m pytest tests/model_openai_test.py tests/model_dashscope_test.py -q
```
