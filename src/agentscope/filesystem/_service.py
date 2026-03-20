# -*- coding: utf-8 -*-
"""Service layer for the filesystem MVP."""
from __future__ import annotations

from typing import Iterable

from ._errors import AccessDeniedError, InvalidArgumentError, NotFoundError
from ._handle import FsHandle, validate_path
from ._tools import (
    delete_file,
    edit_file,
    fs_describe_permissions_markdown,
    get_file_info,
    list_allowed_directories,
    list_directory,
    read_multiple_files,
    read_text_file,
    write_file,
)
from ._types import EntryMeta


_USERINPUT_PREFIX = "/userinput/"
_WORKSPACE_PREFIX = "/workspace/"
_INTERNAL_PREFIX = "/internal/"


class FileDomainService:
    """Policy-aware service wrapper over a granted filesystem handle."""

    def __init__(self, handle: FsHandle) -> None:
        self._handle = handle

    def list_directory(self, path: str) -> list[str]:
        """List immediate children under a logical directory."""
        prefix = path if path.endswith("/") else path + "/"
        prefix = validate_path(prefix)
        entries = self._handle.list(prefix)

        seen_dirs: set[str] = set()
        files: set[str] = set()
        for meta in entries:
            rel = meta["path"][len(prefix) :]
            if not rel:
                continue
            if "/" in rel:
                seen_dirs.add(rel.split("/", 1)[0] + "/")
            else:
                files.add(rel)

        return [f"[DIR] {item}" for item in sorted(seen_dirs)] + [
            f"[FILE] {item}" for item in sorted(files)
        ]

    def get_file_info(self, path: str) -> EntryMeta:
        """Return metadata for a logical file."""
        return self._handle.file(path)

    def list_allowed_directories(self) -> list[str]:
        """Return externally discoverable logical roots."""
        allowed = []
        grants = getattr(self._handle, "_grants", [])
        prefixes = {grant["prefix"] for grant in grants}
        for prefix in (_USERINPUT_PREFIX, _WORKSPACE_PREFIX):
            if prefix in prefixes:
                allowed.append(prefix)
        return allowed

    def read_text_file(
        self,
        path: str,
        start_line: int | None = 1,
        read_lines: int | None = None,
    ) -> str:
        """Read text from a logical file."""
        if start_line is not None and start_line < 1:
            raise InvalidArgumentError("start_line", value=start_line)
        if read_lines is not None and read_lines <= 0:
            raise InvalidArgumentError("read_lines", value=read_lines)

        text = self._handle.read_file(path)
        lines = text.splitlines()
        start = (start_line or 1) - 1
        end = start + read_lines if read_lines is not None else len(lines)
        return "\n".join(lines[start:end])

    def read_multiple_files(self, paths: Iterable[str]) -> list[dict]:
        """Read multiple logical files with per-item success metadata."""
        items: list[dict] = []
        for path in paths:
            try:
                content = self.read_text_file(path)
                items.append({"path": path, "ok": True, "content": content})
            except Exception as exc:  # noqa: BLE001
                items.append({"path": path, "ok": False, "error": str(exc)})
        return items

    def write_file(self, path: str, content: str) -> EntryMeta:
        """Write text to a logical file following the Phase 1 policy."""
        self._assert_writable(path)
        return self._handle.write(path, content, overwrite=True)

    def edit_file(self, path: str, edits: list[dict]) -> EntryMeta:
        """Apply ordered textual replacements and overwrite the file."""
        self._assert_writable(path)
        text = self._handle.read_file(path)
        for edit in edits:
            text = text.replace(edit["oldText"], edit["newText"])
        return self._handle.write(path, text, overwrite=True)

    def delete_file(self, path: str) -> None:
        """Delete a logical file following the Phase 1 policy."""
        domain = self._domain_of(path)
        if domain in (_USERINPUT_PREFIX, _INTERNAL_PREFIX):
            raise AccessDeniedError(path, "delete")
        self._handle.delete(path)

    def describe_permissions_markdown(self) -> str:
        """Return the handle's human-readable grants summary."""
        return self._handle.describe_grants_markdown()

    def tool_functions(self) -> tuple:
        """Return the Phase 1 tool surface for Toolkit wiring."""
        return (
            read_text_file,
            read_multiple_files,
            list_directory,
            get_file_info,
            list_allowed_directories,
            write_file,
            delete_file,
            edit_file,
            fs_describe_permissions_markdown,
        )

    def _assert_writable(self, path: str) -> None:
        domain = self._domain_of(path)
        if domain == _USERINPUT_PREFIX:
            raise AccessDeniedError(path, "write")

    def _domain_of(self, path: str) -> str:
        logical_path = validate_path(path)
        if logical_path.startswith(_USERINPUT_PREFIX):
            return _USERINPUT_PREFIX
        if logical_path.startswith(_WORKSPACE_PREFIX):
            return _WORKSPACE_PREFIX
        if logical_path.startswith(_INTERNAL_PREFIX):
            return _INTERNAL_PREFIX
        raise NotFoundError(logical_path)
