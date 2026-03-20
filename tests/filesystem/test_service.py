# -*- coding: utf-8 -*-
"""Service-layer behavior for the filesystem MVP."""
from __future__ import annotations

import pytest

from agentscope.filesystem import AccessDeniedError, InMemoryFileSystem
from agentscope.filesystem._service import FileDomainService


ALL_OPS = {
    "list",
    "file",
    "read_binary",
    "read_file",
    "read_re",
    "write",
    "delete",
}


def _build_service() -> FileDomainService:
    fs = InMemoryFileSystem()
    admin = fs.create_handle(
        [
            {"prefix": "/userinput/", "ops": set(ALL_OPS)},
            {"prefix": "/internal/", "ops": set(ALL_OPS)},
            {"prefix": "/workspace/", "ops": set(ALL_OPS)},
        ],
    )
    admin.write("/userinput/corpus.txt", "seed corpus")
    admin.write("/internal/run.log", "secret log")

    service_handle = fs.create_handle(
        [
            {"prefix": "/userinput/", "ops": set(ALL_OPS)},
            {"prefix": "/internal/", "ops": set(ALL_OPS)},
            {"prefix": "/workspace/", "ops": set(ALL_OPS)},
        ],
    )
    return FileDomainService(service_handle)


def test_service_hides_internal_from_default_discovery() -> None:
    """The service should not advertise /internal/ by default."""
    svc = _build_service()
    assert svc.list_allowed_directories() == ["/userinput/", "/workspace/"]


def test_service_allows_explicit_internal_reads_and_writes() -> None:
    """Explicit /internal/ access should work when the handle is granted."""
    svc = _build_service()
    assert svc.read_text_file("/internal/run.log") == "secret log"

    meta = svc.write_file("/internal/cache.json", '{"ok": true}')
    assert meta["path"] == "/internal/cache.json"
    assert svc.read_text_file("/internal/cache.json") == '{"ok": true}'


def test_service_enforces_fixed_domain_policy() -> None:
    """Service policy should override permissive handle grants."""
    svc = _build_service()

    with pytest.raises(AccessDeniedError):
        svc.write_file("/userinput/corpus.txt", "overwrite")

    with pytest.raises(AccessDeniedError):
        svc.delete_file("/internal/run.log")

    meta = svc.write_file("/workspace/report.txt", "hello")
    assert meta["path"] == "/workspace/report.txt"
    svc.delete_file("/workspace/report.txt")


def test_service_permissions_markdown_comes_from_handle() -> None:
    """The service should expose the handle's markdown summary."""
    svc = _build_service()
    summary = svc.describe_permissions_markdown()
    assert "/internal/: ls, stat, read, write, delete" in summary
    assert "/workspace/: ls, stat, read, write, delete" in summary
