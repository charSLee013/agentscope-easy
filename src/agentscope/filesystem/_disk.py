# -*- coding: utf-8 -*-
"""Disk-backed filesystem for the filesystem MVP."""
from __future__ import annotations

import os
import re
from datetime import datetime, timezone
from typing import Sequence

from ._base import FileSystemBase
from ._errors import ConflictError, NotFoundError
from ._handle import validate_path
from ._types import EntryMeta, Grant, Path


_INTERNAL_PREFIX = "/internal/"
_USERINPUT_PREFIX = "/userinput/"
_WORKSPACE_PREFIX = "/workspace/"
_RE_PATH_SEP = re.compile(r"\\+")


def _norm_join(base_dir: str, *parts: str) -> str:
    return os.path.abspath(os.path.join(base_dir, *parts))


class DiskFileSystem(FileSystemBase):
    """Disk-backed filesystem using a fixed three-root logical layout."""

    def __init__(
        self,
        *,
        root_dir: str | None = None,
        internal_dir: str | None = None,
        userinput_dir: str | None = None,
        workspace_dir: str | None = None,
    ) -> None:
        super().__init__()
        if root_dir is None:
            stamp = datetime.now().strftime("%m%d%H%M%S")
            base = os.path.abspath(os.path.join(os.getcwd(), "output", stamp))
        else:
            base = os.path.abspath(root_dir)

        self._root_dir = base
        self._internal_dir = os.path.abspath(
            internal_dir or os.path.join(base, "internal"),
        )
        self._userinput_dir = os.path.abspath(
            userinput_dir or os.path.join(base, "userinput"),
        )
        self._workspace_dir = os.path.abspath(
            workspace_dir or os.path.join(base, "workspace"),
        )

        os.makedirs(self._internal_dir, exist_ok=True)
        os.makedirs(self._userinput_dir, exist_ok=True)
        os.makedirs(self._workspace_dir, exist_ok=True)

    def _split_namespace(self, path: Path) -> tuple[str, str]:
        validate_path(path)
        if path.startswith(_INTERNAL_PREFIX):
            return _INTERNAL_PREFIX, path[len(_INTERNAL_PREFIX) :]
        if path.startswith(_USERINPUT_PREFIX):
            return _USERINPUT_PREFIX, path[len(_USERINPUT_PREFIX) :]
        if path.startswith(_WORKSPACE_PREFIX):
            return _WORKSPACE_PREFIX, path[len(_WORKSPACE_PREFIX) :]
        raise NotFoundError(path)

    def _ns_root(self, prefix: str) -> str:
        if prefix == _INTERNAL_PREFIX:
            return self._internal_dir
        if prefix == _USERINPUT_PREFIX:
            return self._userinput_dir
        return self._workspace_dir

    def _to_os_path(self, path: Path) -> str:
        prefix, rel = self._split_namespace(path)
        rel_norm = _RE_PATH_SEP.sub("/", rel).lstrip("/")
        pieces = rel_norm.split("/") if rel_norm else []
        return _norm_join(self._ns_root(prefix), *pieces)

    def _iter_visible_under(
        self,
        prefix: str,
        base_dir: str,
    ) -> dict[Path, EntryMeta]:
        view: dict[Path, EntryMeta] = {}
        for root, _dirs, files in os.walk(base_dir):
            for filename in files:
                abs_path = os.path.join(root, filename)
                rel = os.path.relpath(abs_path, base_dir).replace(os.sep, "/")
                logical = prefix + rel if rel else prefix
                stat = os.stat(abs_path)
                view[logical] = {
                    "path": logical,
                    "size": int(stat.st_size),
                    "updated_at": datetime.fromtimestamp(
                        stat.st_mtime,
                        tz=timezone.utc,
                    ).isoformat(),
                }
        return view

    def _snapshot_impl(self, grants: Sequence[Grant]) -> dict[Path, EntryMeta]:
        visible: dict[Path, EntryMeta] = {}
        if not grants:
            prefixes = {_INTERNAL_PREFIX, _USERINPUT_PREFIX, _WORKSPACE_PREFIX}
        else:
            prefixes = set()
            if any(
                grant["prefix"].startswith(_INTERNAL_PREFIX)
                for grant in grants
            ):
                prefixes.add(_INTERNAL_PREFIX)
            if any(
                grant["prefix"].startswith(_USERINPUT_PREFIX)
                for grant in grants
            ):
                prefixes.add(_USERINPUT_PREFIX)
            if any(
                grant["prefix"].startswith(_WORKSPACE_PREFIX)
                for grant in grants
            ):
                prefixes.add(_WORKSPACE_PREFIX)

        if _INTERNAL_PREFIX in prefixes:
            visible.update(
                self._iter_visible_under(_INTERNAL_PREFIX, self._internal_dir),
            )
        if _USERINPUT_PREFIX in prefixes:
            visible.update(
                self._iter_visible_under(
                    _USERINPUT_PREFIX,
                    self._userinput_dir,
                ),
            )
        if _WORKSPACE_PREFIX in prefixes:
            visible.update(
                self._iter_visible_under(
                    _WORKSPACE_PREFIX,
                    self._workspace_dir,
                ),
            )

        if not grants:
            return visible

        return {
            path: meta
            for path, meta in visible.items()
            if any(path.startswith(grant["prefix"]) for grant in grants)
        }

    def _read_binary_impl(self, path: Path) -> bytes:
        os_path = self._to_os_path(path)
        try:
            with open(os_path, "rb") as file:
                return file.read()
        except FileNotFoundError as exc:
            raise NotFoundError(path) from exc

    def _read_file_impl(
        self,
        path: Path,
        *,
        index: int | None,
        line: int | None,
    ) -> str:
        text = self._read_binary_impl(path).decode("utf-8")
        if index is None and line is None:
            return text

        lines = text.splitlines()
        start = index or 0
        end = start + line if line is not None else len(lines)
        return "\n".join(lines[start:end])

    def _read_re_impl(
        self,
        path: Path,
        pattern: str,
        overlap: int | None,
    ) -> list[str]:
        text = self._read_binary_impl(path).decode("utf-8")
        compiled = re.compile(pattern, re.MULTILINE)
        if not overlap:
            return [match.group(0) for match in compiled.finditer(text)]

        matches: list[str] = []
        pos = 0
        while pos <= len(text):
            match = compiled.search(text, pos)
            if not match:
                break
            chunk = match.group(0)
            matches.append(chunk)
            advance = max(1, len(chunk) - int(overlap))
            pos = match.start() + advance
        return matches

    def _write_impl(
        self,
        path: Path,
        data: bytes | str,
        overwrite: bool,
    ) -> EntryMeta:
        os_path = self._to_os_path(path)
        if not overwrite and os.path.exists(os_path):
            raise ConflictError(path)
        os.makedirs(os.path.dirname(os_path), exist_ok=True)
        payload = data.encode("utf-8") if isinstance(data, str) else data
        with open(os_path, "wb") as file:
            file.write(payload)
        stat = os.stat(os_path)
        return {
            "path": path,
            "size": int(stat.st_size),
            "updated_at": datetime.fromtimestamp(
                stat.st_mtime,
                tz=timezone.utc,
            ).isoformat(),
        }

    def _delete_impl(self, path: Path) -> None:
        os_path = self._to_os_path(path)
        try:
            os.remove(os_path)
        except FileNotFoundError as exc:
            raise NotFoundError(path) from exc
