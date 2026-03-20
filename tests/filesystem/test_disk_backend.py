# -*- coding: utf-8 -*-
"""Disk-backed filesystem behavior."""
from __future__ import annotations

import os
from pathlib import Path

from agentscope.filesystem import DiskFileSystem


def test_disk_backend_creates_default_tree_and_roundtrip(
    tmp_path: Path,
) -> None:
    """The disk backend should create the default tree and persist files."""
    cwd = os.getcwd()
    os.chdir(tmp_path)
    try:
        fs = DiskFileSystem()
        output_dir = tmp_path / "output"
        roots = list(output_dir.iterdir())
        assert len(roots) == 1
        root = roots[0]
        assert (root / "internal").is_dir()
        assert (root / "userinput").is_dir()
        assert (root / "workspace").is_dir()

        handle = fs.create_handle(
            [
                {
                    "prefix": "/workspace/",
                    "ops": {
                        "list",
                        "file",
                        "read_binary",
                        "read_file",
                        "read_re",
                        "write",
                        "delete",
                    },
                },
            ],
        )
        handle.write("/workspace/report.txt", "hello filesystem")
        assert handle.read_file("/workspace/report.txt") == "hello filesystem"
        handle.delete("/workspace/report.txt")
    finally:
        os.chdir(cwd)


def test_disk_backend_supports_nested_grant_prefixes(
    tmp_path: Path,
) -> None:
    """Nested grant prefixes should still surface matching files."""
    cwd = os.getcwd()
    os.chdir(tmp_path)
    try:
        fs = DiskFileSystem()
        handle = fs.create_handle(
            [
                {
                    "prefix": "/workspace/project/",
                    "ops": {
                        "list",
                        "file",
                        "read_binary",
                        "read_file",
                        "read_re",
                        "write",
                        "delete",
                    },
                },
            ],
        )
        handle.write("/workspace/project/report.txt", "nested grant")
        assert (
            handle.read_file("/workspace/project/report.txt") == "nested grant"
        )
        entries = handle.list("/workspace/project/")
        assert len(entries) == 1
        assert entries[0]["path"] == "/workspace/project/report.txt"
        assert entries[0]["size"] == 12
    finally:
        os.chdir(cwd)
