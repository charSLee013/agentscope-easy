# -*- coding: utf-8 -*-
"""In-memory backend roundtrip behavior."""
from __future__ import annotations

from agentscope.filesystem import InMemoryFileSystem


def test_inmemory_basic_roundtrip_and_regex() -> None:
    """The in-memory backend should support text, bytes, slices, and regex."""
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

    content = "alpha\nbravo\nalpha bravo\n"
    handle.write("/workspace/t.txt", content)
    assert handle.read_binary("/workspace/t.txt").decode("utf-8") == content
    assert handle.read_file("/workspace/t.txt", index=1, line=1) == "bravo"
    assert handle.read_re("/workspace/t.txt", r"alpha") == ["alpha", "alpha"]

    handle.delete("/workspace/t.txt")
