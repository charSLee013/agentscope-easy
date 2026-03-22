# -*- coding: utf-8 -*-
"""Real runtime validation script tests for SubAgent V1."""
from __future__ import annotations

import json
import os
from pathlib import Path
import subprocess
import sys


def test_real_runtime_validation_script_emits_machine_readable_proof(
    tmp_path: Path,
) -> None:
    """The proof script should run and write a durable JSON artifact."""
    repo_root = Path(__file__).resolve().parents[1]
    script = (
        repo_root
        / "specs"
        / "037-subagent-v1-core"
        / "subagent_v1_runtime_validation.py"
    )
    output_dir = tmp_path / "runtime-proof"

    env = os.environ.copy()
    env["PYTHONPATH"] = "src"

    completed = subprocess.run(
        [sys.executable, str(script), "--output-dir", str(output_dir)],
        cwd=repo_root,
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )

    assert completed.returncode == 0, completed.stderr or completed.stdout

    proof_path = output_dir / "proof.json"
    assert proof_path.exists()

    proof = json.loads(proof_path.read_text(encoding="utf-8"))
    assert proof["subagent"] == "task_executor"
    assert proof["tool_trace"] == ["write_file"]
    assert proof["output_text"] == "delegated output"
