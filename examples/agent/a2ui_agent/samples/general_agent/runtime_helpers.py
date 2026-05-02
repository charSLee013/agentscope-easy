# -*- coding: utf-8 -*-
"""Runtime helpers shared by the A2UI sample server and its tests."""
from __future__ import annotations

import tempfile
from pathlib import Path

from a2a.types import Message

from agentscope.filesystem import DiskFileSystem, FileDomainService, read_text_file
from agentscope.formatter import A2AChatFormatter
from agentscope.message import Msg
from agentscope.tool import Toolkit
from skills.A2UI_response_generator import (
    view_a2ui_examples,
    view_a2ui_schema,
)


_SAMPLE_DIR = Path(__file__).resolve().parent
_SKILLS_DIR = _SAMPLE_DIR / "skills"
_A2UI_SKILL_DIR = _SKILLS_DIR / "A2UI_response_generator"


def build_sample_toolkit() -> Toolkit:
    """Build the real sample toolkit used by the A2UI server."""
    fs = DiskFileSystem(
        root_dir=tempfile.mkdtemp(prefix="agentscope-a2ui-fs-"),
        internal_dir=str(_SKILLS_DIR),
    )
    handle = fs.create_handle(
        [
            {
                "prefix": "/workspace/",
                "ops": {
                    "list",
                    "file",
                    "read_binary",
                    "read_file",
                    "write",
                    "delete",
                },
            },
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
    toolkit.register_agent_skill(str(_A2UI_SKILL_DIR))
    toolkit.register_tool_function(view_a2ui_schema)
    toolkit.register_tool_function(view_a2ui_examples)
    return toolkit


async def prepare_final_a2a_message(
    formatter: A2AChatFormatter,
    final_msg: Msg | None,
) -> Message:
    """Format and post-process the final A2UI message."""
    if final_msg is None:
        raise RuntimeError("Agent stream completed without a final message")

    from a2ui_utils import post_process_a2a_message_for_ui

    final_a2a_message = await formatter.format([final_msg])
    return post_process_a2a_message_for_ui(final_a2a_message)
