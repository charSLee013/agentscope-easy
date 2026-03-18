# Implementation Plan: 033 mainline M2 tracing/model glue merge

**Branch**: `033-mainline-m2-tracing-model-glue`
**Date**: 2026-03-18
**Spec**: `specs/033-mainline-m2-tracing-model-glue/spec.md`

## Summary

Implement the second mainline absorption wave on `easy` by landing the
remaining model/formatter compatibility patches already approved for M2:
Azure OpenAI support, provider usage metadata, controllable streaming tool
parsing, DashScope multimodality/env headers, Anthropic tool-use fixes, and
Gemini compatibility.

## Selected Change Set

1. Long-horizon and change-river ledger:
   - `.codex/long-horizon/Prompt.md`
   - `.codex/long-horizon/Plan.md`
   - `.codex/long-horizon/Documentation.md`
   - `.codex/long-horizon/source-matrix.md`
   - `specs/033-mainline-m2-tracing-model-glue/*`
2. Model/runtime compatibility:
   - `src/agentscope/model/_model_usage.py`
   - `src/agentscope/model/_openai_model.py`
   - `src/agentscope/model/_dashscope_model.py`
   - `src/agentscope/model/_anthropic_model.py`
   - `src/agentscope/model/_gemini_model.py`
   - `src/agentscope/model/_ollama_model.py`
   - `src/agentscope/message/_message_block.py`
   - `src/agentscope/_utils/_common.py`
3. Formatter/SOP alignment:
   - `src/agentscope/formatter/_dashscope_formatter.py`
   - `docs/model/SOP.md`
4. Focused tests:
   - `tests/model_openai_test.py`
   - `tests/model_dashscope_test.py`
   - `tests/model_anthropic_test.py`
   - `tests/model_gemini_test.py`
   - `tests/model_ollama_test.py`
   - `tests/formatter_dashscope_test.py`

## Conflict Rules

1. Public model constructor surfaces may change when needed; compatibility hard
   cuts are acceptable if they follow the user-approved M2 direction.
2. Keep the implementation tightly scoped to M2 glue work; do not pull in M3
   memory/TTS or M4 A2A/RAG scope through the side door.
3. Preserve `easy` import-safety and optional-feature behavior while absorbing
   provider compatibility patches.
4. Prefer semantically merging upstream patches into current `easy` code over
   mechanical cherry-pick.

## Validation Gates

1. Long-horizon doc validation:
   - `./.venv/bin/python ~/.codex/skills/long-horizon-runner/scripts/validate_long_horizon_docs.py --target .`
2. Focused pytest:
   - `./.venv/bin/python -m pytest tests/model_openai_test.py tests/model_dashscope_test.py tests/model_anthropic_test.py tests/model_gemini_test.py tests/model_ollama_test.py tests/formatter_dashscope_test.py tests/tracer_test.py tests/config_test.py -q`
3. Quality gates:
   - `PRE_COMMIT_HOME="$PWD/.cache/pre-commit" ./.venv/bin/pre-commit run --all-files`
   - `./.venv/bin/python -m ruff check src tests`
   - `./.venv/bin/python -m pylint -E src`
