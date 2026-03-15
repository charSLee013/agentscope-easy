# -*- coding: utf-8 -*-
"""Unittests for the tracing functionality in AgentScope."""
import json
from typing import (
    AsyncGenerator,
    Generator,
    Any,
)
from unittest import IsolatedAsyncioTestCase

from opentelemetry import trace as trace_api
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import SimpleSpanProcessor
from opentelemetry.sdk.trace.export.in_memory_span_exporter import (
    InMemorySpanExporter,
)

from agentscope import _config
from agentscope.agent import AgentBase
from agentscope.embedding import EmbeddingModelBase
from agentscope.formatter import FormatterBase
from agentscope.message import (
    TextBlock,
    Msg,
    ToolUseBlock,
)
from agentscope.model import ChatModelBase, ChatResponse
from agentscope.tool import Toolkit, ToolResponse
from agentscope.tracing import (
    trace,
    trace_llm,
    trace_reply,
    trace_format,
    trace_embedding,
)
from agentscope.tracing._attributes import (
    OperationNameValues,
    ProviderNameValues,
    SpanAttributes as GenAISpanAttributes,
)
from agentscope.tracing._types import (
    SpanAttributes as LegacySpanAttributes,
    SpanKind,
)


class TracingTest(IsolatedAsyncioTestCase):
    """Test cases for tracing functionality"""

    async def asyncSetUp(self) -> None:
        """Set up the environment"""
        _config.trace_enabled = True
        self.prev_tracer_provider = trace_api.get_tracer_provider()
        self.prev_raw_tracer_provider = getattr(
            trace_api,
            "_TRACER_PROVIDER",
            None,
        )
        self.prev_tracer_provider_done = getattr(
            trace_api._TRACER_PROVIDER_SET_ONCE,
            "_done",
            False,
        )
        self.span_exporter = InMemorySpanExporter()
        tracer_provider = TracerProvider()
        tracer_provider.add_span_processor(
            SimpleSpanProcessor(self.span_exporter),
        )
        trace_api._TRACER_PROVIDER = None
        trace_api._TRACER_PROVIDER_SET_ONCE._done = False
        trace_api._set_tracer_provider(tracer_provider, False)

    def _decoded_attr(self, span, key: str) -> Any:
        """Decode JSON-serialized span attributes."""
        value = span.attributes[key]
        if isinstance(value, str):
            return json.loads(value)
        return value

    def _get_span(self, name: str):
        """Return the named finished span."""
        for span in self.span_exporter.get_finished_spans():
            if span.name == name:
                return span
        self.fail(f"Span {name!r} not found")

    async def test_trace(self) -> None:
        """Test the basic tracing functionality"""

        @trace(name="test_func")
        async def test_func(x: int) -> int:
            """Test async function""" ""
            return x * 2

        result = await test_func(5)
        self.assertEqual(result, 10)

        @trace(name="test_gen")
        async def test_gen() -> AsyncGenerator[str, None]:
            """Test async generator"""
            for i in range(3):
                yield f"chunk_{i}"

        results = [_ async for _ in test_gen()]
        self.assertListEqual(results, ["chunk_0", "chunk_1", "chunk_2"])

        @trace(name="test_func_return_with_sync_gen")
        async def test_func_return_with_sync_gen() -> Generator[
            str,
            None,
            None,
        ]:
            """Test async func returning sync generator"""

            def sync_gen() -> Generator[str, None, None]:
                """sync generator"""
                for i in range(3):
                    yield f"sync_chunk_{i}"

            return sync_gen()

        results = list(await test_func_return_with_sync_gen())
        self.assertListEqual(
            results,
            ["sync_chunk_0", "sync_chunk_1", "sync_chunk_2"],
        )

        @trace(name="sync_func")
        def sync_func(x: int) -> int:
            """Test synchronous function"""
            return x + 3

        result = sync_func(4)
        self.assertEqual(result, 7)

        @trace(name="sync_gen")
        def sync_gen() -> Generator[str, None, None]:
            """Test synchronous generator"""
            for i in range(3):
                yield f"sync_chunk_{i}"

        results = list(sync_gen())
        self.assertListEqual(
            results,
            ["sync_chunk_0", "sync_chunk_1", "sync_chunk_2"],
        )

        @trace(name="sync_func_return_with_async_gen")
        def sync_func_return_with_async_gen() -> AsyncGenerator[str, None]:
            """Test sync func returning async generator"""

            async def async_gen() -> AsyncGenerator[str, None]:
                """async generator"""
                for i in range(3):
                    yield f"chunk_{i}"

            return async_gen()

        results = [_ async for _ in sync_func_return_with_async_gen()]
        self.assertListEqual(results, ["chunk_0", "chunk_1", "chunk_2"])

        # Error handling
        @trace(name="error_sync_func")
        def error_sync_func() -> int:
            """Test error handling in sync function"""
            raise ValueError("Negative value not allowed")

        with self.assertRaises(ValueError):
            error_sync_func()

        @trace(name="error_async_func")
        async def error_async_func() -> int:
            """Test error handling in async function"""
            raise ValueError("Negative value not allowed")

        with self.assertRaises(ValueError):
            await error_async_func()

    async def test_trace_llm(self) -> None:
        """Test tracing LLM"""

        class LLM(ChatModelBase):
            """Test LLM class"""

            def __init__(self, stream: bool, raise_error: bool) -> None:
                """Initialize LLM"""
                super().__init__("test", stream)
                self.raise_error = raise_error

            @trace_llm
            async def __call__(
                self,
                messages: list[dict],
                **kwargs: Any,
            ) -> AsyncGenerator[ChatResponse, None] | ChatResponse:
                """Simulate LLM call"""

                if self.raise_error:
                    raise ValueError("Simulated error in LLM call")

                if self.stream:

                    async def generator() -> AsyncGenerator[
                        ChatResponse,
                        None,
                    ]:
                        for i in range(3):
                            yield ChatResponse(
                                id=f"msg_{i}",
                                content=[
                                    TextBlock(
                                        type="text",
                                        text="x" * (i + 1),
                                    ),
                                ],
                            )

                    return generator()
                return ChatResponse(
                    id="msg_0",
                    content=[
                        TextBlock(
                            type="text",
                            text="Hello, world!",
                        ),
                    ],
                )

        stream_llm = LLM(True, False)
        res = [_.content async for _ in await stream_llm([])]
        self.assertListEqual(
            res,
            [
                [TextBlock(type="text", text="x")],
                [TextBlock(type="text", text="xx")],
                [TextBlock(type="text", text="xxx")],
            ],
        )
        stream_span = self._get_span("LLM.__call__")
        self.assertEqual(
            self._decoded_attr(
                stream_span,
                GenAISpanAttributes.GEN_AI_OUTPUT_MESSAGES,
            )[0]["content"][0]["content"],
            "xxx",
        )

        non_stream_llm = LLM(False, False)
        res = await non_stream_llm([])
        self.assertListEqual(
            res.content,
            [
                TextBlock(type="text", text="Hello, world!"),
            ],
        )

        error_llm = LLM(False, True)
        with self.assertRaises(ValueError):
            await error_llm([])

    async def test_trace_reply(self) -> None:
        """Test tracing reply"""

        class Agent(AgentBase):
            """Test Agent class"""

            @trace_reply
            async def reply(self, raise_error: bool = False) -> Msg:
                """Simulate agent reply"""
                if raise_error:
                    raise ValueError("Simulated error in reply")
                return Msg(
                    "assistant",
                    [TextBlock(type="text", text="Hello, world!")],
                    "assistant",
                )

            async def observe(self, msg: Msg) -> None:
                raise NotImplementedError()

            async def handle_interrupt(
                self,
                *args: Any,
                **kwargs: Any,
            ) -> Msg:
                """Handle interrupt"""
                raise NotImplementedError()

        agent = Agent()
        res = await agent()
        self.assertListEqual(
            res.content,
            [TextBlock(type="text", text="Hello, world!")],
        )

        with self.assertRaises(ValueError):
            await agent.reply(raise_error=True)

    async def test_trace_format(self) -> None:
        """Test tracing formatter"""

        class Formatter(FormatterBase):
            """Test Formatter class"""

            @trace_format
            async def format(self, raise_error: bool = False) -> list[dict]:
                """Simulate formatting"""
                if raise_error:
                    raise ValueError("Simulated error in formatting")
                return [{"role": "user", "content": "Hello, world!"}]

        formatter = Formatter()
        res = await formatter.format()
        self.assertListEqual(
            res,
            [{"role": "user", "content": "Hello, world!"}],
        )

        with self.assertRaises(ValueError):
            await formatter.format(raise_error=True)

    async def test_trace_toolkit(self) -> None:
        """Test tracing toolkit"""
        toolkit = Toolkit()

        def func(raise_error: bool) -> ToolResponse:
            """Test tool function"""
            if raise_error:
                raise ValueError("Simulated error in tool function")
            return ToolResponse(
                content=[
                    TextBlock(type="text", text="Tool executed successfully"),
                ],
            )

        toolkit.register_tool_function(func)
        res = await toolkit.call_tool_function(
            ToolUseBlock(
                type="tool_use",
                id="xxx",
                name="func",
                input={"raise_error": False},
            ),
        )
        async for chunk in res:
            self.assertListEqual(
                chunk.content,
                [TextBlock(type="text", text="Tool executed successfully")],
            )
        res = await toolkit.call_tool_function(
            ToolUseBlock(
                type="tool_use",
                id="xxx",
                name="func",
                input={"raise_error": True},
            ),
        )
        async for chunk in res:
            self.assertListEqual(
                chunk.content,
                [
                    TextBlock(
                        type="text",
                        text="Error: Simulated error in tool function",
                    ),
                ],
            )

        async def gen_func(
            raise_error: bool,
        ) -> AsyncGenerator[ToolResponse, None]:
            """Test async generator tool function"""
            yield ToolResponse(
                content=[TextBlock(type="text", text="Chunk 0")],
            )
            if raise_error:
                raise ValueError(
                    "Simulated error in async generator tool function",
                )
            yield ToolResponse(
                content=[TextBlock(type="text", text="Chunk 1")],
            )

        toolkit.register_tool_function(gen_func)
        self.span_exporter.clear()
        res = await toolkit.call_tool_function(
            ToolUseBlock(
                type="tool_use",
                id="xxx",
                name="gen_func",
                input={"raise_error": False},
            ),
        )
        index = 0
        async for chunk in res:
            self.assertListEqual(
                chunk.content,
                [TextBlock(type="text", text=f"Chunk {index}")],
            )
            index += 1
        tool_span = self._get_span("call_tool_function")
        self.assertIn(
            "Chunk 1",
            self._decoded_attr(
                tool_span,
                GenAISpanAttributes.GEN_AI_TOOL_CALL_RESULT,
            ),
        )

        res = await toolkit.call_tool_function(
            ToolUseBlock(
                type="tool_use",
                id="xxx",
                name="gen_func",
                input={"raise_error": True},
            ),
        )
        with self.assertRaises(ValueError):
            async for _ in res:
                pass

    async def test_trace_embedding(self) -> None:
        """Test tracing embedding"""

        class EmbeddingModel(EmbeddingModelBase):
            """Test embedding model class"""

            def __init__(self) -> None:
                """Initialize embedding model"""
                super().__init__("test_embedding", 3)

            @trace_embedding
            async def __call__(self, raise_error: bool) -> list[list[float]]:
                """Simulate embedding call"""
                if raise_error:
                    raise ValueError("Simulated error in embedding call")
                return [[0, 1, 2]]

        model = EmbeddingModel()
        res = await model(False)
        self.assertListEqual(res, [[0, 1, 2]])

        with self.assertRaises(ValueError):
            await model(True)

    async def test_remaining_tracing_decorators_emit_dual_attributes(
        self,
    ) -> None:
        """Generic, formatter, and embedding spans keep both attr layers."""

        @trace(name="generic_stream")
        async def generic_stream() -> AsyncGenerator[str, None]:
            for chunk in ("first", "last"):
                yield chunk

        class OpenAIChatFormatter(FormatterBase):
            @trace_format
            async def format(self) -> list[dict]:
                return [{"role": "user", "content": "Hello, world!"}]

        class OpenAIEmbeddingModel(EmbeddingModelBase):
            def __init__(self) -> None:
                super().__init__("embed-small", 1024)

            @trace_embedding
            async def __call__(self) -> list[list[float]]:
                return [[0.0, 1.0, 2.0]]

        self.span_exporter.clear()
        formatter = OpenAIChatFormatter()
        embedding_model = OpenAIEmbeddingModel()

        generic_result = [_ async for _ in generic_stream()]
        formatter_result = await formatter.format()
        embedding_result = await embedding_model()

        self.assertEqual(generic_result, ["first", "last"])
        self.assertEqual(
            formatter_result,
            [{"role": "user", "content": "Hello, world!"}],
        )
        self.assertEqual(embedding_result, [[0.0, 1.0, 2.0]])

        generic_span = self._get_span("generic_stream")
        self.assertEqual(
            self._decoded_attr(
                generic_span,
                LegacySpanAttributes.SPAN_KIND,
            ),
            SpanKind.COMMON.value,
        )
        self.assertEqual(
            generic_span.attributes[GenAISpanAttributes.GEN_AI_OPERATION_NAME],
            OperationNameValues.INVOKE_GENERIC_FUNCTION,
        )
        self.assertEqual(
            generic_span.attributes[
                GenAISpanAttributes.AGENTSCOPE_FUNCTION_NAME
            ],
            "generic_stream",
        )
        self.assertEqual(
            self._decoded_attr(
                generic_span,
                GenAISpanAttributes.AGENTSCOPE_FUNCTION_OUTPUT,
            ),
            "last",
        )
        self.assertEqual(
            self._decoded_attr(
                generic_span,
                LegacySpanAttributes.OUTPUT,
            ),
            "last",
        )

        formatter_span = self._get_span("OpenAIChatFormatter.format")
        self.assertEqual(
            self._decoded_attr(
                formatter_span,
                LegacySpanAttributes.SPAN_KIND,
            ),
            SpanKind.FORMATTER.value,
        )
        self.assertEqual(
            formatter_span.attributes[
                GenAISpanAttributes.GEN_AI_OPERATION_NAME
            ],
            OperationNameValues.FORMATTER,
        )
        self.assertEqual(
            formatter_span.attributes[
                GenAISpanAttributes.AGENTSCOPE_FORMAT_TARGET
            ],
            ProviderNameValues.OPENAI,
        )
        self.assertEqual(
            formatter_span.attributes[
                GenAISpanAttributes.AGENTSCOPE_FORMAT_COUNT
            ],
            1,
        )
        self.assertEqual(
            self._decoded_attr(
                formatter_span,
                LegacySpanAttributes.OUTPUT,
            ),
            formatter_result,
        )

        embedding_span = self._get_span("OpenAIEmbeddingModel.__call__")
        self.assertEqual(
            self._decoded_attr(
                embedding_span,
                LegacySpanAttributes.SPAN_KIND,
            ),
            SpanKind.EMBEDDING.value,
        )
        self.assertEqual(
            embedding_span.attributes[
                GenAISpanAttributes.GEN_AI_OPERATION_NAME
            ],
            OperationNameValues.EMBEDDINGS,
        )
        self.assertEqual(
            embedding_span.attributes[
                GenAISpanAttributes.GEN_AI_PROVIDER_NAME
            ],
            ProviderNameValues.OPENAI,
        )
        self.assertEqual(
            embedding_span.attributes[
                GenAISpanAttributes.GEN_AI_REQUEST_MODEL
            ],
            "embed-small",
        )
        self.assertEqual(
            self._decoded_attr(
                embedding_span,
                LegacySpanAttributes.META,
            ),
            {"model_name": "embed-small"},
        )
        self.assertEqual(
            self._decoded_attr(
                embedding_span,
                LegacySpanAttributes.OUTPUT,
            ),
            embedding_result,
        )

    async def asyncTearDown(self) -> None:
        """Tear down the environment"""
        _config.trace_enabled = True
        trace_api._TRACER_PROVIDER = self.prev_raw_tracer_provider
        trace_api._TRACER_PROVIDER_SET_ONCE._done = (
            self.prev_tracer_provider_done
        )
