# -*- coding: utf-8 -*-
"""Regression tests for import-time side effects."""

import os
import subprocess
import sys
from pathlib import Path


def test_import_agentscope_tool_does_not_import_ray() -> None:
    """`import agentscope.tool` should not eagerly import ray."""
    repo_root = Path(__file__).resolve().parents[1]
    env = os.environ.copy()
    env["PYTHONPATH"] = str(repo_root / "src")

    result = subprocess.run(
        [
            sys.executable,
            "-c",
            (
                "import sys; "
                "import agentscope.tool; "
                "print('ray' in sys.modules)"
            ),
        ],
        check=True,
        capture_output=True,
        text=True,
        env=env,
        cwd=repo_root,
    )

    assert result.stdout.strip() == "False"
