# -*- coding: utf-8 -*-
"""Abstract filesystem base class for logical backends."""
from __future__ import annotations

from typing import TYPE_CHECKING, Sequence

from agentscope.module import StateModule

from ._types import EntryMeta, Grant, Path

if TYPE_CHECKING:
    from ._handle import FsHandle


class FileSystemBase(StateModule):
    """Abstract base class for logical filesystem backends."""

    def create_handle(self, grants: Sequence[Grant]) -> "FsHandle":
        """Create a handle enforcing the provided grants."""
        from ._handle import FsHandle as FsHandleCls

        return FsHandleCls(self, list(grants))

    def _snapshot_impl(self, grants: Sequence[Grant]) -> dict[Path, EntryMeta]:
        """Return visible entry metadata keyed by logical path."""
        raise NotImplementedError

    def _read_binary_impl(self, path: Path) -> bytes:
        """Read raw bytes from a logical path."""
        raise NotImplementedError

    def _read_file_impl(
        self,
        path: Path,
        *,
        index: int | None,
        line: int | None,
    ) -> str:
        """Read textual content from a logical path."""
        raise NotImplementedError

    def _read_re_impl(
        self,
        path: Path,
        pattern: str,
        overlap: int | None,
    ) -> list[str]:
        """Read regex matches from a logical path."""
        raise NotImplementedError

    def _write_impl(
        self,
        path: Path,
        data: bytes | str,
        overwrite: bool,
    ) -> EntryMeta:
        """Write bytes or text to a logical path."""
        raise NotImplementedError

    def _delete_impl(self, path: Path) -> None:
        """Delete a logical path."""
        raise NotImplementedError
