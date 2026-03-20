# -*- coding: utf-8 -*-
"""Core type definitions for the filesystem MVP."""
from __future__ import annotations

from datetime import datetime
from typing import Literal, TypedDict


Path = str

Operation = Literal[
    "list",
    "file",
    "read_binary",
    "read_file",
    "read_re",
    "write",
    "delete",
]


class Grant(TypedDict):
    """Authority record describing allowed operations for a path prefix."""

    prefix: Path
    ops: set[Operation]


class _EntryMetaRequired(TypedDict):
    """Minimum metadata describing a filesystem entry."""

    path: Path


class EntryMeta(_EntryMetaRequired, total=False):
    """Optional metadata fields for filesystem entries."""

    size: int
    updated_at: datetime | str | None
