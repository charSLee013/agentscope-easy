# -*- coding: utf-8 -*-
"""Regression tests for example filesystem wiring."""
from __future__ import annotations

import ast
from pathlib import Path


def test_examples_do_not_use_cwd_default_disk_filesystem() -> None:
    """Example DiskFileSystem calls should not create repo output/ dirs."""
    repo_root = Path(__file__).resolve().parents[2]
    offenders: list[str] = []
    for path in (repo_root / "examples").rglob("*.py"):
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if not isinstance(node, ast.Call):
                continue
            if not isinstance(node.func, ast.Name):
                continue
            if node.func.id != "DiskFileSystem":
                continue
            if not any(keyword.arg == "root_dir" for keyword in node.keywords):
                offenders.append(str(path.relative_to(repo_root)))

    assert offenders == []
