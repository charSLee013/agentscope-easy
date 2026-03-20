# -*- coding: utf-8 -*-
"""Filesystem MVP exports."""

from ._types import EntryMeta, Grant, Operation, Path
from ._errors import (
    AccessDeniedError,
    ConflictError,
    FileSystemError,
    InvalidArgumentError,
    InvalidPathError,
    NotFoundError,
)
from ._base import FileSystemBase
from ._handle import FsHandle, validate_path
from ._memory import InMemoryFileSystem
from ._disk import DiskFileSystem
from ._service import FileDomainService
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

__all__ = [
    "Path",
    "Operation",
    "Grant",
    "EntryMeta",
    "FileSystemError",
    "InvalidPathError",
    "AccessDeniedError",
    "NotFoundError",
    "ConflictError",
    "InvalidArgumentError",
    "FileSystemBase",
    "FsHandle",
    "validate_path",
    "InMemoryFileSystem",
    "DiskFileSystem",
    "FileDomainService",
    "read_text_file",
    "read_multiple_files",
    "list_directory",
    "get_file_info",
    "list_allowed_directories",
    "write_file",
    "delete_file",
    "edit_file",
    "fs_describe_permissions_markdown",
]
