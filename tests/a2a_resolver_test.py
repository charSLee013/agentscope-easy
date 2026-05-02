# -*- coding: utf-8 -*-
"""The agent card resolver tests for A2A agents."""
import json
import os
import sys
import tempfile
import uuid
from contextlib import contextmanager
from pathlib import Path
from unittest import IsolatedAsyncioTestCase
from unittest.mock import patch

from a2a.types import Message, MessageSendParams, TextPart

from agentscope.a2a import FileAgentCardResolver
from agentscope.message import Msg


A2A_SAMPLE_DIR = (
    Path(__file__).resolve().parents[1] / "examples" / "agent" / "a2a_agent"
)


@contextmanager
def a2a_sample_on_path():
    """Temporarily add the A2A sample directory to sys.path."""
    sys.path.insert(0, str(A2A_SAMPLE_DIR))
    try:
        yield
    finally:
        sys.path.remove(str(A2A_SAMPLE_DIR))


def load_sample_agent_card():
    """Load the real A2A sample agent card."""
    sys.modules.pop("agent_card", None)
    with a2a_sample_on_path():
        from agent_card import agent_card

    return agent_card


async def _collect_async(async_iterable):
    """Collect all items from an async iterable."""
    items = []
    async for item in async_iterable:
        items.append(item)
    return items


class A2AAgentCardResolverTest(IsolatedAsyncioTestCase):
    """Test the A2A agent card resolver."""

    async def asyncSetUp(self) -> None:
        """Set up the test case."""
        self.agent_card = load_sample_agent_card()
        self.agent_card_path = "./test_agent_card.json"

    async def test_file_card_resolver(self) -> None:
        """Test the file agent card resolver."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Save one agent card to a file
            self.agent_card_path = os.path.join(tmpdir, "test_agent_card.json")
            json_dict = self.agent_card.model_dump()
            with open(self.agent_card_path, "w", encoding="utf-8") as file:
                json.dump(json_dict, file)

            agent_card = await FileAgentCardResolver(
                file_path=self.agent_card_path,
            ).get_agent_card()

            self.assertDictEqual(
                agent_card.model_dump(),
                self.agent_card.model_dump(),
            )

    async def test_agent_card_skills_match_server_registration(self) -> None:
        """A2A agent card skills should match the server Toolkit surface."""
        with a2a_sample_on_path():
            sys.modules.pop("setup_a2a_server", None)
            import setup_a2a_server

        toolkit = setup_a2a_server.build_a2a_toolkit()
        card_skill_ids = {skill.id for skill in self.agent_card.skills}
        registered_tool_ids = {
            schema["function"]["name"]
            for schema in toolkit.get_json_schemas()
        }

        self.assertEqual(card_skill_ids, registered_tool_ids)

    async def test_server_uses_task_id_for_session_identity(self) -> None:
        """A2A session identity should use the canonical task_id."""
        with a2a_sample_on_path():
            sys.modules.pop("setup_a2a_server", None)
            import setup_a2a_server

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

            async def format(self, messages):
                return Message(
                    messageId="formatted",
                    role="agent",
                    parts=[TextPart(text="done")],
                )

        class FakeAgent:
            def __init__(self, *args, **kwargs) -> None:
                pass

            async def __call__(self, msg):
                return Msg("Friday", "done", "assistant")

        async def fake_stream_printing_messages(*, agents, coroutine_task):
            yield await coroutine_task, True

        params = MessageSendParams(
            message=Message(
                messageId="input-message",
                role="user",
                parts=[TextPart(text="hello")],
            ),
        )
        uuid_value = uuid.UUID("12345678123456781234567812345678")

        with (
            patch.object(setup_a2a_server.uuid, "uuid4", return_value=uuid_value),
            patch.object(setup_a2a_server, "build_a2a_toolkit"),
            patch.object(setup_a2a_server, "DashScopeChatModel"),
            patch.object(setup_a2a_server, "ReActAgent", FakeAgent),
            patch.object(setup_a2a_server, "JSONSession", FakeSession),
            patch.object(setup_a2a_server, "A2AChatFormatter", FakeFormatter),
            patch.object(
                setup_a2a_server,
                "stream_printing_messages",
                fake_stream_printing_messages,
            ),
        ):
            events = await _collect_async(
                setup_a2a_server.SimpleStreamHandler().on_message_send_stream(
                    params,
                ),
            )

        self.assertEqual([event.task_id for event in events], [uuid_value.hex] * 3)
        self.assertEqual(load_session_ids, [uuid_value.hex])
        self.assertEqual(save_session_ids, [uuid_value.hex])
        self.assertEqual(len(save_dirs), 1)
        self.assertNotEqual(save_dirs[0], "./sessions")
