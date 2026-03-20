# -*- coding: utf-8 -*-
"""Toolkit integration for filesystem tools."""
from __future__ import annotations

from unittest import IsolatedAsyncioTestCase

from agentscope.filesystem import InMemoryFileSystem
from agentscope.filesystem._service import FileDomainService
from agentscope.filesystem._tools import (
    fs_describe_permissions_markdown,
    list_allowed_directories,
    read_text_file,
    write_file,
)
from agentscope.message import ToolUseBlock
from agentscope.tool import Toolkit


class FilesystemToolTest(IsolatedAsyncioTestCase):
    """Tool-level tests for the filesystem MVP."""

    async def asyncSetUp(self) -> None:
        self.fs = InMemoryFileSystem()
        admin = self.fs.create_handle(
            [
                {
                    "prefix": "/userinput/",
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
                {
                    "prefix": "/internal/",
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
        admin.write("/internal/log.txt", "hello\nworld")
        self.service = FileDomainService(
            self.fs.create_handle(
                [
                    {
                        "prefix": "/userinput/",
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
                    {
                        "prefix": "/internal/",
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
            ),
        )
        self.toolkit = Toolkit()
        for tool in (
            read_text_file,
            write_file,
            list_allowed_directories,
            fs_describe_permissions_markdown,
        ):
            self.toolkit.register_tool_function(
                tool,
                preset_kwargs={"service": self.service},
            )

    async def test_preset_service_argument_is_hidden_from_schema(self) -> None:
        """Toolkit schemas should not expose the injected service argument."""
        schemas = self.toolkit.get_json_schemas()
        schema_by_name = {
            schema["function"]["name"]: schema for schema in schemas
        }

        assert (
            "service"
            not in schema_by_name["read_text_file"]["function"]["parameters"][
                "properties"
            ]
        )
        assert (
            "service"
            not in schema_by_name["write_file"]["function"]["parameters"][
                "properties"
            ]
        )

    async def test_tools_execute_with_service_injection(self) -> None:
        """Filesystem tools should execute successfully through Toolkit."""
        list_dirs = await self.toolkit.call_tool_function(
            ToolUseBlock(
                type="tool_use",
                id="1",
                name="list_allowed_directories",
                input={},
            ),
        )
        chunks = [chunk async for chunk in list_dirs]
        assert chunks[-1].content[0]["text"] == "/userinput/\n/workspace/"

        read_internal = await self.toolkit.call_tool_function(
            ToolUseBlock(
                type="tool_use",
                id="2",
                name="read_text_file",
                input={"path": "/internal/log.txt"},
            ),
        )
        chunks = [chunk async for chunk in read_internal]
        assert "hello" in chunks[-1].content[0]["text"]

        write_workspace = await self.toolkit.call_tool_function(
            ToolUseBlock(
                type="tool_use",
                id="3",
                name="write_file",
                input={"path": "/workspace/out.txt", "content": "payload"},
            ),
        )
        chunks = [chunk async for chunk in write_workspace]
        assert "wrote" in chunks[-1].content[0]["text"]

        permissions = await self.toolkit.call_tool_function(
            ToolUseBlock(
                type="tool_use",
                id="4",
                name="fs_describe_permissions_markdown",
                input={},
            ),
        )
        chunks = [chunk async for chunk in permissions]
        assert "/internal/" in chunks[-1].content[0]["text"]

    async def test_read_text_file_preserves_source_line_numbers(self) -> None:
        """Sliced reads should keep original source line numbers."""
        self.service.write_file(
            "/workspace/numbered.txt",
            "alpha\nbeta\ngamma\ndelta",
        )

        result = await read_text_file(
            service=self.service,
            path="/workspace/numbered.txt",
            start_line=3,
            read_lines=2,
        )

        text = result.content[0]["text"]
        assert "line3: gamma" in text
        assert "line4: delta" in text
