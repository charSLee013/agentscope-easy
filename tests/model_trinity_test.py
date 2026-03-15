# -*- coding: utf-8 -*-
"""Unit tests for the Trinity-RFT model adapter."""
from unittest.async_case import IsolatedAsyncioTestCase
from unittest.mock import AsyncMock, Mock

from agentscope.message import TextBlock
from agentscope.model import ChatResponse, TrinityChatModel


class TestTrinityChatModel(IsolatedAsyncioTestCase):
    """Test cases for TrinityChatModel."""

    async def test_init_with_trinity_client(self) -> None:
        """The adapter should reuse the provided Trinity client."""
        model_name = "Qwen/Qwen3-8B"
        mock_client = Mock()
        mock_client.model_path = model_name

        model_1 = TrinityChatModel(
            openai_async_client=mock_client,
            enable_thinking=False,
            generate_kwargs={
                "temperature": 1.0,
                "top_k": 2,
            },
        )
        model_2 = TrinityChatModel(
            openai_async_client=mock_client,
            enable_thinking=True,
            generate_kwargs={
                "max_tokens": 500,
                "top_p": 0.9,
            },
        )
        self.assertEqual(model_1.model_name, model_name)
        self.assertFalse(model_1.stream)
        self.assertIs(model_1.client, mock_client)
        self.assertEqual(model_2.model_name, model_name)
        self.assertFalse(model_2.stream)
        self.assertIs(model_2.client, mock_client)

        messages = [{"role": "user", "content": "Hello"}]
        mock_message = Mock()
        mock_message.content = "Hi there!"
        mock_message.reasoning_content = None
        mock_message.tool_calls = []
        mock_message.audio = None
        mock_message.parsed = None
        mock_choice = Mock()
        mock_choice.message = mock_message
        mock_response = Mock()
        mock_response.choices = [mock_choice]
        mock_usage = Mock()
        mock_usage.prompt_tokens = 10
        mock_usage.completion_tokens = 20
        mock_response.usage = mock_usage

        mock_client.chat.completions.create = AsyncMock(
            return_value=mock_response,
        )

        result = await model_1(messages)
        call_args = mock_client.chat.completions.create.call_args[1]
        self.assertEqual(call_args["model"], model_name)
        self.assertEqual(call_args["messages"], messages)
        self.assertFalse(call_args["stream"])
        self.assertFalse(call_args["chat_template_kwargs"]["enable_thinking"])
        self.assertEqual(call_args["temperature"], 1.0)
        self.assertEqual(call_args["top_k"], 2)
        self.assertNotIn("max_tokens", call_args)
        self.assertNotIn("top_p", call_args)
        self.assertIsInstance(result, ChatResponse)
        self.assertEqual(
            result.content,
            [TextBlock(type="text", text="Hi there!")],
        )

        result = await model_2(messages)
        call_args = mock_client.chat.completions.create.call_args[1]
        self.assertEqual(call_args["model"], model_name)
        self.assertEqual(call_args["messages"], messages)
        self.assertFalse(call_args["stream"])
        self.assertTrue(call_args["chat_template_kwargs"]["enable_thinking"])
        self.assertEqual(call_args["max_tokens"], 500)
        self.assertEqual(call_args["top_p"], 0.9)
        self.assertNotIn("temperature", call_args)
        self.assertNotIn("top_k", call_args)
        self.assertIsInstance(result, ChatResponse)
        self.assertEqual(
            result.content,
            [TextBlock(type="text", text="Hi there!")],
        )

    async def test_init_rejects_client_without_model_path(self) -> None:
        """Clients without model_path should be rejected early."""
        with self.assertRaisesRegex(ValueError, "model_path"):
            TrinityChatModel(openai_async_client=object())
