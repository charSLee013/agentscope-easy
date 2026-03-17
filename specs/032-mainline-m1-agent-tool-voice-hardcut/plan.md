# Implementation Plan: 032 mainline M1 agent/tool/voice hard cut

**Branch**: `032-mainline-m1-agent-tool-voice-hardcut`
**Date**: 2026-03-17
**Spec**: `specs/032-mainline-m1-agent-tool-voice-hardcut/spec.md`

## Summary

Implement the first mainline absorption wave on `easy` by hard-cutting the
public `agent/tool` surface toward `main`, landing the missing realtime voice
runtime in the same wave, and keeping playback default-off.

## Selected Change Set

1. Public surface switch:
   - `src/agentscope/agent/__init__.py`
   - `src/agentscope/tool/__init__.py`
   - `src/agentscope/__init__.py`
2. New runtime packages:
   - `src/agentscope/realtime/*`
3. Voice additions:
   - `src/agentscope/agent/_realtime_agent.py`
   - `src/agentscope/_utils/_common.py` realtime resampling helper
4. Wave-1 runtime fixes:
   - OpenAI realtime tool-argument formatting
   - realtime dependency alignment in `pyproject.toml`

## Conflict Rules

1. Public API follows `main` for `agent/tool` exports.
2. Internal `easy`-only code may remain temporarily if it is not part of the
   public contract and does not block the wave.
3. Audio playback default-off is higher priority than upstream voice defaults.
4. `A2A` and provider-expansion TTS stay out of this wave unless the realtime
   runtime port proves they are a hard dependency.
5. Memory architecture is not part of this branch except for directly touched
   compile/runtime compatibility.

## Validation Gates

1. Focused tests:
   - `./.venv/bin/python -m unittest tests.react_agent_test -v`
   - `./.venv/bin/python -m unittest tests.toolkit_test -v`
   - `./.venv/bin/python -m unittest tests.tts_openai_test -v`
   - `./.venv/bin/python -m unittest tests.tts_gemini_test -v`
   - `./.venv/bin/python -m unittest tests.tts_dashscope_test -v`
   - `./.venv/bin/python -m unittest tests.realtime_openai_test -v`
   - `./.venv/bin/python -m unittest tests.realtime_dashscope_test -v`
   - `./.venv/bin/python -m unittest tests.realtime_gemini_test -v`
   - `./.venv/bin/python -m unittest tests.realtime_event_test -v`
   - `./.venv/bin/python -m unittest tests.agent.test_audio_playback_gate -v`
2. Quality gates:
   - `PRE_COMMIT_HOME="$PWD/.cache/pre-commit" ./.venv/bin/pre-commit run --all-files`
   - `./.venv/bin/python -m ruff check src tests`
   - `./.venv/bin/python -m pylint -E src`
