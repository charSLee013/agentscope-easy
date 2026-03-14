# -*- coding: utf-8 -*-
"""Unit tests for ReMe long-term memory classes."""
import json
import sys
import types
import unittest
from typing import Any
from unittest.async_case import IsolatedAsyncioTestCase
from unittest.mock import AsyncMock, MagicMock, patch

from agentscope.embedding import DashScopeTextEmbedding, OpenAITextEmbedding
from agentscope.memory import (
    ReMePersonalLongTermMemory,
    ReMeTaskLongTermMemory,
    ReMeToolLongTermMemory,
)
from agentscope.message import Msg, TextBlock, ThinkingBlock
from agentscope.model import DashScopeChatModel, OpenAIChatModel
from agentscope.tool import ToolResponse


class _FakeReMeApp:
    """Small async context stub replacing the external reme_ai dependency."""

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        self.args = args
        self.kwargs = kwargs

    async def __aenter__(self) -> "_FakeReMeApp":
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        return None


def _fake_reme_module() -> types.SimpleNamespace:
    """Build a fake `reme_ai` module object."""
    return types.SimpleNamespace(ReMeApp=_FakeReMeApp)


class ReMeMemoryTest(IsolatedAsyncioTestCase):
    """Tests for ReMe long-term memory public behavior."""

    def setUp(self) -> None:
        self.mock_dashscope_model = MagicMock(spec=DashScopeChatModel)
        self.mock_dashscope_model.model_name = "qwen3-max"
        self.mock_dashscope_model.api_key = "dash-key"

        self.mock_dashscope_embedding = MagicMock(spec=DashScopeTextEmbedding)
        self.mock_dashscope_embedding.model_name = "text-embedding-v4"
        self.mock_dashscope_embedding.api_key = "embed-key"
        self.mock_dashscope_embedding.dimensions = 1024

        self.mock_openai_model = MagicMock(spec=OpenAIChatModel)
        self.mock_openai_model.model_name = "gpt-4o-mini"
        self.mock_openai_model.client = types.SimpleNamespace(
            base_url="https://api.openai.com/v1",
            api_key="openai-key",
        )

        self.mock_openai_embedding = MagicMock(spec=OpenAITextEmbedding)
        self.mock_openai_embedding.model_name = "text-embedding-3-small"
        self.mock_openai_embedding.dimensions = 1024
        self.mock_openai_embedding.client = types.SimpleNamespace(
            base_url="https://api.openai.com/v1",
            api_key="embed-openai-key",
        )

    def _make_memory(
        self,
        memory_class,
        *,
        model=None,
        embedding_model=None,
    ):
        """Create a memory instance with fake reme module injection."""
        with patch.dict(sys.modules, {"reme_ai": _fake_reme_module()}):
            return memory_class(
                agent_name="TestAgent",
                user_name="workspace-1",
                model=model or self.mock_dashscope_model,
                embedding_model=(
                    embedding_model or self.mock_dashscope_embedding
                ),
            )

    def _start_memory(self, memory_class):
        """Create a started memory instance with mocked async app."""
        memory = self._make_memory(memory_class)
        memory.app = AsyncMock()
        memory._app_started = True
        return memory

    async def test_base_initializes_for_dashscope_and_openai(self) -> None:
        """Base wiring should accept both DashScope and OpenAI pairs."""
        dash_memory = self._make_memory(ReMePersonalLongTermMemory)
        openai_memory = self._make_memory(
            ReMePersonalLongTermMemory,
            model=self.mock_openai_model,
            embedding_model=self.mock_openai_embedding,
        )

        self.assertEqual(dash_memory.workspace_id, "workspace-1")
        self.assertEqual(openai_memory.workspace_id, "workspace-1")
        self.assertEqual(
            openai_memory.app.kwargs["embedding_api_base"],
            "https://api.openai.com/v1",
        )

    async def test_context_manager_marks_app_started(self) -> None:
        """Async context manager should toggle app started state."""
        memory = self._make_memory(ReMePersonalLongTermMemory)

        self.assertFalse(memory._app_started)
        async with memory as entered:
            self.assertIs(entered, memory)
            self.assertTrue(memory._app_started)
        self.assertFalse(memory._app_started)

    async def test_personal_record_and_retrieve_flow(self) -> None:
        """Personal memory should record and retrieve through ReMe app."""
        memory = self._start_memory(ReMePersonalLongTermMemory)
        memory.app.async_execute = AsyncMock(
            side_effect=[
                {"metadata": {"memory_list": [{"content": "one"}]}},
                {"answer": "Prefers Hangzhou homestays."},
            ],
        )

        record_result = await memory.record_to_memory(
            thinking="remember preference",
            content=["User prefers Hangzhou homestays"],
        )
        retrieve_result = await memory.retrieve_from_memory(
            keywords=["Hangzhou"],
        )

        self.assertIsInstance(record_result, ToolResponse)
        self.assertIn("Successfully recorded 1", record_result.content[0]["text"])
        self.assertIn("Hangzhou", retrieve_result.content[0]["text"])

    async def test_task_record_and_retrieve_flow(self) -> None:
        """Task memory should store and retrieve task experiences."""
        memory = self._start_memory(ReMeTaskLongTermMemory)
        memory.app.async_execute = AsyncMock(
            side_effect=[
                {"status": "ok"},
                {"answer": "Keyword 'Python':\nUse EXPLAIN ANALYZE first."},
            ],
        )

        record_result = await memory.record_to_memory(
            thinking="remember tactic",
            content=["Use EXPLAIN ANALYZE before indexing."],
        )
        retrieve_result = await memory.retrieve_from_memory(
            keywords=["Python"],
        )

        self.assertIn("Successfully recorded 1 task", record_result.content[0]["text"])
        self.assertIn("EXPLAIN ANALYZE", retrieve_result.content[0]["text"])

    async def test_tool_record_and_retrieve_flow(self) -> None:
        """Tool memory should parse JSON events and retrieve guidance."""
        memory = self._start_memory(ReMeToolLongTermMemory)
        memory.app.async_execute = AsyncMock(
            side_effect=[
                {"status": "ok"},
                {"status": "ok"},
                {"answer": "Use search_web with concise keywords."},
            ],
        )
        content = [
            json.dumps(
                {
                    "create_time": "2025-01-01T12:00:00",
                    "tool_name": "search_web",
                    "input": {"query": "hangzhou"},
                    "output": "ok",
                    "token_cost": 10,
                    "success": True,
                    "time_cost": 0.3,
                },
            ),
        ]

        record_result = await memory.record_to_memory(
            thinking="remember tool use",
            content=content,
        )
        retrieve_result = await memory.retrieve_from_memory(
            keywords=["search_web"],
        )

        self.assertIn("Successfully recorded 1 tool execution", record_result.content[0]["text"])
        self.assertIn("search_web", retrieve_result.content[0]["text"])

    async def test_tool_record_returns_friendly_message_for_invalid_json(
        self,
    ) -> None:
        """Tool memory should not explode on invalid JSON strings."""
        memory = self._start_memory(ReMeToolLongTermMemory)

        with self.assertWarns(UserWarning):
            result = await memory.record_to_memory(
                thinking="bad tool output",
                content=["not-json"],
            )

        self.assertEqual(
            result.content[0]["text"],
            "No valid tool call results to record.",
        )

    async def test_direct_record_and_retrieve_require_started_context(self) -> None:
        """Direct APIs should fail fast before context start."""
        memory = self._make_memory(ReMePersonalLongTermMemory)
        msg = Msg("user", "hello", "user")

        with self.assertRaises(RuntimeError):
            await memory.record([msg])
        with self.assertRaises(RuntimeError):
            await memory.retrieve(msg)

    async def test_direct_record_and_retrieve_work_after_start(self) -> None:
        """Direct APIs should serialize messages and use the right op names."""
        memory = self._start_memory(ReMeTaskLongTermMemory)
        memory.app.async_execute = AsyncMock(
            side_effect=[
                {"status": "ok"},
                {"answer": "Relevant task memory."},
            ],
        )
        msgs = [
            Msg("user", "Plan Hangzhou trip", "user"),
            Msg("assistant", "Let's do it", "assistant"),
        ]

        await memory.record(msgs, score=0.8)
        result = await memory.retrieve(
            Msg("user", "Hangzhou", "user"),
            limit=3,
        )

        self.assertEqual(result, "Relevant task memory.")
        self.assertEqual(memory.app.async_execute.call_args_list[0][1]["name"], "summary_task_memory")
        self.assertEqual(memory.app.async_execute.call_args_list[1][1]["name"], "retrieve_task_memory")

    async def test_personal_branches_and_error_paths(self) -> None:
        """Personal memory should cover no-result and exception branches."""
        memory = self._start_memory(ReMePersonalLongTermMemory)
        memory.app.async_execute = AsyncMock(
            side_effect=[
                {},
                {"answer": ""},
                Exception("personal-record-error"),
                Exception("personal-retrieve-error"),
            ],
        )

        result_no_meta = await memory.record_to_memory(
            thinking="",
            content=["Remember this"],
        )
        result_no_memory = await memory.retrieve_from_memory(
            keywords=["unknown"],
        )
        result_record_error = await memory.record_to_memory(
            thinking="again",
            content=["boom"],
        )
        result_retrieve_error = await memory.retrieve_from_memory(
            keywords=["boom"],
        )

        self.assertEqual(
            result_no_meta.content[0]["text"],
            "Memory recording completed.",
        )
        self.assertEqual(
            result_no_memory.content[0]["text"],
            "No memories found for the given keywords.",
        )
        self.assertIn(
            "personal-record-error",
            result_record_error.content[0]["text"],
        )
        self.assertIn(
            "personal-retrieve-error",
            result_retrieve_error.content[0]["text"],
        )

    async def test_personal_direct_api_edge_cases(self) -> None:
        """Personal direct APIs should handle content blocks and errors."""
        memory = self._start_memory(ReMePersonalLongTermMemory)
        block_msg = Msg(
            "user",
            [
                ThinkingBlock(type="thinking", thinking="plan"),
                TextBlock(type="text", text="execute"),
            ],
            "user",
        )
        memory.app.async_execute = AsyncMock(
            side_effect=[
                {"status": "ok"},
                {"answer": ""},
                Exception("record-failed"),
                Exception("retrieve-failed"),
            ],
        )

        await memory.record([block_msg])
        empty_result = await memory.retrieve(block_msg)
        with self.assertWarns(UserWarning):
            await memory.record([block_msg])
        with self.assertWarns(UserWarning):
            warned_result = await memory.retrieve(block_msg)

        self.assertEqual(empty_result, "")
        self.assertEqual(warned_result, "")
        with self.assertRaises(TypeError):
            await memory.record(["bad"])
        with self.assertRaises(TypeError):
            await memory.retrieve("bad")
        stopped = self._make_memory(ReMePersonalLongTermMemory)
        with self.assertRaises(RuntimeError):
            await stopped.record([block_msg])
        with self.assertRaises(RuntimeError):
            await stopped.retrieve(block_msg)
        self.assertEqual(await memory.retrieve(None), "")

    async def test_task_branches_and_error_paths(self) -> None:
        """Task memory should cover no-result and exception branches."""
        memory = self._start_memory(ReMeTaskLongTermMemory)
        memory.app.async_execute = AsyncMock(
            side_effect=[
                {"status": "ok"},
                {"answer": ""},
                Exception("task-record-error"),
                Exception("task-retrieve-error"),
            ],
        )

        ok_result = await memory.record_to_memory(
            thinking="",
            content=["Task step"],
        )
        no_result = await memory.retrieve_from_memory(["unknown"])
        error_record = await memory.record_to_memory(
            thinking="x",
            content=["y"],
        )
        error_retrieve = await memory.retrieve_from_memory(["boom"])

        self.assertIn("Successfully recorded 1 task", ok_result.content[0]["text"])
        self.assertEqual(
            no_result.content[0]["text"],
            "No task experiences found for the given keywords.",
        )
        self.assertIn("task-record-error", error_record.content[0]["text"])
        self.assertIn("task-retrieve-error", error_retrieve.content[0]["text"])

    async def test_task_direct_api_edge_cases(self) -> None:
        """Task direct APIs should handle no-query and warning paths."""
        memory = self._start_memory(ReMeTaskLongTermMemory)
        block_msg = Msg(
            "user",
            [
                ThinkingBlock(type="thinking", thinking="inspect"),
                TextBlock(type="text", text="logs"),
            ],
            "user",
        )
        empty_msg = Msg("user", [], "user")
        memory.app.async_execute = AsyncMock(
            side_effect=[
                {"status": "ok"},
                {"answer": "task answer"},
                Exception("task-record-direct-error"),
                Exception("task-retrieve-direct-error"),
            ],
        )

        await memory.record(block_msg, score=0.5)
        self.assertEqual(await memory.retrieve(block_msg), "task answer")
        self.assertEqual(await memory.retrieve(empty_msg), "")
        with self.assertWarns(UserWarning):
            await memory.record(block_msg)
        with self.assertWarns(UserWarning):
            result = await memory.retrieve(block_msg)
        self.assertEqual(result, "")
        with self.assertRaises(TypeError):
            await memory.record(["bad"])
        with self.assertRaises(TypeError):
            await memory.retrieve("bad")
        stopped = self._make_memory(ReMeTaskLongTermMemory)
        with self.assertRaises(RuntimeError):
            await stopped.record([block_msg])
        with self.assertRaises(RuntimeError):
            await stopped.retrieve(block_msg)
        with self.assertRaises(RuntimeError):
            await stopped.record_to_memory("x", ["y"])
        with self.assertRaises(RuntimeError):
            await stopped.retrieve_from_memory(["y"])

    async def test_tool_branches_and_error_paths(self) -> None:
        """Tool memory should cover no-result and exception branches."""
        memory = self._start_memory(ReMeToolLongTermMemory)
        payload = json.dumps(
            {
                "create_time": "2025-01-01T12:00:00",
                "tool_name": "search_web",
                "input": {"query": "x"},
                "output": "ok",
                "token_cost": 1,
                "success": True,
                "time_cost": 0.1,
            },
        )
        memory.app.async_execute = AsyncMock(
            side_effect=[
                {"status": "ok"},
                {"status": "ok"},
                {"answer": ""},
                Exception("tool-record-error"),
                Exception("tool-retrieve-error"),
            ],
        )

        ok_result = await memory.record_to_memory("why", [payload])
        no_result = await memory.retrieve_from_memory(["missing"])
        error_record = await memory.record_to_memory("why", [payload])
        error_retrieve = await memory.retrieve_from_memory(["broken"])

        self.assertIn("Successfully recorded 1 tool execution", ok_result.content[0]["text"])
        self.assertEqual(
            no_result.content[0]["text"],
            "No tool guidelines found for: missing",
        )
        self.assertIn("tool-record-error", error_record.content[0]["text"])
        self.assertIn("tool-retrieve-error", error_retrieve.content[0]["text"])

    async def test_tool_direct_api_edge_cases(self) -> None:
        """Tool direct APIs should cover string/dict/empty/warning branches."""
        memory = self._start_memory(ReMeToolLongTermMemory)
        payload = json.dumps(
            {
                "create_time": "2025-01-01T12:00:00",
                "tool_name": "tool_a",
                "input": {"query": "x"},
                "output": "ok",
                "token_cost": 1,
                "success": True,
                "time_cost": 0.1,
            },
        )
        msg = Msg("user", payload, "user")
        empty_msg = Msg("user", [], "user")
        memory.app.async_execute = AsyncMock(
            side_effect=[
                {"status": "ok"},
                {"status": "ok"},
                {"answer": "tool answer"},
                "string answer",
                {"other": "value"},
                Exception("tool-record-direct-error"),
                Exception("tool-retrieve-direct-error"),
            ],
        )

        await memory.record([msg])
        self.assertEqual(await memory.retrieve(msg), "tool answer")
        self.assertEqual(await memory.retrieve(msg), "string answer")
        self.assertEqual(await memory.retrieve(msg), "{'other': 'value'}")
        self.assertEqual(await memory.retrieve(empty_msg), "")
        with self.assertWarns(UserWarning):
            await memory.record([msg])
        with self.assertWarns(UserWarning):
            result = await memory.retrieve(msg)
        self.assertEqual(result, "")
        with self.assertRaises(TypeError):
            await memory.record(["bad"])
        with self.assertRaises(TypeError):
            await memory.retrieve("bad")
        stopped = self._make_memory(ReMeToolLongTermMemory)
        with self.assertRaises(RuntimeError):
            await stopped.record([msg])
        with self.assertRaises(RuntimeError):
            await stopped.retrieve(msg)
        with self.assertRaises(RuntimeError):
            await stopped.record_to_memory("x", [payload])
        with self.assertRaises(RuntimeError):
            await stopped.retrieve_from_memory(["tool_a"])

    async def test_invalid_model_inputs_raise_value_error(self) -> None:
        """Constructor should reject unsupported model and embedding types."""
        with patch.dict(sys.modules, {"reme_ai": _fake_reme_module()}):
            with self.assertRaises(ValueError):
                ReMePersonalLongTermMemory(
                    user_name="workspace",
                    model=object(),
                    embedding_model=self.mock_dashscope_embedding,
                )
            with self.assertRaises(ValueError):
                ReMePersonalLongTermMemory(
                    user_name="workspace",
                    model=self.mock_dashscope_model,
                    embedding_model=object(),
                )

    async def test_missing_reme_dependency_raises_import_error(self) -> None:
        """Constructor should surface a clear install hint when import fails."""
        sys.modules.pop("reme_ai", None)
        original_import = __import__

        def _raising_import(name, *args, **kwargs):
            if name == "reme_ai":
                raise ImportError("missing")
            return original_import(name, *args, **kwargs)

        with patch("builtins.__import__", side_effect=_raising_import):
            with self.assertRaises(ImportError) as ctx:
                ReMePersonalLongTermMemory(
                    user_name="workspace",
                    model=self.mock_dashscope_model,
                    embedding_model=self.mock_dashscope_embedding,
                )
        self.assertIn("pip install reme-ai", str(ctx.exception))


if __name__ == "__main__":
    unittest.main()
