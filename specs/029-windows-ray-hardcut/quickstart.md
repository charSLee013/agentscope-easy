# Quickstart: 029 Windows RayEvaluator hard cut

## 1) Native Windows behavior

Constructing `RayEvaluator` on native Windows now fails fast with a clear error
instead of attempting unstable Ray startup.

## 2) Supported path

Use `GeneralEvaluator` on native Windows, or run Ray-based evaluation inside
WSL2/Linux/macOS.

## 3) Validation commands

```bash
python -m pytest tests/evaluation_test.py -q
pre-commit run --all-files
```
