# -*- coding: utf-8 -*-
"""Regression tests for deep research report path generation."""
from __future__ import annotations

import asyncio
import importlib
import os
import sys
from contextlib import contextmanager
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Iterator
from unittest.mock import AsyncMock, patch

from agentscope.filesystem import validate_path
from agentscope.formatter import DashScopeChatFormatter
from agentscope.memory import InMemoryMemory
from agentscope.message import Msg, TextBlock
from agentscope.model import ChatModelBase, ChatResponse


DEEP_RESEARCH_DIR = (
    Path(__file__).resolve().parents[1]
    / "examples"
    / "agent"
    / "deep_research_agent"
)


@contextmanager
def deep_research_on_path() -> Iterator[None]:
    """Temporarily expose the deep research example package root."""
    sys.path.insert(0, str(DEEP_RESEARCH_DIR))
    try:
        yield
    finally:
        sys.path.remove(str(DEEP_RESEARCH_DIR))


def _load_deep_research_module():
    """Import the deep research example module from its real sample path."""
    with deep_research_on_path():
        importlib.invalidate_caches()
        return importlib.import_module("deep_research_agent")


def test_deep_research_import_has_no_logging_side_effects() -> None:
    """Importing the example module must not create log files."""
    sys.modules.pop("deep_research_agent", None)
    with patch("os.makedirs") as makedirs, patch(
        "agentscope.setup_logger",
    ) as setup_logger:
        _load_deep_research_module()

    makedirs.assert_not_called()
    setup_logger.assert_not_called()


class _DummyModel(ChatModelBase):
    """Minimal chat model for deep research construction tests."""

    def __init__(self) -> None:
        super().__init__("deep-research-test-model", stream=False)

    async def __call__(self, _messages, **kwargs) -> ChatResponse:
        return ChatResponse(
            content=[TextBlock(type="text", text="ok")],
        )


def _build_agent(module, tmpdir: str):
    """Construct a deep research agent with lightweight test doubles."""
    return module.DeepResearchAgent(
        name="researcher",
        model=_DummyModel(),
        formatter=DashScopeChatFormatter(),
        memory=InMemoryMemory(),
        search_mcp_client=object(),
        tmp_file_storage_dir=tmpdir,
    )


def test_inprocess_report_path_is_stable_and_logical() -> None:
    """Draft report paths must not depend on raw user_query content."""
    module = _load_deep_research_module()

    path = module._build_inprocess_report_path("report-base", 3)

    assert path == "/workspace/report-base_inprocess_report_3.md"
    assert validate_path(path) == path


def test_deep_research_agent_registers_logical_file_tools() -> None:
    """The agent must expose FileDomain-backed file tools."""
    module = _load_deep_research_module()
    with TemporaryDirectory() as tmpdir:
        os.makedirs(os.path.join(tmpdir, "log"), exist_ok=True)
        agent = _build_agent(module, tmpdir)
        workspace_entries = agent.filesystem_service.list_directory(
            "/workspace/",
        )

    tool_names = set(agent.toolkit.tools)
    assert {
        "read_text_file",
        "write_file",
        "edit_file",
        "list_directory",
    }.issubset(tool_names)
    assert agent.read_file_function == "read_text_file"
    assert agent.write_file_function == "write_file"
    assert "[DIR] log/" not in workspace_entries


def test_reply_appends_expected_output_to_structured_user_content() -> None:
    """Expected-output hints must preserve structured message content."""
    module = _load_deep_research_module()
    with TemporaryDirectory() as tmpdir:
        agent = _build_agent(module, tmpdir)

    async def fake_decompose():
        agent.current_subtask[-1].knowledge_gaps = "gap"
        agent.current_subtask[-1].working_plan = "plan"

    agent.max_iters = 0
    agent._ensure_mcp_initialized = AsyncMock()
    agent.decompose_and_expand_subtask = AsyncMock(
        side_effect=fake_decompose,
    )
    agent._summarizing = AsyncMock(
        return_value=Msg("researcher", "summary", "assistant"),
    )
    user_msg = Msg(
        "user",
        [TextBlock(type="text", text="question")],
        "user",
    )

    asyncio.run(agent.reply(user_msg))

    stored_msg = agent.memory.content[0][0]
    assert isinstance(stored_msg.content, list)
    assert stored_msg.get_text_content() == "question\nExpected Output:\ngap"


def test_summarize_intermediate_results_writes_workspace_report() -> None:
    """Intermediate summaries must write via write_file to a logical path."""
    module = _load_deep_research_module()
    with TemporaryDirectory() as tmpdir:
        agent = _build_agent(module, tmpdir)

    agent.current_subtask = [
        module.SubTaskItem(
            objective="obj",
            working_plan="plan",
            knowledge_gaps="gap",
        ),
    ]
    agent.intermediate_memory = [
        Msg("assistant", "tool evidence", "assistant"),
    ]
    agent.get_model_output = AsyncMock(return_value=[{"text": "draft report"}])
    calls = []

    async def fake_call_specific_tool(func_name, params):
        calls.append((func_name, params))
        return None, None

    agent.call_specific_tool = fake_call_specific_tool

    asyncio.run(agent.summarize_intermediate_results())

    assert calls == [
        (
            "write_file",
            {
                "path": module._build_inprocess_report_path(
                    agent.report_path_based,
                    1,
                ),
                "content": "draft report",
            },
        ),
    ]


def test_generate_deepresearch_report_reads_existing_drafts_only() -> None:
    """Final report generation must read only existing drafts, then write once."""
    module = _load_deep_research_module()
    with TemporaryDirectory() as tmpdir:
        agent = _build_agent(module, tmpdir)

    agent.user_query = "original task"
    agent.current_subtask = [
        module.SubTaskItem(
            objective="obj",
            working_plan="plan",
            knowledge_gaps="must-cover",
        ),
    ]
    agent.report_index = 2
    calls = []

    async def fake_call_specific_tool(func_name, params):
        calls.append((func_name, params))
        if func_name == agent.read_file_function:
            return None, Msg(
                "system",
                [
                    {
                        "type": "tool_result",
                        "name": func_name,
                        "id": "tool-1",
                        "output": [{"type": "text", "text": "draft-1"}],
                    },
                ],
                "system",
            )
        return None, Msg(
            "system",
            [
                {
                    "type": "tool_result",
                    "name": func_name,
                    "id": "tool-2",
                    "output": [{"type": "text", "text": "written"}],
                },
            ],
            "system",
        )

    agent.call_specific_tool = fake_call_specific_tool
    agent.get_model_output = AsyncMock(return_value=[{"text": "final report"}])

    _, logical_path = asyncio.run(
        agent._generate_deepresearch_report("checklist-body"),
    )

    read_calls = [call for call in calls if call[0] == agent.read_file_function]
    write_calls = [
        call for call in calls if call[0] == agent.write_file_function
    ]

    assert len(read_calls) == 1
    assert read_calls[0][1]["path"] == module._build_inprocess_report_path(
        agent.report_path_based,
        1,
    )
    assert len(write_calls) == 1
    assert write_calls[0][1]["path"] == (
        f"/workspace/{agent.report_path_based}_detailed_report.md"
    )
    assert logical_path == f"/workspace/{agent.report_path_based}_detailed_report.md"

    msgs = agent.get_model_output.await_args.kwargs["msgs"]
    assert "original task" in msgs[0].content
    assert "checklist-body" in msgs[0].content


def test_generate_deepresearch_report_fails_fast_on_read_errors() -> None:
    """Draft read errors must stop report generation instead of being treated as text."""
    module = _load_deep_research_module()
    with TemporaryDirectory() as tmpdir:
        agent = _build_agent(module, tmpdir)

    agent.user_query = "original task"
    agent.current_subtask = [
        module.SubTaskItem(
            objective="obj",
            working_plan="plan",
            knowledge_gaps="must-cover",
        ),
    ]
    agent.report_index = 2

    async def fake_call_specific_tool(func_name, params):
        if func_name == agent.read_file_function:
            return None, Msg(
                "system",
                [
                    {
                        "type": "tool_result",
                        "name": func_name,
                        "id": "tool-1",
                        "output": [
                            {
                                "type": "text",
                                "text": "Error: NotFoundError: missing draft",
                            },
                        ],
                    },
                ],
                "system",
            )
        return None, Msg(
            "system",
            [
                {
                    "type": "tool_result",
                    "name": func_name,
                    "id": "tool-2",
                    "output": [{"type": "text", "text": "written"}],
                },
            ],
            "system",
        )

    agent.call_specific_tool = fake_call_specific_tool
    agent.get_model_output = AsyncMock(return_value=[{"text": "final report"}])

    try:
        asyncio.run(agent._generate_deepresearch_report("checklist-body"))
        assert False, "Expected RuntimeError was not raised"
    except RuntimeError as exc:
        assert "Failed to read draft report" in str(exc)


def test_follow_up_does_not_swallow_model_errors() -> None:
    """Expansion and judge errors must surface instead of pretending enough info."""
    module = _load_deep_research_module()
    with TemporaryDirectory() as tmpdir:
        agent = _build_agent(module, tmpdir)

    agent.current_subtask = [
        module.SubTaskItem(
            objective="obj",
            working_plan="plan",
            knowledge_gaps="gap",
        ),
    ]
    agent.get_model_output = AsyncMock(side_effect=RuntimeError("boom"))

    try:
        asyncio.run(
            agent._follow_up("search results", {"input": {"query": "q"}}),
        )
        assert False, "Expected RuntimeError was not raised"
    except RuntimeError as exc:
        assert "boom" in str(exc)


def test_decompose_does_not_swallow_model_errors() -> None:
    """Planning failures must surface instead of returning retry text."""
    module = _load_deep_research_module()
    with TemporaryDirectory() as tmpdir:
        agent = _build_agent(module, tmpdir)

    agent.current_subtask = [
        module.SubTaskItem(
            objective="obj",
            working_plan="plan",
            knowledge_gaps="gap",
        ),
    ]
    agent.get_model_output = AsyncMock(side_effect=RuntimeError("boom"))

    try:
        asyncio.run(agent.decompose_and_expand_subtask())
        assert False, "Expected RuntimeError was not raised"
    except RuntimeError as exc:
        assert "boom" in str(exc)


def test_reflect_failure_does_not_swallow_model_errors() -> None:
    """Reflection failures must surface instead of pretending retry is enough."""
    module = _load_deep_research_module()
    with TemporaryDirectory() as tmpdir:
        agent = _build_agent(module, tmpdir)

    agent.current_subtask = [
        module.SubTaskItem(
            objective="obj",
            working_plan="plan",
            knowledge_gaps="gap",
        ),
    ]
    agent.intermediate_memory = [Msg("assistant", "history", "assistant")]
    agent.get_model_output = AsyncMock(side_effect=RuntimeError("boom"))

    try:
        asyncio.run(agent.reflect_failure())
        assert False, "Expected RuntimeError was not raised"
    except RuntimeError as exc:
        assert "boom" in str(exc)


def test_summarizing_awaits_memory_add() -> None:
    """Summaries must be awaited when written back into memory."""
    module = _load_deep_research_module()
    with TemporaryDirectory() as tmpdir:
        agent = _build_agent(module, tmpdir)

    agent.current_subtask = [
        module.SubTaskItem(
            objective="obj",
            working_plan="plan",
            knowledge_gaps="gap",
        ),
    ]
    agent._generate_deepresearch_report = AsyncMock(
        return_value=(
            Msg(
                "system",
                [
                    {
                        "type": "tool_result",
                        "name": "write_file",
                        "id": "tool-1",
                        "output": [{"type": "text", "text": "final report"}],
                    },
                ],
                "system",
            ),
            "/workspace/final.md",
        ),
    )
    agent.memory.add = AsyncMock()

    asyncio.run(agent._summarizing())

    agent.memory.add.assert_awaited_once()


def test_deep_research_main_propagates_runtime_errors() -> None:
    """The sample entrypoint should expose runtime failures to callers."""
    module_name = "deep_research_main_for_test"
    main_path = DEEP_RESEARCH_DIR / "main.py"
    spec = importlib.util.spec_from_file_location(module_name, main_path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    with deep_research_on_path():
        spec.loader.exec_module(module)

    class FailingClient:
        def __init__(self, *args, **kwargs) -> None:
            pass

        async def connect(self) -> None:
            raise RuntimeError("connect boom")

        async def close(self) -> None:
            pass

    with TemporaryDirectory() as tmpdir, patch.dict(
        module.os.environ,
        {"AGENT_OPERATION_DIR": tmpdir},
    ), patch.object(
        module.tempfile,
        "mkdtemp",
        side_effect=AssertionError("mkdtemp should not run"),
    ), patch.object(module, "StdIOStatefulClient", FailingClient):
        try:
            asyncio.run(module.main("query"))
            assert False, "Expected RuntimeError was not raised"
        except RuntimeError as exc:
            assert "connect boom" in str(exc)
