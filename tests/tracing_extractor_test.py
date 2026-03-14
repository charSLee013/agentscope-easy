# -*- coding: utf-8 -*-
"""Tracing extractor tests."""
from unittest import TestCase

from agentscope.embedding import EmbeddingModelBase
from agentscope.formatter import FormatterBase
from agentscope.message import Msg, TextBlock, ToolUseBlock
from agentscope.model import ChatModelBase, ChatResponse
from agentscope.tracing._attributes import (
    OperationNameValues,
    ProviderNameValues,
    SpanAttributes,
)
from agentscope.tracing._extractor import (
    _get_agent_messages,
    _get_agent_request_attributes,
    _get_agent_response_attributes,
    _get_embedding_request_attributes,
    _get_embedding_response_attributes,
    _get_formatter_request_attributes,
    _get_formatter_response_attributes,
    _get_generic_function_request_attributes,
    _get_generic_function_response_attributes,
    _get_llm_request_attributes,
    _get_tool_request_attributes,
)


class DummyModel(ChatModelBase):
    """Model stub for extractor tests."""

    def __init__(self) -> None:
        super().__init__("dummy-model", stream=False)

    async def __call__(self, _messages, **kwargs):
        return ChatResponse(content=[TextBlock(type="text", text="ok")])


class DummyAgent:
    """Agent stub for extractor tests."""

    id = "agent-1"
    name = "Friday"


class OpenAIChatFormatter(FormatterBase):
    """Formatter stub named to exercise provider inference."""

    async def format(self, *args, **kwargs):
        return [{"role": "user", "content": "ok"}]


class OpenAIEmbeddingModel(EmbeddingModelBase):
    """Embedding stub named to exercise provider inference."""

    def __init__(self) -> None:
        super().__init__("embed-small", 1024)

    async def __call__(self, *args, **kwargs):
        return [[0.1, 0.2]]


class TracingExtractorTest(TestCase):
    """Tests for tracing attribute extractors."""

    def test_get_agent_messages_supports_single_and_list_input(self) -> None:
        """Agent messages should normalize single Msg and list[Msg]."""
        single = Msg("user", "hello", "user")
        multiple = [
            Msg("user", "first", "user"),
            Msg(
                "assistant",
                [
                    ToolUseBlock(
                        type="tool_use",
                        id="tool-1",
                        name="search",
                        input={"query": "x"},
                    ),
                ],
                "assistant",
            ),
        ]

        single_payload = _get_agent_messages(single)
        multiple_payload = _get_agent_messages(multiple)

        self.assertEqual(single_payload[0]["content"][0]["content"], "hello")
        self.assertEqual(len(multiple_payload), 2)
        self.assertEqual(
            multiple_payload[1]["content"][0]["type"],
            "tool_call",
        )

    def test_extract_request_and_response_attributes(self) -> None:
        """Agent/tool/llm extractors should emit structured attributes."""
        agent_msg = Msg("user", "hello", "user")
        response_msg = Msg("assistant", "done", "assistant")
        tool_call = ToolUseBlock(
            type="tool_use",
            id="tool-2",
            name="lookup",
            input={"query": "hello"},
        )

        agent_attrs = _get_agent_request_attributes(
            DummyAgent(),
            (agent_msg,),
            {},
        )
        response_attrs = _get_agent_response_attributes(response_msg)
        llm_attrs = _get_llm_request_attributes(
            DummyModel(),
            ([],),
            {"tools": [], "tool_choice": "auto"},
        )
        tool_attrs = _get_tool_request_attributes(object(), tool_call)

        self.assertIn(SpanAttributes.GEN_AI_INPUT_MESSAGES, agent_attrs)
        self.assertIn(SpanAttributes.GEN_AI_OUTPUT_MESSAGES, response_attrs)
        self.assertEqual(
            llm_attrs[SpanAttributes.GEN_AI_REQUEST_MODEL],
            "dummy-model",
        )
        self.assertEqual(
            tool_attrs[SpanAttributes.GEN_AI_TOOL_NAME],
            "lookup",
        )

    def test_extract_formatter_embedding_and_generic_attributes(self) -> None:
        """Formatter, embedding, and generic helpers should emit new attrs."""
        formatter_attrs = _get_formatter_request_attributes(
            OpenAIChatFormatter(),
            (["msg"],),
            {"system": "demo"},
        )
        formatter_response_attrs = _get_formatter_response_attributes(
            [{"role": "user", "content": "ok"}],
        )
        embedding_attrs = _get_embedding_request_attributes(
            OpenAIEmbeddingModel(),
            (["hello"],),
            {},
        )
        embedding_response_attrs = _get_embedding_response_attributes(
            [[0.1, 0.2]],
        )
        generic_attrs = _get_generic_function_request_attributes(
            "demo_func",
            (1,),
            {"flag": True},
        )
        generic_response_attrs = _get_generic_function_response_attributes(
            {"done": True},
        )

        self.assertEqual(
            formatter_attrs[SpanAttributes.GEN_AI_OPERATION_NAME],
            OperationNameValues.FORMATTER,
        )
        self.assertEqual(
            formatter_attrs[SpanAttributes.AGENTSCOPE_FORMAT_TARGET],
            ProviderNameValues.OPENAI,
        )
        self.assertEqual(
            formatter_response_attrs[SpanAttributes.AGENTSCOPE_FORMAT_COUNT],
            1,
        )
        self.assertEqual(
            embedding_attrs[SpanAttributes.GEN_AI_OPERATION_NAME],
            OperationNameValues.EMBEDDINGS,
        )
        self.assertEqual(
            embedding_attrs[SpanAttributes.GEN_AI_PROVIDER_NAME],
            ProviderNameValues.OPENAI,
        )
        self.assertEqual(
            embedding_attrs[SpanAttributes.GEN_AI_REQUEST_MODEL],
            "embed-small",
        )
        self.assertIn(
            SpanAttributes.AGENTSCOPE_FUNCTION_OUTPUT,
            embedding_response_attrs,
        )
        self.assertEqual(
            generic_attrs[SpanAttributes.GEN_AI_OPERATION_NAME],
            OperationNameValues.INVOKE_GENERIC_FUNCTION,
        )
        self.assertEqual(
            generic_attrs[SpanAttributes.AGENTSCOPE_FUNCTION_NAME],
            "demo_func",
        )
        self.assertIn(
            SpanAttributes.AGENTSCOPE_FUNCTION_OUTPUT,
            generic_response_attrs,
        )
