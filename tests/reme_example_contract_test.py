# -*- coding: utf-8 -*-
"""Contract tests for the ReMe short-term memory example."""
from __future__ import annotations

import asyncio
import importlib.util
from pathlib import Path
from unittest.mock import patch

from agentscope.filesystem import FileDomainService, InMemoryFileSystem


REME_EXAMPLE_PATH = (
    Path(__file__).resolve().parents[1]
    / "examples"
    / "functionality"
    / "short_term_memory"
    / "reme"
    / "short_term_memory_example.py"
)


def _load_reme_example_module():
    """Load the ReMe example module without executing main()."""
    spec = importlib.util.spec_from_file_location(
        "test_reme_short_term_memory_example",
        REME_EXAMPLE_PATH,
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_reme_example_uses_shared_demo_root() -> None:
    """Workspace and offload roots must share the same demo root."""
    module = _load_reme_example_module()
    example_dir = REME_EXAMPLE_PATH.parent

    assert module._workspace_dir().parent == module._demo_root()
    assert module._reme_store_dir().parent == module._workspace_dir()
    assert module._source_readme_path().is_file()
    assert not module._demo_root().is_relative_to(example_dir)


def test_reme_example_import_has_no_runtime_side_effects() -> None:
    """Importing the example must not load env files or create temp dirs."""
    with patch(
        "dotenv.load_dotenv",
        side_effect=AssertionError("load_dotenv should not run on import"),
    ), patch(
        "tempfile.mkdtemp",
        side_effect=AssertionError("mkdtemp should not run on import"),
    ):
        _load_reme_example_module()


def test_seed_workspace_readme_writes_into_logical_workspace() -> None:
    """The sample should seed README through FileDomainService, not host-path open."""
    module = _load_reme_example_module()
    fs = InMemoryFileSystem()
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
    service = FileDomainService(handle)

    text = module._seed_workspace_readme(service)

    assert text
    assert service.read_text_file(module._WORKSPACE_README_PATH) == text


def test_grep_workspace_uses_service_read_re() -> None:
    """The grep helper should search through FileDomainService."""
    module = _load_reme_example_module()
    fs = InMemoryFileSystem()
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
    service = FileDomainService(handle)
    service.write_file("/workspace/sample.txt", "alpha beta alpha")

    result = asyncio.run(
        module._grep_workspace(
            service,
            "/workspace/sample.txt",
            "alpha",
            "2",
        ),
    )

    assert result.content[0]["text"] == "alpha\nalpha"


def test_read_workspace_file_reads_numbered_logical_lines() -> None:
    """The read helper should read logical workspace lines with numbering."""
    module = _load_reme_example_module()
    fs = InMemoryFileSystem()
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
    service = FileDomainService(handle)
    service.write_file("/workspace/sample.txt", "alpha\nbeta\ngamma")

    result = asyncio.run(
        module._read_workspace_file(
            service,
            "/workspace/sample.txt",
            1,
            2,
        ),
    )

    assert result.content[0]["text"] == "line2: beta\nline3: gamma"
