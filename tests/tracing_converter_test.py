# -*- coding: utf-8 -*-
"""Tracing converter tests."""
from unittest import TestCase

from agentscope.message import AudioBlock, ImageBlock, TextBlock, ToolResultBlock
from agentscope.tracing._converter import _convert_block_to_part


class TracingConverterTest(TestCase):
    """Tests for tracing content-block conversion."""

    def test_convert_text_and_tool_result_blocks(self) -> None:
        """Text and tool result blocks should map into tracing parts."""
        text_part = _convert_block_to_part(
            TextBlock(type="text", text="hello"),
        )
        result_part = _convert_block_to_part(
            ToolResultBlock(
                type="tool_result",
                id="tool-1",
                name="search",
                output=[TextBlock(type="text", text="done")],
            ),
        )

        self.assertEqual(
            text_part,
            {"type": "text", "content": "hello"},
        )
        self.assertEqual(result_part["type"], "tool_call_response")
        self.assertEqual(result_part["id"], "tool-1")

    def test_convert_media_blocks(self) -> None:
        """Media blocks should become uri/blob parts."""
        image_part = _convert_block_to_part(
            ImageBlock(
                type="image",
                source={"type": "url", "url": "https://example.com/a.png"},
            ),
        )
        audio_part = _convert_block_to_part(
            AudioBlock(
                type="audio",
                source={"type": "base64", "data": "abc", "media_type": "audio/wav"},
            ),
        )

        self.assertEqual(image_part["type"], "uri")
        self.assertEqual(image_part["modality"], "image")
        self.assertEqual(audio_part["type"], "blob")
        self.assertEqual(audio_part["modality"], "audio")
