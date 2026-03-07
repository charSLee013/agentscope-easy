# Quickstart: 027 worktree subagent megabatch closeout

## 1) Create integration branch and lane worktrees

```bash
git branch 027-worktree-subagent-megabatch easy
mkdir -p ../wt-027
git worktree add ../wt-027/lane-a -b 027-lane-a-runtime-memory easy
git worktree add ../wt-027/lane-b -b 027-lane-b-model-formatter easy
git worktree add ../wt-027/lane-c -b 027-lane-c-rag-plan-reader easy
git worktree add ../wt-027/lane-d -b 027-lane-d-docs-ci-compat easy
git worktree add ../wt-027/integration 027-worktree-subagent-megabatch
```

## 2) Process lane commit sets in parallel

Use one subagent per lane and run `git cherry-pick -x` for lane-assigned SHAs.
Record empty-skips/conflicts in lane reports.

## 3) Fan-in merge order

```bash
git -C ../wt-027/integration merge --no-ff 027-lane-d-docs-ci-compat -m "merge: lane-d docs ci compat"
git -C ../wt-027/integration merge --no-ff 027-lane-c-rag-plan-reader -m "merge: lane-c rag plan reader"
git -C ../wt-027/integration merge --no-ff 027-lane-b-model-formatter -m "merge: lane-b model formatter"
git -C ../wt-027/integration merge --no-ff 027-lane-a-runtime-memory -m "merge: lane-a runtime memory"
```

## 4) Run integration gates

```bash
pre-commit run --all-files
python -m ruff check src tests
python -m pytest -p no:capture tests/plan_test.py tests/rag_reader_test.py tests/react_agent_test.py -q
python -m pytest -p no:capture tests/model_openai_test.py tests/model_gemini_test.py -q
python -m pytest -p no:capture tests/formatter_openai_test.py tests/formatter_gemini_test.py tests/formatter_ollama_test.py tests/formatter_dashscope_test.py -q
python -m pytest -p no:capture tests/init_import_test.py tests/model_dashscope_test.py tests/search/test_search_schema_contracts.py -q
```
