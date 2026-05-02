# -*- coding: utf-8 -*-
"""Regression tests for A2UI skill retrieval tools."""

import asyncio
import ast
import importlib
import re
import sys
import tempfile
import uuid
from unittest.mock import patch

from a2a.types import Message, MessageSendParams, TextPart

from agentscope.filesystem import DiskFileSystem, FileDomainService, read_text_file
from agentscope.message import Msg
from agentscope.message import ToolUseBlock
from agentscope.tool import Toolkit, ToolResponse

from tests._a2ui_sample import (
    SAMPLE_DIR,
    SKILL_DIR,
    load_sample_agent_card,
    purge_a2ui_skill_modules,
    sample_on_path,
    stubbed_a2ui_extension,
)


def _load_skill_module():
    """Import the A2UI skill package from the real sample path."""
    with sample_on_path():
        purge_a2ui_skill_modules()
        importlib.invalidate_caches()
        return importlib.import_module("skills.A2UI_response_generator")


async def _collect_tool_chunks(
    toolkit: Toolkit,
    tool_use: ToolUseBlock,
) -> list[ToolResponse]:
    """Collect all response chunks from a toolkit tool call."""
    chunks = []
    async_gen = await toolkit.call_tool_function(tool_use)
    async for chunk in async_gen:
        chunks.append(chunk)
    return chunks


async def _collect_async(async_iterable):
    """Collect all items from an async iterable."""
    items = []
    async for item in async_iterable:
        items.append(item)
    return items


def test_a2ui_skill_tools_are_importable_and_return_tool_response() -> None:
    """A2UI retrieval tools should be importable from the sample package."""
    skill_module = _load_skill_module()
    schema_result = asyncio.run(skill_module.view_a2ui_schema())
    examples_result = asyncio.run(
        skill_module.view_a2ui_examples("SINGLE_COLUMN_LIST_WITH_IMAGE"),
    )

    assert isinstance(schema_result, ToolResponse)
    assert isinstance(examples_result, ToolResponse)
    assert "A2UI JSON Schema" in schema_result.content[0]["text"]
    assert "A2UI Template" in examples_result.content[0]["text"]


def test_skill_markdown_template_names_match_runtime_contract() -> None:
    """The skill doc should list the exact template names accepted at runtime."""
    module = ast.parse((SKILL_DIR / "view_a2ui_examples.py").read_text())
    template_keys: list[str] = []
    for node in module.body:
        if not isinstance(node, ast.Assign):
            continue
        if not any(
            isinstance(target, ast.Name) and target.id == "TEMPLATE_MAP"
            for target in node.targets
        ):
            continue
        template_keys = [key.value for key in node.value.keys]
        break

    skill_md = (SKILL_DIR / "SKILL.md").read_text()
    match = re.search(
        r"\*\*Available templates:\*\*(.*?)\*\*IMPORTANT\*\*",
        skill_md,
        re.S,
    )
    assert match is not None

    documented_keys = [
        match.group(1)
        for match in (
            re.match(r"- `([^`]+)`", line)
            for line in match.group(1).splitlines()
        )
        if match
    ]

    assert sorted(documented_keys) == sorted(template_keys)


def test_view_a2ui_examples_docstring_matches_runtime_contract() -> None:
    """The tool docstring should describe the same template names it accepts."""
    module = ast.parse((SKILL_DIR / "view_a2ui_examples.py").read_text())
    template_keys: list[str] = []
    docstring_keys: list[str] = []
    for node in module.body:
        if isinstance(node, ast.Assign) and any(
            isinstance(target, ast.Name) and target.id == "TEMPLATE_MAP"
            for target in node.targets
        ):
            template_keys = [key.value for key in node.value.keys]
        if isinstance(node, ast.AsyncFunctionDef) and node.name == (
            "view_a2ui_examples"
        ):
            docstring = ast.get_docstring(node) or ""
            docstring_keys = [
                match.group(1)
                for match in (
                    re.match(r"\s*-\s([A-Z0-9_]+)", line)
                    for line in docstring.splitlines()
                )
                if match
            ]

    assert sorted(docstring_keys) == sorted(template_keys)


def test_a2ui_skill_package_import_does_not_mutate_sys_path() -> None:
    """Importing the skill package should not rewrite interpreter search paths."""
    baseline = list(sys.path)
    with sample_on_path():
        purge_a2ui_skill_modules()
        importlib.invalidate_caches()
        importlib.import_module("skills.A2UI_response_generator")

    assert sys.path == baseline


def test_a2ui_retrieval_tools_are_not_dual_use_scripts() -> None:
    """Retrieval tool modules should not keep stale script entrypoints."""
    for file_name in ("view_a2ui_schema.py", "view_a2ui_examples.py"):
        text = (SKILL_DIR / file_name).read_text()
        assert "__main__" not in text


def test_setup_server_reuses_runtime_helper_objects() -> None:
    """The server should import and reuse the shared runtime helpers."""
    with sample_on_path(), stubbed_a2ui_extension():
        purge_a2ui_skill_modules()
        importlib.invalidate_caches()
        runtime_helpers = importlib.import_module("runtime_helpers")
        setup_server = importlib.import_module("setup_a2ui_server")

    assert setup_server.build_sample_toolkit is runtime_helpers.build_sample_toolkit
    assert (
        setup_server.prepare_final_a2a_message
        is runtime_helpers.prepare_final_a2a_message
    )


def test_agent_card_skills_match_server_registration() -> None:
    """agent_card.skills[*].id must match the tools the server actually registers.

    This locks the contract: the skills the agent card advertises must be
    exactly what setup_a2ui_server registers into the Toolkit.
    """
    card = load_sample_agent_card()
    card_skill_ids = {skill.id for skill in card.skills}
    with sample_on_path():
        purge_a2ui_skill_modules()
        importlib.invalidate_caches()
        runtime_helpers = importlib.import_module("runtime_helpers")
        toolkit = runtime_helpers.build_sample_toolkit()
    registered_tool_ids = {
        schema["function"]["name"]
        for schema in toolkit.get_json_schemas()
    }
    assert card_skill_ids == registered_tool_ids, (
        f"agent_card.skills mismatch.\n"
        f"Card advertises: {sorted(card_skill_ids)}\n"
        f"Server registers: {sorted(registered_tool_ids)}"
    )


def test_prepare_final_a2a_message_rejects_missing_final_msg() -> None:
    """The sample runtime must fail fast if no final Msg is available."""
    with sample_on_path():
        purge_a2ui_skill_modules()
        importlib.invalidate_caches()
        runtime_helpers = importlib.import_module("runtime_helpers")
    formatter = type("Formatter", (), {})()

    try:
        asyncio.run(
            runtime_helpers.prepare_final_a2a_message(formatter, None),
        )
        assert False, "Expected RuntimeError was not raised"
    except RuntimeError as exc:
        assert "without a final message" in str(exc)


def test_prepare_final_a2a_message_formats_then_post_processes() -> None:
    """The success path must format first, then post-process the message."""
    with sample_on_path(), stubbed_a2ui_extension():
        purge_a2ui_skill_modules()
        importlib.invalidate_caches()
        runtime_helpers = importlib.import_module("runtime_helpers")
        a2ui_utils = importlib.import_module("a2ui_utils")

    class FakeFormatter:
        def __init__(self) -> None:
            self.calls = []

        async def format(self, messages):
            self.calls.append(messages)
            return "formatted-message"

    formatter = FakeFormatter()
    final_msg = object()

    with patch.object(
        a2ui_utils,
        "post_process_a2a_message_for_ui",
        return_value="processed-message",
    ) as post_process:
        result = asyncio.run(
            runtime_helpers.prepare_final_a2a_message(formatter, final_msg),
        )

    assert formatter.calls == [[final_msg]]
    post_process.assert_called_once_with("formatted-message")
    assert result == "processed-message"


def test_setup_server_uses_generated_task_id_for_session_identity() -> None:
    """Missing inbound task_id should not fall back to a fixed session id."""
    with sample_on_path(), stubbed_a2ui_extension():
        purge_a2ui_skill_modules()
        importlib.invalidate_caches()
        setup_server = importlib.import_module("setup_a2ui_server")

    load_session_ids = []
    save_session_ids = []
    save_dirs = []

    class FakeSession:
        def __init__(self, save_dir: str) -> None:
            self.save_dir = save_dir
            save_dirs.append(save_dir)

        async def load_session_state(self, session_id, agent):
            load_session_ids.append(session_id)

        async def save_session_state(self, session_id, agent):
            save_session_ids.append(session_id)

    class FakeFormatter:
        async def format_a2a_message(self, name, message):
            return Msg(name, "hello", "user")

    class FakeAgent:
        sys_prompt = "prompt"

        def __init__(self, *args, **kwargs) -> None:
            pass

        async def __call__(self, msg):
            return Msg("Friday", "done", "assistant")

    async def fake_stream_printing_messages(*, agents, coroutine_task):
        yield await coroutine_task, True

    async def fake_prepare_final_a2a_message(formatter, final_msg):
        return Message(
            messageId="final-message",
            role="agent",
            parts=[TextPart(text="done")],
        )

    params = MessageSendParams(
        message=Message(
            messageId="input-message",
            role="user",
            parts=[TextPart(text="hello")],
        ),
    )
    uuid_value = uuid.UUID("12345678123456781234567812345678")

    with (
        patch.object(setup_server.uuid, "uuid4", return_value=uuid_value),
        patch.object(setup_server, "build_sample_toolkit", return_value=Toolkit()),
        patch.object(setup_server, "DashScopeChatModel", return_value=object()),
        patch.object(setup_server, "ReActAgent", FakeAgent),
        patch.object(setup_server, "JSONSession", FakeSession),
        patch.object(setup_server, "A2AChatFormatter", FakeFormatter),
        patch.object(
            setup_server,
            "stream_printing_messages",
            fake_stream_printing_messages,
        ),
        patch.object(
            setup_server,
            "prepare_final_a2a_message",
            fake_prepare_final_a2a_message,
        ),
    ):
        events = asyncio.run(
            _collect_async(
                setup_server.SimpleStreamHandler().on_message_send_stream(
                    params,
                ),
            ),
        )

    assert [event.task_id for event in events] == [
        uuid_value.hex,
        uuid_value.hex,
    ]
    assert load_session_ids == [uuid_value.hex]
    assert save_session_ids == [uuid_value.hex]
    assert len(save_dirs) == 1
    assert save_dirs[0] != "./sessions"


def test_setup_server_reuses_session_directory_for_same_task_id() -> None:
    """Two requests with one task_id must share save_dir and recover saved state."""
    with sample_on_path(), stubbed_a2ui_extension():
        purge_a2ui_skill_modules()
        importlib.invalidate_caches()
        setup_server = importlib.import_module("setup_a2ui_server")

    save_dirs = []
    loaded_states = []
    persisted = {}

    class FakeSession:
        def __init__(self, save_dir: str) -> None:
            self.save_dir = save_dir
            save_dirs.append(save_dir)

        async def load_session_state(self, session_id, agent):
            loaded_states.append(persisted.get((self.save_dir, session_id), False))

        async def save_session_state(self, session_id, agent):
            persisted[(self.save_dir, session_id)] = True

    class FakeFormatter:
        async def format_a2a_message(self, name, message):
            return Msg(name, "hello", "user")

    class FakeAgent:
        sys_prompt = "prompt"

        def __init__(self, *args, **kwargs) -> None:
            pass

        async def __call__(self, msg):
            return Msg("Friday", "done", "assistant")

    async def fake_stream_printing_messages(*, agents, coroutine_task):
        yield await coroutine_task, True

    async def fake_prepare_final_a2a_message(formatter, final_msg):
        return Message(
            messageId="final-message",
            role="agent",
            parts=[TextPart(text="done")],
        )

    params = MessageSendParams(
        message=Message(
            messageId="input-message",
            role="user",
            parts=[TextPart(text="hello")],
        ),
    )

    with (
        patch.object(setup_server, "build_sample_toolkit", return_value=Toolkit()),
        patch.object(setup_server, "DashScopeChatModel", return_value=object()),
        patch.object(setup_server, "ReActAgent", FakeAgent),
        patch.object(setup_server, "JSONSession", FakeSession),
        patch.object(setup_server, "A2AChatFormatter", FakeFormatter),
        patch.object(
            setup_server,
            "stream_printing_messages",
            fake_stream_printing_messages,
        ),
        patch.object(
            setup_server,
            "prepare_final_a2a_message",
            fake_prepare_final_a2a_message,
        ),
    ):
        handler = setup_server.SimpleStreamHandler()
        asyncio.run(
            _collect_async(
                handler.on_message_send_stream(
                    params,
                    task_id="shared-task",
                    context_id="ctx",
                ),
            ),
        )
        asyncio.run(
            _collect_async(
                handler.on_message_send_stream(
                    params,
                    task_id="shared-task",
                    context_id="ctx",
                ),
            ),
        )

    assert len(save_dirs) == 2
    assert save_dirs[0] == save_dirs[1]
    assert loaded_states == [False, True]


# ─── MEDIUM-2: invalid inputs must raise ValueError ───────────────────────────


def test_view_a2ui_schema_rejects_bad_schema_category() -> None:
    """view_a2ui_schema with an invalid schema_category must raise ValueError."""
    skill_module = _load_skill_module()

    try:
        asyncio.run(skill_module.view_a2ui_schema("BAD_CATEGORY"))
        assert False, "Expected ValueError was not raised"
    except ValueError as exc:
        assert "Invalid schema category: BAD_CATEGORY" in str(exc)


def test_view_a2ui_examples_rejects_empty_template_name() -> None:
    """view_a2ui_examples with empty template_name must raise ValueError."""
    skill_module = _load_skill_module()

    try:
        asyncio.run(skill_module.view_a2ui_examples(""))
        assert False, "Expected ValueError was not raised"
    except ValueError as exc:
        assert "template_name is required and cannot be empty" in str(exc)


def test_view_a2ui_examples_rejects_unknown_template() -> None:
    """view_a2ui_examples with an unknown template name must raise ValueError."""
    skill_module = _load_skill_module()

    try:
        asyncio.run(skill_module.view_a2ui_examples("NOT_A_REAL_TEMPLATE"))
        assert False, "Expected ValueError was not raised"
    except ValueError as exc:
        assert "Unknown template name: NOT_A_REAL_TEMPLATE" in str(exc)
        assert "Available templates:" in str(exc)


def test_toolkit_wraps_tool_value_error_as_error_text() -> None:
    """Toolkit must surface a registered async tool's ValueError as error text."""
    async def bad_tool(x: int) -> ToolResponse:
        raise ValueError("BAD")

    toolkit = Toolkit()
    toolkit.register_tool_function(bad_tool)

    tool_use = ToolUseBlock(
        type="tool_use",
        id="bad-tool",
        name="bad_tool",
        input={"x": 1},
    )
    chunks = asyncio.run(_collect_tool_chunks(toolkit, tool_use))
    combined = "".join(c.content[0]["text"] for c in chunks)
    assert combined.startswith("Error:")


# ─── MEDIUM-3: FileDomain main-chain regression test ──────────────────────────


def test_read_text_file_resolves_internal_skill_path() -> None:
    """FileDomain read_text_file should retrieve the real SKILL.md at /internal/."""
    with tempfile.TemporaryDirectory() as tmpdir:
        fs = DiskFileSystem(
            root_dir=tmpdir,
            internal_dir=str(SAMPLE_DIR / "skills"),
        )
        handle = fs.create_handle(
            [
                {
                    "prefix": "/internal/",
                    "ops": {"list", "file", "read_binary", "read_file"},
                },
            ],
        )
        service = FileDomainService(handle)
        toolkit = Toolkit()
        toolkit.register_tool_function(
            read_text_file,
            preset_kwargs={"service": service},
        )
        tool_use = ToolUseBlock(
            type="tool_use",
            id="read-skill",
            name="read_text_file",
            input={"path": "/internal/A2UI_response_generator/SKILL.md"},
        )
        result_chunks = asyncio.run(_collect_tool_chunks(toolkit, tool_use))

    assert len(result_chunks) == 1
    result = result_chunks[0]
    assert isinstance(result, ToolResponse)
    text = result.content[0]["text"]
    assert "---" in text, "SKILL.md frontmatter not found"
    assert "view_a2ui_schema" in text, "view_a2ui_schema not found in SKILL.md"
    assert "view_a2ui_examples" in text, "view_a2ui_examples not found in SKILL.md"
