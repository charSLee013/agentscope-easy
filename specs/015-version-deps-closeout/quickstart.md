# Quickstart: Verify 015 version/dependency closure

## 1) Inspect target commit intent

```bash
git show --name-only --oneline 08be504
git show --name-only --oneline 7df0148
git show --name-only --oneline 2984902
```

## 2) Verify current easy state

```bash
cat src/agentscope/_version.py
rg -n "opentelemetry-|mem0ai" pyproject.toml
```

Expected:
- version is `1.0.10` (supersedes 1.0.9 target)
- OTel constraints and mem0 pin already present

## 3) Verify this branch is specs-only

```bash
git diff --name-only easy...HEAD
```

Expected: only `specs/015-version-deps-closeout/*`.

## 4) Quality gate

```bash
pre-commit run --all-files
```
