# Quickstart: 021 agent runtime closeout

## 1) Create branch

```bash
.specify/scripts/bash/create-new-feature.sh --json --number 21 --short-name "agent-runtime-closeout" "批量吸收 agent runtime 同类修复"
```

## 2) Cherry-pick selected commits

Apply in fixed order:

```bash
git cherry-pick 34a8a300bde9c3b3f2f294ef1b9895813dd23316
git cherry-pick 7f83c1eda397cb910c5f2807cdf0319b7d06f5e3
git cherry-pick f4c6b6f0c7f5b9dc2bc0065db277aa2ea88f9f4b
git cherry-pick 5a247979e4108c820488f5b50716176c109fb372
git cherry-pick df9680572f4a59d0e54b176fca0ee209827661c5
git cherry-pick dd05db2f3324d16ee8c795bfce321384568f22fc
git cherry-pick 28547e7c83673cc9196f353dd550f89463581042
git cherry-pick 1c9d88b9ca1a0772d6290e548faf98e3ad958c48
```

For conflict resolution:
- keep easy architecture in `src/agentscope/__init__.py`;
- merge only fix-intent in `_react_agent.py`;
- use `git cherry-pick --skip` for empty-equivalent commits.

## 3) Run validation gates

```bash
pre-commit run --all-files
pre-commit run --all-files
./.venv/bin/python -m ruff check src tests
./.venv/bin/python -m pylint -E src
./.venv/bin/python -m pytest tests/react_agent_test.py tests/pipeline_test.py tests/hook_test.py -q
./.venv/bin/python -m pytest tests/model_openai_test.py tests/model_dashscope_test.py tests/model_anthropic_test.py tests/model_gemini_test.py -q
./.venv/bin/python -m pytest tests/evaluation_test.py -q
```
