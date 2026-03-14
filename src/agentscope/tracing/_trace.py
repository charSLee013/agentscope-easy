# -*- coding: utf-8 -*-
"""The tracing decorators for agent, formatter, toolkit, chat and embedding
models."""
import inspect
from functools import wraps
from typing import (
    Generator,
    AsyncGenerator,
    Callable,
    Any,
    Coroutine,
    TypeVar,
    TYPE_CHECKING,
)

import aioitertools

from ._attributes import (
    SpanAttributes as GenAISpanAttributes,
    _serialize_to_str,
)
from ._extractor import (
    _get_agent_request_attributes,
    _get_agent_response_attributes,
    _get_embedding_request_attributes,
    _get_embedding_response_attributes,
    _get_formatter_request_attributes,
    _get_formatter_response_attributes,
    _get_generic_function_request_attributes,
    _get_generic_function_response_attributes,
    _get_llm_request_attributes,
    _get_llm_response_attributes,
    _get_tool_request_attributes,
    _get_tool_response_attributes,
)
from ._setup import _get_tracer
from .. import _config
from ..embedding._embedding_base import EmbeddingModelBase
from .._logging import logger
from ._types import SpanKind, SpanAttributes as LegacySpanAttributes

if TYPE_CHECKING:
    from ..agent import AgentBase
    from ..formatter import FormatterBase
    from ..tool import (
        Toolkit,
        ToolResponse,
    )
    from ..message import (
        Msg,
        ToolUseBlock,
    )
    from ..embedding import EmbeddingResponse
    from ..model import ChatResponse
    from ..model._model_base import ChatModelBase
    from opentelemetry.trace import Span
else:
    Toolkit = "Toolkit"
    ToolResponse = "ToolResponse"
    Msg = "Msg"
    ToolUseBlock = "ToolUseBlock"
    EmbeddingResponse = "EmbeddingResponse"
    ChatResponse = "ChatResponse"
    Span = "Span"


T = TypeVar("T")


def _check_tracing_enabled() -> bool:
    """Check if the OpenTelemetry tracer is initialized in AgentScope with an
    endpoint.

    TODO: We expect an OpenTelemetry official interface to check if the
     tracer is initialized. Leaving this function here as a temporary
     solution.
    """
    return _config.trace_enabled


def _clean_attributes(attributes: dict[str, Any]) -> dict[str, Any]:
    """Drop None values before passing attributes to OpenTelemetry."""
    return {
        key: value for key, value in attributes.items() if value is not None
    }


def _merge_attributes(*attribute_groups: dict[str, Any]) -> dict[str, Any]:
    """Merge multiple attribute dictionaries and drop None values."""
    merged: dict[str, Any] = {}
    for group in attribute_groups:
        merged.update(group)
    return _clean_attributes(merged)


def _legacy_attributes(
    span_kind: SpanKind,
    input_payload: Any,
    meta_payload: Any,
) -> dict[str, str]:
    """Build legacy tracing attributes used by evaluation stats."""
    return {
        LegacySpanAttributes.SPAN_KIND: _serialize_to_str(span_kind),
        LegacySpanAttributes.PROJECT_RUN_ID: _serialize_to_str(
            _config.run_id,
        ),
        LegacySpanAttributes.INPUT: _serialize_to_str(input_payload),
        LegacySpanAttributes.META: _serialize_to_str(meta_payload),
    }


def _set_span_success(span: Span) -> None:
    """Mark a span as successful and close it."""
    import opentelemetry

    span.set_status(opentelemetry.trace.StatusCode.OK)
    span.end()


def _set_span_error(span: Span, error: Exception) -> None:
    """Mark a span as failed and close it."""
    import opentelemetry

    span.set_status(opentelemetry.trace.StatusCode.ERROR, str(error))
    span.record_exception(error)
    span.end()


def _stream_response_attributes(span: Span, chunk: Any) -> dict[str, Any]:
    """Infer response attributes for streaming spans by legacy span kind."""
    span_kind = getattr(span, "attributes", {}).get(
        LegacySpanAttributes.SPAN_KIND,
    )

    if span_kind == SpanKind.LLM.value:
        return _get_llm_response_attributes(chunk)

    if span_kind == SpanKind.TOOL.value:
        return _get_tool_response_attributes(chunk)

    return _get_generic_function_response_attributes(chunk)


def _trace_sync_generator_wrapper(
    res: Generator[T, None, None],
    span: Span,
) -> Generator[T, None, None]:
    """Trace the sync generator output with OpenTelemetry."""

    has_error = False

    try:
        last_chunk = None
        for chunk in res:
            last_chunk = chunk
            yield chunk
    except Exception as e:
        has_error = True
        _set_span_error(span, e)
        raise e from None

    finally:
        if not has_error:
            # Set the last chunk as output
            span.set_attributes(
                _merge_attributes(
                    {
                        LegacySpanAttributes.OUTPUT: _serialize_to_str(
                            last_chunk,
                        ),
                    },
                    _stream_response_attributes(span, last_chunk),
                ),
            )
            _set_span_success(span)


async def _trace_async_generator_wrapper(
    res: AsyncGenerator[T, None],
    span: Span,
) -> AsyncGenerator[T, None]:
    """Trace the async generator output with OpenTelemetry.

    Args:
        res (`AsyncGenerator[T, None]`):
            The generator or async generator to be traced.
        span (`Span`):
            The OpenTelemetry span to be used for tracing.

    Yields:
        `T`:
            The output of the async generator.
    """
    has_error = False

    try:
        last_chunk = None
        async for chunk in aioitertools.iter(res):
            last_chunk = chunk
            yield chunk

    except Exception as e:
        has_error = True
        _set_span_error(span, e)
        raise e from None

    finally:
        if not has_error:
            # Set the last chunk as output
            span.set_attributes(
                _merge_attributes(
                    {
                        LegacySpanAttributes.OUTPUT: _serialize_to_str(
                            last_chunk,
                        ),
                    },
                    _stream_response_attributes(span, last_chunk),
                ),
            )
            _set_span_success(span)


def trace(
    name: str,
) -> Callable:
    """A generic tracing decorator for synchronous and asynchronous functions.

    Args:
        name (`str`):
            The name of the span to be created.

    Returns:
        `Callable`:
            Returns a decorator that wraps the given function with
            OpenTelemetry tracing.
    """

    def decorator(
        func: Callable,
    ) -> Callable:
        """A decorator that wraps the given function with OpenTelemetry tracing

        Args:
            func (`Callable`):
                The function to be traced, which can be sync or async function,
                and returns an object or a generator.

        Returns:
            `Callable`:
                A wrapper function that traces the function call and handles
                input/output and exceptions.
        """
        # Async function
        if inspect.iscoroutinefunction(func):

            @wraps(func)
            async def wrapper(
                *args: Any,
                **kwargs: Any,
            ) -> Any:
                """The wrapper function for tracing the sync function call."""
                if not _check_tracing_enabled():
                    return await func(*args, **kwargs)

                tracer = _get_tracer()
                attributes = _merge_attributes(
                    _legacy_attributes(
                        SpanKind.COMMON,
                        {
                            "args": args,
                            "kwargs": kwargs,
                        },
                        {},
                    ),
                    _get_generic_function_request_attributes(
                        name,
                        args,
                        kwargs,
                    ),
                )

                with tracer.start_as_current_span(
                    name=name,
                    attributes=attributes,
                    end_on_exit=False,
                ) as span:
                    try:
                        res = await func(*args, **kwargs)

                        # If generator or async generator
                        if isinstance(res, AsyncGenerator):
                            return _trace_async_generator_wrapper(res, span)
                        if isinstance(res, Generator):
                            return _trace_sync_generator_wrapper(res, span)

                        # non-generator result
                        span.set_attributes(
                            _merge_attributes(
                                {
                                    LegacySpanAttributes.OUTPUT: (
                                        _serialize_to_str(res)
                                    ),
                                },
                                _get_generic_function_response_attributes(res),
                            ),
                        )
                        _set_span_success(span)
                        return res

                    except Exception as e:
                        _set_span_error(span, e)
                        raise e from None

            return wrapper

        # Sync function
        @wraps(func)
        def sync_wrapper(
            *args: Any,
            **kwargs: Any,
        ) -> Any:
            """The wrapper function for tracing the sync function call."""
            if not _check_tracing_enabled():
                return func(*args, **kwargs)

            tracer = _get_tracer()
            attributes = _merge_attributes(
                _legacy_attributes(
                    SpanKind.COMMON,
                    {
                        "args": args,
                        "kwargs": kwargs,
                    },
                    {},
                ),
                _get_generic_function_request_attributes(
                    name,
                    args,
                    kwargs,
                ),
            )

            with tracer.start_as_current_span(
                name=name,
                attributes=attributes,
                end_on_exit=False,
            ) as span:
                try:
                    res = func(*args, **kwargs)

                    # If generator or async generator
                    if isinstance(res, AsyncGenerator):
                        return _trace_async_generator_wrapper(res, span)
                    if isinstance(res, Generator):
                        return _trace_sync_generator_wrapper(res, span)

                    # non-generator result
                    span.set_attributes(
                        _merge_attributes(
                            {
                                LegacySpanAttributes.OUTPUT: _serialize_to_str(
                                    res,
                                ),
                            },
                            _get_generic_function_response_attributes(res),
                        ),
                    )
                    _set_span_success(span)
                    return res

                except Exception as e:
                    _set_span_error(span, e)
                    raise e from None

        return sync_wrapper

    return decorator


def trace_toolkit(
    func: Callable[
        ...,
        Coroutine[Any, Any, AsyncGenerator[ToolResponse, None]],
    ],
) -> Callable[..., Coroutine[Any, Any, AsyncGenerator[ToolResponse, None]]]:
    """Trace the toolkit `call_tool_function` method with OpenTelemetry."""

    @wraps(func)
    async def wrapper(
        self: Toolkit,
        tool_call: ToolUseBlock,
    ) -> AsyncGenerator[ToolResponse, None]:
        """The wrapper function for tracing the toolkit call_tool_function
        method."""
        if not _check_tracing_enabled():
            return await func(self, tool_call=tool_call)

        tracer = _get_tracer()
        attributes = _merge_attributes(
            _legacy_attributes(
                SpanKind.TOOL,
                {"tool_call": tool_call},
                {**tool_call},
            ),
            _get_tool_request_attributes(self, tool_call),
            {
                GenAISpanAttributes.AGENTSCOPE_FUNCTION_NAME: (
                    f"{self.__class__.__name__}.{func.__name__}"
                ),
            },
        )

        with tracer.start_as_current_span(
            f"{func.__name__}",
            attributes=attributes,
            end_on_exit=False,
        ) as span:
            try:
                # Call the toolkit function
                res = await func(self, tool_call=tool_call)

                # The result must be an AsyncGenerator of ToolResponse objects
                return _trace_async_generator_wrapper(res, span)

            except Exception as e:
                _set_span_error(span, e)
                raise e from None

    return wrapper


def trace_reply(
    func: Callable[..., Coroutine[Any, Any, Msg]],
) -> Callable[..., Coroutine[Any, Any, Msg]]:
    """Trace the agent reply call with OpenTelemetry.

    Args:
        func (`Callable[..., Coroutine[Any, Any, Msg]]`):
            The agent async reply function to be traced.

    Returns:
        `Callable[..., Coroutine[Any, Any, Msg]]`:
            A wrapper function that traces the agent reply call and handles
            input/output and exceptions.
    """

    @wraps(func)
    async def wrapper(
        self: "AgentBase",
        *args: Any,
        **kwargs: Any,
    ) -> Msg:
        """The wrapper function for tracing the agent reply function call."""
        if not _check_tracing_enabled():
            return await func(self, *args, **kwargs)

        from ..agent import AgentBase

        if not isinstance(self, AgentBase):
            logger.warning(
                "Skipping tracing for %s as the first argument"
                "is not an instance of AgentBase, but %s",
                func.__name__,
                type(self),
            )
            return await func(self, *args, **kwargs)

        agent_name = self.name if hasattr(self, "name") else None
        tracer = _get_tracer()
        attributes = _merge_attributes(
            _legacy_attributes(
                SpanKind.AGENT,
                {
                    "args": args,
                    "kwargs": kwargs,
                },
                {
                    "id": self.id,
                    "name": agent_name,
                },
            ),
            _get_agent_request_attributes(self, args, kwargs),
            {
                GenAISpanAttributes.AGENTSCOPE_FUNCTION_NAME: (
                    f"{self.__class__.__name__}.{func.__name__}"
                ),
            },
        )

        with tracer.start_as_current_span(
            f"{self.__class__.__name__}.{func.__name__}",
            attributes=attributes,
            end_on_exit=False,
        ) as span:
            try:
                # Call the agent reply function
                res = await func(self, *args, **kwargs)

                # Set the output attribute
                span.set_attributes(
                    _merge_attributes(
                        {
                            LegacySpanAttributes.OUTPUT: _serialize_to_str(
                                res,
                            ),
                        },
                        _get_agent_response_attributes(res),
                    ),
                )
                _set_span_success(span)
                return res

            except Exception as e:
                _set_span_error(span, e)
                raise e from None

    return wrapper


def trace_embedding(
    func: Callable[..., Coroutine[Any, Any, EmbeddingResponse]],
) -> Callable[..., Coroutine[Any, Any, EmbeddingResponse]]:
    """Trace the embedding call with OpenTelemetry."""

    @wraps(func)
    async def wrapper(
        self: EmbeddingModelBase,
        *args: Any,
        **kwargs: Any,
    ) -> EmbeddingResponse:
        """The wrapper function for tracing the embedding call."""
        if not _check_tracing_enabled():
            return await func(self, *args, **kwargs)

        if not isinstance(self, EmbeddingModelBase):
            logger.warning(
                "Skipping tracing for %s as the first argument"
                "is not an instance of EmbeddingModelBase, but %s",
                func.__name__,
                type(self),
            )
            return await func(self, *args, **kwargs)

        tracer = _get_tracer()
        attributes = _merge_attributes(
            _legacy_attributes(
                SpanKind.EMBEDDING,
                {
                    "args": args,
                    "kwargs": kwargs,
                },
                {
                    "model_name": self.model_name,
                },
            ),
            _get_embedding_request_attributes(self, args, kwargs),
            {
                GenAISpanAttributes.AGENTSCOPE_FUNCTION_NAME: (
                    f"{self.__class__.__name__}.{func.__name__}"
                ),
            },
        )

        with tracer.start_as_current_span(
            f"{self.__class__.__name__}.{func.__name__}",
            attributes=attributes,
            end_on_exit=False,
        ) as span:
            try:
                # Call the embedding function
                res = await func(self, *args, **kwargs)

                # Set the output attribute
                span.set_attributes(
                    _merge_attributes(
                        {
                            LegacySpanAttributes.OUTPUT: _serialize_to_str(
                                res,
                            ),
                        },
                        _get_embedding_response_attributes(res),
                    ),
                )
                _set_span_success(span)
                return res

            except Exception as e:
                _set_span_error(span, e)
                raise e from None

    return wrapper


def trace_format(
    func: Callable[..., Coroutine[Any, Any, list[dict]]],
) -> Callable[..., Coroutine[Any, Any, list[dict]]]:
    """Trace the format function of the formatter with OpenTelemetry.

    Args:
        func (`Callable[..., Coroutine[Any, Any, list[dict]]]`):
            The async format function to be traced.

    Returns:
        `Callable[..., Coroutine[Any, Any, list[dict]]]`:
            An async wrapper function that traces the format call and handles
            input/output and exceptions.
    """

    @wraps(func)
    async def wrapper(
        self: "FormatterBase",
        *args: Any,
        **kwargs: Any,
    ) -> list[dict]:
        """Wrap the formatter __call__ method with OpenTelemetry tracing."""
        if not _check_tracing_enabled():
            return await func(self, *args, **kwargs)

        from ..formatter import FormatterBase

        if not isinstance(self, FormatterBase):
            logger.warning(
                "Skipping tracing for %s as the first argument"
                "is not an instance of FormatterBase, but %s",
                func.__name__,
                type(self),
            )
            return await func(self, *args, **kwargs)

        tracer = _get_tracer()
        attributes = _merge_attributes(
            _legacy_attributes(
                SpanKind.FORMATTER,
                {
                    "args": args,
                    "kwargs": kwargs,
                },
                {},
            ),
            _get_formatter_request_attributes(self, args, kwargs),
            {
                GenAISpanAttributes.AGENTSCOPE_FUNCTION_NAME: (
                    f"{self.__class__.__name__}.{func.__name__}"
                ),
            },
        )

        with tracer.start_as_current_span(
            f"{self.__class__.__name__}.{func.__name__}",
            attributes=attributes,
            end_on_exit=False,
        ) as span:
            try:
                # Call the formatter function
                res = await func(self, *args, **kwargs)

                # Set the output attribute
                span.set_attributes(
                    _merge_attributes(
                        {
                            LegacySpanAttributes.OUTPUT: _serialize_to_str(
                                res,
                            ),
                        },
                        _get_formatter_response_attributes(res),
                    ),
                )
                _set_span_success(span)
                return res

            except Exception as e:
                _set_span_error(span, e)
                raise e from None

    return wrapper


def trace_llm(
    func: Callable[
        ...,
        Coroutine[
            Any,
            Any,
            ChatResponse | AsyncGenerator[ChatResponse, None],
        ],
    ],
) -> Callable[
    ...,
    Coroutine[Any, Any, ChatResponse | AsyncGenerator[ChatResponse, None]],
]:
    """Trace the LLM call with OpenTelemetry.

    Args:
        func (`Callable`):
            The function to be traced, which should be a coroutine that
            returns either a `ChatResponse` or an `AsyncGenerator`
            of `ChatResponse`.

    Returns:
        `Callable`:
            A wrapper function that traces the LLM call and handles
            input/output and exceptions.
    """

    @wraps(func)
    async def async_wrapper(
        self: "ChatModelBase",
        *args: Any,
        **kwargs: Any,
    ) -> ChatResponse | AsyncGenerator[ChatResponse, None]:
        """The wrapper function for tracing the LLM call."""
        if not _check_tracing_enabled():
            return await func(self, *args, **kwargs)

        from ..model._model_base import ChatModelBase as _ChatModelBase

        if not isinstance(self, _ChatModelBase):
            logger.warning(
                "Skipping tracing for %s as the first argument"
                "is not an instance of ChatModelBase, but %s",
                func.__name__,
                type(self),
            )
            return await func(self, *args, **kwargs)

        tracer = _get_tracer()
        attributes = _merge_attributes(
            _legacy_attributes(
                SpanKind.LLM,
                {
                    "args": args,
                    "kwargs": kwargs,
                },
                {
                    "model_name": self.model_name,
                    "stream": self.stream,
                },
            ),
            _get_llm_request_attributes(self, args, kwargs),
            {
                GenAISpanAttributes.AGENTSCOPE_FUNCTION_NAME: (
                    f"{self.__class__.__name__}.__call__"
                ),
            },
        )

        # Begin the llm call span
        with tracer.start_as_current_span(
            f"{self.__class__.__name__}.__call__",
            attributes=attributes,
            end_on_exit=False,
        ) as span:
            try:
                # Must be an async calling
                res = await func(self, *args, **kwargs)

                # If the result is a AsyncGenerator
                if isinstance(res, AsyncGenerator):
                    return _trace_async_generator_wrapper(res, span)

                # non-generator result
                span.set_attributes(
                    _merge_attributes(
                        {
                            LegacySpanAttributes.OUTPUT: _serialize_to_str(
                                res,
                            ),
                        },
                        _get_llm_response_attributes(res),
                    ),
                )
                _set_span_success(span)
                return res

            except Exception as e:
                _set_span_error(span, e)
                raise e from None

    return async_wrapper
