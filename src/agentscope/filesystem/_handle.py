# -*- coding: utf-8 -*-
"""Filesystem handle enforcing path validation and grant checks."""
# pylint: disable=protected-access
from __future__ import annotations

import re
from typing import TYPE_CHECKING, Sequence

from ._errors import (
    AccessDeniedError,
    ConflictError,
    InvalidArgumentError,
    InvalidPathError,
    NotFoundError,
)
from ._types import EntryMeta, Grant, Operation, Path

if TYPE_CHECKING:
    from ._base import FileSystemBase


_CONTROL_CHAR_PATTERN = re.compile(r"[\x00-\x1F]")
_ILLEGAL_SEGMENTS = ("..", "*", "?", "\\")


def _clone_meta(meta: EntryMeta) -> EntryMeta:
    clone: EntryMeta = {"path": meta["path"]}
    if "size" in meta:
        clone["size"] = meta["size"]
    if "updated_at" in meta:
        clone["updated_at"] = meta["updated_at"]
    return clone


def validate_path(path: Path) -> Path:
    """Validate a logical absolute path."""
    if not isinstance(path, str):
        raise InvalidPathError(str(path))

    if not path.startswith("/"):
        raise InvalidPathError(path)

    if _CONTROL_CHAR_PATTERN.search(path):
        raise InvalidPathError(path)

    if any(segment in path for segment in _ILLEGAL_SEGMENTS):
        raise InvalidPathError(path)

    if "//" in path:
        raise InvalidPathError(path)

    return path


class FsHandle:
    """Authorized view over a filesystem backend."""

    def __init__(
        self,
        filesystem: "FileSystemBase",
        grants: list[Grant],
    ) -> None:
        self._fs = filesystem
        self._grants = list(grants)
        self._index: dict[Path, EntryMeta] = {}
        self._refresh_index()

    def list(self, prefix: Path | None = None) -> list[EntryMeta]:
        """List visible entries, optionally under a prefix."""
        if prefix is not None:
            prefix = validate_path(prefix)
            self._ensure_allowed(prefix, "list")
        else:
            self._ensure_list_capability()

        self._refresh_index()
        collected: list[EntryMeta] = []
        for path_candidate, meta in self._index.items():
            if prefix is not None and not path_candidate.startswith(prefix):
                continue
            collected.append(_clone_meta(meta))
        collected.sort(key=lambda item: item["path"])
        return collected

    def file(self, path: Path) -> EntryMeta:
        """Fetch metadata for a logical file."""
        logical_path = self._ensure_allowed(validate_path(path), "file")
        self._refresh_index()
        meta = self._index.get(logical_path)
        if meta is None:
            raise NotFoundError(logical_path)
        return _clone_meta(meta)

    def read_binary(self, path: Path) -> bytes:
        """Read bytes from a logical file."""
        logical_path = self._ensure_allowed(validate_path(path), "read_binary")
        self._refresh_index()
        self._ensure_exists(logical_path)
        return self._fs._read_binary_impl(logical_path)

    def read_file(
        self,
        path: Path,
        *,
        index: int | None = None,
        line: int | None = None,
    ) -> str:
        """Read text from a logical file with optional slicing."""
        logical_path = self._ensure_allowed(validate_path(path), "read_file")
        if index is not None and index < 0:
            raise InvalidArgumentError("index", value=index)
        if line is not None and line <= 0:
            raise InvalidArgumentError("line", value=line)

        self._refresh_index()
        self._ensure_exists(logical_path)
        return self._fs._read_file_impl(
            logical_path,
            index=index,
            line=line,
        )

    def read_re(
        self,
        path: Path,
        pattern: str,
        *,
        overlap: int | None = None,
    ) -> Sequence[str]:
        """Read regex matches from a logical file."""
        logical_path = self._ensure_allowed(validate_path(path), "read_re")
        if overlap is not None and overlap < 0:
            raise InvalidArgumentError("overlap", value=overlap)

        self._refresh_index()
        self._ensure_exists(logical_path)
        return self._fs._read_re_impl(logical_path, pattern, overlap)

    def write(
        self,
        path: Path,
        data: bytes | str,
        *,
        overwrite: bool = True,
    ) -> EntryMeta:
        """Write bytes or text to a logical file."""
        logical_path = self._ensure_allowed(validate_path(path), "write")
        if not isinstance(data, (bytes, str)):
            raise InvalidArgumentError("data", value=type(data).__name__)

        self._refresh_index()
        if not overwrite and logical_path in self._index:
            raise ConflictError(logical_path)

        meta = self._fs._write_impl(logical_path, data, overwrite)
        self._refresh_index()
        return _clone_meta(meta)

    def delete(self, path: Path) -> None:
        """Delete a logical file."""
        logical_path = self._ensure_allowed(validate_path(path), "delete")
        self._refresh_index()
        self._ensure_exists(logical_path)
        self._fs._delete_impl(logical_path)
        self._refresh_index()

    def describe_grants_markdown(self) -> str:
        """Return a compact human-readable grants summary."""
        per_prefix: dict[str, set[str]] = {}
        for grant in self._grants:
            prefix = grant["prefix"]
            ops = per_prefix.setdefault(prefix, set())
            ops.update(grant.get("ops", set()))

        def _tokens(ops: set[str]) -> list[str]:
            items: list[str] = []
            if "list" in ops:
                items.append("ls")
            if "file" in ops:
                items.append("stat")
            if any(
                operation in ops
                for operation in ("read_file", "read_binary", "read_re")
            ):
                items.append("read")
            if "write" in ops:
                items.append("write")
            if "delete" in ops:
                items.append("delete")
            return items

        lines: list[str] = []
        for prefix in sorted(per_prefix):
            items = _tokens(per_prefix[prefix])
            line = f"{prefix}: {', '.join(items)}" if items else f"{prefix}:"
            lines.append(line)
        return "\n".join(lines)

    def _refresh_index(self) -> None:
        self._index = self._fs._snapshot_impl(self._grants)

    def _ensure_exists(self, path: Path) -> None:
        if path not in self._index:
            raise NotFoundError(path)

    def _ensure_allowed(self, path: Path, operation: Operation) -> Path:
        allowed_ops = self._collect_ops(path)
        if operation not in allowed_ops:
            raise AccessDeniedError(path, operation)
        return path

    def _collect_ops(self, path: Path) -> set[Operation]:
        allowed: set[Operation] = set()
        for grant in self._grants:
            if path.startswith(grant["prefix"]):
                allowed.update(grant["ops"])
        return allowed

    def _ensure_list_capability(self) -> None:
        if not any("list" in grant["ops"] for grant in self._grants):
            raise AccessDeniedError("/", "list")


__all__ = ["FsHandle", "validate_path"]
