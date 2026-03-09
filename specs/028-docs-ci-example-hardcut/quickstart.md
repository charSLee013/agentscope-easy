# Quickstart: 028 docs CI example hardcut

## 1) CI-safe behavior

When `CI` is set, tutorial Sphinx configs select no gallery example files.

## 2) Local manual behavior

```bash
cd docs/tutorial/en
./build.sh
```

Local manual builds keep the existing tutorial execution behavior and still
require any necessary external API keys.

## 3) Sanity check

```bash
rg -n "IN_CI|filename_pattern" docs/tutorial/en/conf.py docs/tutorial/zh_CN/conf.py
rg -n "sphinx-build|docs/tutorial" .github/workflows -S
```
