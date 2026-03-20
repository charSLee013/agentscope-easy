# -*- coding: utf-8 -*-
"""Path validation rules for the filesystem MVP."""
import pytest

from agentscope.filesystem import InvalidPathError, validate_path


@pytest.mark.parametrize(
    "path",
    [
        "/workspace/a.txt",
        "/internal/logs/run-1.json",
        "/userinput/corpus.md",
    ],
)
def test_validate_path_accepts_absolute_noncontrol(path: str) -> None:
    """Absolute logical paths should pass unchanged."""
    assert validate_path(path) == path


@pytest.mark.parametrize(
    "path",
    [
        "workspace/a.txt",
        "/workspace/../secret",
        "/workspace/with*wildcard",
        "/workspace/with?query",
        "/workspace/double//slash",
        "/bad\\windows",
        "\x01/ctrl",
    ],
)
def test_validate_path_rejects_invalid_patterns(path: str) -> None:
    """Traversal-like or malformed logical paths should be rejected."""
    with pytest.raises(InvalidPathError):
        validate_path(path)


def test_validate_path_preserves_trailing_space() -> None:
    """Logical paths are strict strings and should not be normalized."""
    path = "/workspace/a "
    assert validate_path(path) == path
