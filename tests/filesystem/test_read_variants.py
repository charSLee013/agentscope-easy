# -*- coding: utf-8 -*-
"""Argument validation and read variants for handles."""
from __future__ import annotations

import pytest

from agentscope.filesystem import (
    FsHandle,
    InMemoryFileSystem,
    InvalidArgumentError,
)


ALL_OPS = {
    "list",
    "file",
    "read_binary",
    "read_file",
    "read_re",
    "write",
    "delete",
}


def _handle() -> tuple[InMemoryFileSystem, FsHandle]:
    fs = InMemoryFileSystem()
    handle = fs.create_handle(
        [{"prefix": "/workspace/", "ops": set(ALL_OPS)}],
    )
    return fs, handle


def test_invalid_arguments_raise() -> None:
    """Negative indices and overlaps should fail fast."""
    _, handle = _handle()
    handle.write("/workspace/sample.txt", "content")

    with pytest.raises(InvalidArgumentError):
        handle.read_file("/workspace/sample.txt", index=-1)

    with pytest.raises(InvalidArgumentError):
        handle.read_file("/workspace/sample.txt", line=0)

    with pytest.raises(InvalidArgumentError):
        handle.read_re("/workspace/sample.txt", r"sample", overlap=-1)


def test_text_and_binary_round_trip() -> None:
    """Text and binary reads should agree on persisted content."""
    _, handle = _handle()
    handle.write("/workspace/data.txt", "alpha\nbravo\ncharlie")

    assert handle.read_file("/workspace/data.txt") == "alpha\nbravo\ncharlie"
    assert (
        handle.read_binary("/workspace/data.txt") == b"alpha\nbravo\ncharlie"
    )


def test_write_rejects_non_text_binary() -> None:
    """Only bytes and strings are accepted write payloads."""
    _, handle = _handle()
    with pytest.raises(InvalidArgumentError):
        handle.write("/workspace/blob.bin", 3.14)  # type: ignore[arg-type]
