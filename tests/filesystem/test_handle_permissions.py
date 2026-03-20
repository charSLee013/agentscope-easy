# -*- coding: utf-8 -*-
"""Permission enforcement for filesystem handles."""
from __future__ import annotations

import pytest

from agentscope.filesystem import AccessDeniedError, InMemoryFileSystem


ALL_READ = {"list", "file", "read_binary", "read_file", "read_re"}


def test_handle_permissions_union_and_denials() -> None:
    """Workspace grants allow writes while userinput stays read-only."""
    fs = InMemoryFileSystem()
    handle = fs.create_handle(
        [
            {"prefix": "/userinput/", "ops": set(ALL_READ)},
            {
                "prefix": "/workspace/",
                "ops": set(ALL_READ) | {"write", "delete"},
            },
        ],
    )

    handle.write("/workspace/a.txt", "data")
    assert handle.read_file("/workspace/a.txt") == "data"
    handle.delete("/workspace/a.txt")

    with pytest.raises(AccessDeniedError):
        handle.write("/userinput/a.txt", "nope")
