# -*- coding: utf-8 -*-
"""Internal regression tests for the ReMe short-term memory example."""
from __future__ import annotations

import asyncio
import importlib.util
from pathlib import Path
from tempfile import TemporaryDirectory

from agentscope.message import Msg


REME_MEMORY_PATH = (
    Path(__file__).resolve().parents[1]
    / "examples"
    / "functionality"
    / "short_term_memory"
    / "reme"
    / "reme_short_term_memory.py"
)


def _load_reme_memory_module():
    """Load the ReMe memory module from the example path."""
    spec = importlib.util.spec_from_file_location(
        "test_reme_short_term_memory",
        REME_MEMORY_PATH,
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class _DummyFormatter:
    """Formatter that exposes structured content for get_memory()."""

    def __init__(self) -> None:
        self.last_msgs = None

    async def format(self, *, msgs):
        self.last_msgs = msgs
        return [
            {
                "role": "assistant",
                "content": [
                    {
                        "type": "tool_result",
                        "name": "tool",
                        "id": "tool-1",
                        "output": [{"type": "text", "text": "payload"}],
                    },
                ],
            },
        ]


class _EchoFormatter:
    """Formatter that returns one dict per stored message."""

    async def format(self, *, msgs):
        return [
            {
                "role": msg.role,
                "content": msg.get_text_content() or "",
            }
            for msg in msgs
        ]


class _DummyApp:
    """Async execute stub for ReMe offload tests."""

    def __init__(self) -> None:
        self.calls = []

    async def async_execute(self, **kwargs):
        self.calls.append(kwargs)
        return {
            "answer": [{"role": "assistant", "content": "managed text"}],
            "metadata": {"write_file_dict": {}},
        }


class _EchoApp:
    """Async execute stub that returns one answer per input message."""

    async def async_execute(self, **kwargs):
        return {
            "answer": [
                {"role": msg["role"], "content": msg.get("content") or ""}
                for msg in kwargs["messages"]
            ],
            "metadata": {"write_file_dict": {}},
        }


class _CompactingApp:
    """Async execute stub that compacts multiple messages into one."""

    async def async_execute(self, **kwargs):
        return {
            "answer": [{"role": "assistant", "content": "summary"}],
            "metadata": {"write_file_dict": {}},
        }


class _ReorderingApp:
    """Async execute stub that returns messages in reverse order."""

    async def async_execute(self, **kwargs):
        return {
            "answer": list(reversed(kwargs["messages"])),
            "metadata": {"write_file_dict": {}},
        }


def test_get_memory_preserves_tuple_storage_and_serializes_blocks() -> None:
    """get_memory should keep tuple storage and preserve structured content text."""
    module = _load_reme_memory_module()
    memory = object.__new__(module.ReMeShortTermMemory)
    module.InMemoryMemory.__init__(memory)
    memory.formatter = _EchoFormatter()
    memory.app = _DummyApp()
    memory.working_summary_mode = "auto"
    memory.compact_ratio_threshold = 0.75
    memory.max_total_tokens = 10
    memory.max_tool_message_tokens = 10
    memory.group_token_threshold = None
    memory.keep_recent_count = 1
    with TemporaryDirectory() as tmpdir:
        memory.store_dir = tmpdir
        memory.content = [(Msg("assistant", "seed", "assistant"), [])]

        result = asyncio.run(memory.get_memory())

    assert result[0].content[0]["text"] == "managed text"
    assert isinstance(memory.content[0], tuple)
    assert memory.app.calls[0]["messages"][0]["content"]

    asyncio.run(memory.add(Msg("assistant", "next", "assistant")))
    assert len(memory.content) == 2


def test_get_memory_accepts_base_filter_arguments() -> None:
    """get_memory should honor MemoryBase filtering arguments."""
    module = _load_reme_memory_module()
    memory = object.__new__(module.ReMeShortTermMemory)
    module.InMemoryMemory.__init__(memory)
    memory.formatter = _DummyFormatter()
    memory.app = _DummyApp()
    memory.working_summary_mode = "auto"
    memory.compact_ratio_threshold = 0.75
    memory.max_total_tokens = 10
    memory.max_tool_message_tokens = 10
    memory.group_token_threshold = None
    memory.keep_recent_count = 1
    with TemporaryDirectory() as tmpdir:
        memory.store_dir = tmpdir
        keep = Msg("assistant", "keep", "assistant")
        skip = Msg("assistant", "skip", "assistant")
        memory.content = [(keep, []), (skip, ["compressed"])]

        asyncio.run(
            memory.get_memory(
                exclude_mark="compressed",
                prepend_summary=False,
                audit_flag=True,
            ),
        )

    assert [msg.id for msg in memory.formatter.last_msgs] == [keep.id]


def test_get_memory_exclude_mark_ids_stay_updatable() -> None:
    """IDs returned from exclude_mark reads must update backing marks."""
    module = _load_reme_memory_module()
    memory = object.__new__(module.ReMeShortTermMemory)
    module.InMemoryMemory.__init__(memory)
    memory.formatter = _EchoFormatter()
    memory.app = _EchoApp()
    memory.working_summary_mode = "auto"
    memory.compact_ratio_threshold = 0.75
    memory.max_total_tokens = 10
    memory.max_tool_message_tokens = 10
    memory.group_token_threshold = None
    memory.keep_recent_count = 1
    with TemporaryDirectory() as tmpdir:
        memory.store_dir = tmpdir
        keep = Msg("assistant", "keep", "assistant")
        skip = Msg("assistant", "skip", "assistant")
        memory.content = [(keep, []), (skip, ["compressed"])]

        visible = asyncio.run(
            memory.get_memory(
                exclude_mark="compressed",
                prepend_summary=False,
            ),
        )
        updated = asyncio.run(
            memory.update_messages_mark(
                new_mark="compressed",
                msg_ids=[msg.id for msg in visible],
            ),
        )
        visible_after = asyncio.run(
            module.InMemoryMemory.get_memory(
                memory,
                exclude_mark="compressed",
            ),
        )

    assert [msg.id for msg in visible] == [keep.id]
    assert updated == 1
    assert visible_after == []


def test_get_memory_preserves_marks_after_management() -> None:
    """get_memory should not discard marks when rewriting stored messages."""
    module = _load_reme_memory_module()
    memory = object.__new__(module.ReMeShortTermMemory)
    module.InMemoryMemory.__init__(memory)
    memory.formatter = _DummyFormatter()
    memory.app = _EchoApp()
    memory.working_summary_mode = "auto"
    memory.compact_ratio_threshold = 0.75
    memory.max_total_tokens = 10
    memory.max_tool_message_tokens = 10
    memory.group_token_threshold = None
    memory.keep_recent_count = 1
    with TemporaryDirectory() as tmpdir:
        memory.store_dir = tmpdir
        important = Msg("assistant", "important", "assistant")
        compressed = Msg("assistant", "compressed", "assistant")
        memory.content = [
            (important, ["important"]),
            (compressed, ["compressed"]),
        ]

        asyncio.run(memory.get_memory(prepend_summary=False))

        important_msgs = asyncio.run(
            module.InMemoryMemory.get_memory(memory, mark="important"),
        )
        visible_msgs = asyncio.run(
            module.InMemoryMemory.get_memory(
                memory,
                exclude_mark="compressed",
            ),
        )

    assert len(important_msgs) == 1
    assert important_msgs[0].content[0]["text"]
    assert len(visible_msgs) == 1


def test_get_memory_does_not_rewrite_storage_when_mapping_is_unsafe() -> None:
    """Non-1:1 ReMe rewrites must not corrupt stored marks."""
    module = _load_reme_memory_module()
    memory = object.__new__(module.ReMeShortTermMemory)
    module.InMemoryMemory.__init__(memory)
    memory.formatter = _EchoFormatter()
    memory.app = _CompactingApp()
    memory.working_summary_mode = "auto"
    memory.compact_ratio_threshold = 0.75
    memory.max_total_tokens = 10
    memory.max_tool_message_tokens = 10
    memory.group_token_threshold = None
    memory.keep_recent_count = 1
    with TemporaryDirectory() as tmpdir:
        memory.store_dir = tmpdir
        keep = Msg("assistant", "keep", "assistant")
        compressed = Msg("assistant", "compressed", "assistant")
        memory.content = [(keep, []), (compressed, ["compressed"])]

        result = asyncio.run(memory.get_memory(prepend_summary=False))
        visible_msgs = asyncio.run(
            module.InMemoryMemory.get_memory(
                memory,
                exclude_mark="compressed",
            ),
        )

    assert result[0].get_text_content() == "summary"
    assert [msg.id for msg in visible_msgs] == [keep.id]


def test_get_memory_persists_managed_messages_without_marks() -> None:
    """Unmarked memory should persist ReMe compaction for future reads."""
    module = _load_reme_memory_module()
    memory = object.__new__(module.ReMeShortTermMemory)
    module.InMemoryMemory.__init__(memory)
    memory.formatter = _EchoFormatter()
    memory.app = _CompactingApp()
    memory.working_summary_mode = "auto"
    memory.compact_ratio_threshold = 0.75
    memory.max_total_tokens = 10
    memory.max_tool_message_tokens = 10
    memory.group_token_threshold = None
    memory.keep_recent_count = 1
    with TemporaryDirectory() as tmpdir:
        memory.store_dir = tmpdir
        first = Msg("assistant", "first", "assistant")
        second = Msg("assistant", "second", "assistant")
        memory.content = [(first, []), (second, [])]

        result = asyncio.run(memory.get_memory())

    assert result[0].get_text_content() == "summary"
    assert [msg.get_text_content() for msg, _ in memory.content] == ["summary"]


def test_get_memory_does_not_rewrite_storage_when_messages_reorder() -> None:
    """Reordered ReMe output must not receive positional marks."""
    module = _load_reme_memory_module()
    memory = object.__new__(module.ReMeShortTermMemory)
    module.InMemoryMemory.__init__(memory)
    memory.formatter = _EchoFormatter()
    memory.app = _ReorderingApp()
    memory.working_summary_mode = "auto"
    memory.compact_ratio_threshold = 0.75
    memory.max_total_tokens = 10
    memory.max_tool_message_tokens = 10
    memory.group_token_threshold = None
    memory.keep_recent_count = 1
    with TemporaryDirectory() as tmpdir:
        memory.store_dir = tmpdir
        first = Msg("assistant", "first", "assistant")
        second = Msg("assistant", "second", "assistant")
        memory.content = [(first, ["first"]), (second, ["second"])]

        result = asyncio.run(memory.get_memory(prepend_summary=False))
        first_msgs = asyncio.run(
            module.InMemoryMemory.get_memory(memory, mark="first"),
        )

    assert [msg.get_text_content() for msg in result] == ["second", "first"]
    assert [msg.id for msg in first_msgs] == [first.id]


def test_get_memory_does_not_rewrite_storage_with_prepended_summary() -> None:
    """Synthetic compressed summaries must not shift stored marks."""
    module = _load_reme_memory_module()
    memory = object.__new__(module.ReMeShortTermMemory)
    module.InMemoryMemory.__init__(memory)
    memory.formatter = _EchoFormatter()
    memory.app = _EchoApp()
    memory.working_summary_mode = "auto"
    memory.compact_ratio_threshold = 0.75
    memory.max_total_tokens = 10
    memory.max_tool_message_tokens = 10
    memory.group_token_threshold = None
    memory.keep_recent_count = 1
    with TemporaryDirectory() as tmpdir:
        memory.store_dir = tmpdir
        first = Msg("assistant", "first", "assistant")
        second = Msg("assistant", "second", "assistant")
        memory.content = [(first, ["m1"]), (second, ["m2"])]
        asyncio.run(memory.update_compressed_summary("summary text"))

        result = asyncio.run(memory.get_memory())
        m1_msgs = asyncio.run(
            module.InMemoryMemory.get_memory(
                memory,
                mark="m1",
                prepend_summary=False,
            ),
        )
        m2_msgs = asyncio.run(
            module.InMemoryMemory.get_memory(
                memory,
                mark="m2",
                prepend_summary=False,
            ),
        )

    assert [msg.get_text_content() for msg in result] == [
        "summary text",
        "first",
        "second",
    ]
    assert [msg.id for msg in m1_msgs] == [first.id]
    assert [msg.id for msg in m2_msgs] == [second.id]
