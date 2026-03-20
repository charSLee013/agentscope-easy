# -*- coding: utf-8 -*-
# pylint: disable=protected-access
"""Unit tests for MCP helper contracts."""
from datetime import timedelta
import inspect
from types import SimpleNamespace
from unittest import IsolatedAsyncioTestCase
from unittest.mock import AsyncMock

import mcp.types

from agentscope.mcp import HttpStatelessClient, StatefulClientBase
from agentscope.mcp._client_base import MCPClientBase


class DummyStatefulClient(StatefulClientBase):
    """Tiny stateful client probe for contract tests."""

    def __init__(self) -> None:
        super().__init__(name="dummy")


class MCPClientContractTest(IsolatedAsyncioTestCase):
    """Contract tests for MCP timeout and cleanup helpers."""

    @staticmethod
    def _tool(name: str = "tool_1") -> mcp.types.Tool:
        return mcp.types.Tool(
            name=name,
            description="A test MCP tool.",
            inputSchema={"type": "object", "properties": {}},
        )

    def test_mcp_client_base_signature_exposes_execution_timeout(self) -> None:
        """The abstract MCP client contract should expose execution timeout."""
        signature = inspect.signature(MCPClientBase.get_callable_function)
        self.assertIn("execution_timeout", signature.parameters)

    async def test_stateful_get_callable_function_carries_timeout(
        self,
    ) -> None:
        """Stateful clients should forward execution timeout."""
        client = DummyStatefulClient()
        client.is_connected = True
        client.session = AsyncMock()
        client._cached_tools = [self._tool()]

        func = await client.get_callable_function(
            "tool_1",
            execution_timeout=2.5,
        )

        self.assertEqual(func.timeout, timedelta(seconds=2.5))

    async def test_http_stateless_get_callable_function_carries_timeout(
        self,
    ) -> None:
        """Stateless clients should also forward execution timeout."""
        client = HttpStatelessClient(
            name="dummy",
            transport="streamable_http",
            url="http://127.0.0.1:1/mcp",
        )
        client._tools = [self._tool()]

        func = await client.get_callable_function(
            "tool_1",
            execution_timeout=1.25,
        )

        self.assertEqual(func.timeout, timedelta(seconds=1.25))

    async def test_zero_execution_timeout_is_preserved(self) -> None:
        """A zero timeout should remain an explicit zero-duration contract."""
        client = DummyStatefulClient()
        client.is_connected = True
        client.session = AsyncMock()
        client._cached_tools = [self._tool()]

        func = await client.get_callable_function(
            "tool_1",
            execution_timeout=0,
        )

        self.assertEqual(func.timeout, timedelta(seconds=0))

    async def test_stateful_close_can_raise_or_swallow_cleanup_errors(
        self,
    ) -> None:
        """Cleanup should obey the ignore_errors switch."""
        client = DummyStatefulClient()
        client.is_connected = True
        client.stack = SimpleNamespace(
            aclose=AsyncMock(side_effect=RuntimeError("boom")),
        )
        client.session = AsyncMock()

        with self.assertRaises(RuntimeError):
            await client.close(ignore_errors=False)

        client.is_connected = True
        client.stack = SimpleNamespace(
            aclose=AsyncMock(side_effect=RuntimeError("boom")),
        )
        client.session = AsyncMock()

        await client.close(ignore_errors=True)
        self.assertFalse(client.is_connected)
        self.assertIsNone(client.stack)
        self.assertIsNone(client.session)
