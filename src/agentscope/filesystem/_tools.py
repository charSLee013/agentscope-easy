# -*- coding: utf-8 -*-
"""Filesystem tool functions for the filesystem MVP."""
from __future__ import annotations

from agentscope.message import TextBlock
from agentscope.tool import ToolResponse


async def read_text_file(
    service: object,
    path: str,
    start_line: int | None = 1,
    read_lines: int | None = None,
    with_line_numbers: bool | None = True,
    with_header: bool | None = True,
) -> ToolResponse:
    """Read text from a logical file."""
    raw_text = service.read_text_file(
        path,
        start_line=start_line,
        read_lines=read_lines,
    )

    if with_line_numbers:
        lines = raw_text.splitlines()
        line_offset = (start_line or 1) - 1
        numbered = [
            f"line{i}: {line}"
            for i, line in enumerate(lines, start=line_offset + 1)
        ]
        if with_header:
            header = [
                f"line_count: {len(lines)}",
                "format: line{N}: <content>",
            ]
            text_out = "\n".join([*header, *numbered])
        else:
            text_out = "\n".join(numbered)
    else:
        if with_header:
            lines = raw_text.splitlines()
            header = [f"line_count: {len(lines)}", "format: raw"]
            text_out = (
                "\n".join([*header, raw_text])
                if raw_text
                else "\n".join(header)
            )
        else:
            text_out = raw_text

    return ToolResponse(content=[TextBlock(type="text", text=text_out)])


async def read_multiple_files(
    service: object,
    paths: list[str],
    with_line_numbers: bool | None = True,
    with_header: bool | None = True,
) -> ToolResponse:
    """Read multiple logical files."""
    items = service.read_multiple_files(paths)
    sections: list[str] = []
    for item in items:
        path = item.get("path", "<unknown>")
        if item.get("ok"):
            content = item.get("content", "")
            lines = content.splitlines()
            header_parts: list[str] = []
            if with_header:
                header_parts = [
                    f"line_count: {len(lines)}",
                    (
                        "format: line{N}: <content>"
                        if with_line_numbers
                        else "format: raw"
                    ),
                ]

            body = (
                "\n".join(
                    f"line{i}: {line}" for i, line in enumerate(lines, start=1)
                )
                if with_line_numbers
                else content
            )

            section = [f"## {path}", *header_parts]
            if body:
                section.append(body)
            sections.append("\n".join(section))
        else:
            sections.append(f"## {path} (error)\n{item.get('error', '')}")

    return ToolResponse(
        content=[
            TextBlock(type="text", text="\n\n".join(sections) or "<empty>"),
        ],
    )


async def list_directory(service: object, path: str) -> ToolResponse:
    """List immediate children of a logical directory."""
    lines = service.list_directory(path)
    return ToolResponse(
        content=[TextBlock(type="text", text="\n".join(lines) or "<empty>")],
    )


async def get_file_info(service: object, path: str) -> ToolResponse:
    """Return metadata for a logical file."""
    meta = service.get_file_info(path)
    payload = "\n".join(f"{key}: {value}" for key, value in meta.items())
    return ToolResponse(content=[TextBlock(type="text", text=payload)])


async def list_allowed_directories(service: object) -> ToolResponse:
    """List the default discoverable logical roots."""
    directories = service.list_allowed_directories()
    return ToolResponse(
        content=[TextBlock(type="text", text="\n".join(directories))],
    )


async def write_file(service: object, path: str, content: str) -> ToolResponse:
    """Write text to a logical file."""
    meta = service.write_file(path, content)
    text = f"wrote {int(meta.get('size', 0))} bytes to {meta['path']}"
    return ToolResponse(content=[TextBlock(type="text", text=text)])


async def delete_file(service: object, path: str) -> ToolResponse:
    """Delete a logical file."""
    service.delete_file(path)
    return ToolResponse(
        content=[TextBlock(type="text", text=f"deleted {path}")],
    )


async def edit_file(
    service: object,
    path: str,
    edits: list[dict],
) -> ToolResponse:
    """Apply ordered textual replacements then overwrite the file."""
    meta = service.edit_file(path, edits)
    text = f"edited {meta['path']} (size={int(meta.get('size', 0))})"
    return ToolResponse(content=[TextBlock(type="text", text=text)])


async def fs_describe_permissions_markdown(service: object) -> ToolResponse:
    """Summarize the current grants as human-readable markdown."""
    text = service.describe_permissions_markdown()
    return ToolResponse(content=[TextBlock(type="text", text=text)])


__all__ = [
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
