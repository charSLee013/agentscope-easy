# -*- coding: utf-8 -*-
from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"


def _run_python(code: str) -> subprocess.CompletedProcess[str]:
    env = os.environ.copy()
    env["PYTHONPATH"] = str(SRC) + os.pathsep + env.get("PYTHONPATH", "")
    return subprocess.run(
        [sys.executable, "-c", code],
        text=True,
        env=env,
        capture_output=True,
        check=False,
    )


def test_import_agentscope_does_not_require_requests() -> None:
    code = r"""
import builtins

real_import = builtins.__import__

def guarded_import(name, globals=None, locals=None, fromlist=(), level=0):
    if name == "requests" or name.startswith("requests."):
        raise ModuleNotFoundError("blocked: requests")
    return real_import(name, globals, locals, fromlist, level)

builtins.__import__ = guarded_import

import agentscope

assert "requests" not in globals()
print(agentscope.__version__)
"""
    res = _run_python(code)
    assert res.returncode == 0, f"stdout:\n{res.stdout}\nstderr:\n{res.stderr}"


def test_init_with_studio_url_requires_requests() -> None:
    code = r"""
import builtins

real_import = builtins.__import__

def guarded_import(name, globals=None, locals=None, fromlist=(), level=0):
    if name == "requests" or name.startswith("requests."):
        raise ModuleNotFoundError("blocked: requests")
    return real_import(name, globals, locals, fromlist, level)

builtins.__import__ = guarded_import

import agentscope

try:
    agentscope.init(studio_url="http://example.invalid")
except ImportError as e:
    print(str(e))
    raise SystemExit(0)

raise SystemExit(1)
"""
    res = _run_python(code)
    assert res.returncode == 0, f"stdout:\n{res.stdout}\nstderr:\n{res.stderr}"
    assert "pip install requests" in res.stdout


def test_import_agentscope_tts_is_provider_safe() -> None:
    code = r"""
import builtins

real_import = builtins.__import__
blocked = {"openai", "dashscope", "google", "google.genai"}

def guarded_import(name, globals=None, locals=None, fromlist=(), level=0):
    if (
        name in blocked
        or any(name.startswith(prefix + ".") for prefix in blocked)
    ):
        raise ModuleNotFoundError(f"blocked: {name}")
    return real_import(name, globals, locals, fromlist, level)

builtins.__import__ = guarded_import

import agentscope
import agentscope.tts

print(sorted(agentscope.tts.__all__))
"""
    res = _run_python(code)
    assert res.returncode == 0, f"stdout:\n{res.stdout}\nstderr:\n{res.stderr}"
    assert "OpenAITTSModel" in res.stdout


def test_import_agentscope_tune_is_trinity_safe() -> None:
    code = r"""
import builtins

real_import = builtins.__import__
blocked = {"trinity", "omegaconf"}

def guarded_import(name, globals=None, locals=None, fromlist=(), level=0):
    if (
        name in blocked
        or any(name.startswith(prefix + ".") for prefix in blocked)
    ):
        raise ModuleNotFoundError(f"blocked: {name}")
    return real_import(name, globals, locals, fromlist, level)

builtins.__import__ = guarded_import

import agentscope
import agentscope.tune

print(sorted(agentscope.tune.__all__))
"""
    res = _run_python(code)
    assert res.returncode == 0, f"stdout:\n{res.stdout}\nstderr:\n{res.stderr}"
    assert "WorkflowType" in res.stdout
