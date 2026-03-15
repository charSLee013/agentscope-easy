# -*- coding: utf-8 -*-
"""Extract tracing attributes from AgentScope runtime objects."""
from typing import Any

from .. import _config
from ..message import Msg, ToolUseBlock
from ._attributes import (
    OperationNameValues,
    ProviderNameValues,
    SpanAttributes,
)
from ._converter import _convert_block_to_part
from ._utils import _serialize_to_str


_CLASS_NAME_MAP = {
    "anthropic": ProviderNameValues.ANTHROPIC,
    "dashscope": ProviderNameValues.DASHSCOPE,
    "deepseek": ProviderNameValues.DEEPSEEK,
    "gemini": ProviderNameValues.GCP_GEMINI,
    "ollama": ProviderNameValues.OLLAMA,
    "openai": ProviderNameValues.OPENAI,
}


def _get_provider_name(instance: Any) -> str:
    """Infer provider name from the model class name."""
    class_name = instance.__class__.__name__.lower()
    for prefix, provider in _CLASS_NAME_MAP.items():
        if class_name.startswith(prefix):
            return provider
    return "unknown"


def _get_formatter_target(instance: Any) -> str:
    """Infer formatter target from the formatter class name."""
    class_name = instance.__class__.__name__
    prefix_key = (
        class_name.removesuffix("ChatFormatter")
        .removesuffix("MultiAgentFormatter")
        .removesuffix("Formatter")
        .lower()
    )
    return _CLASS_NAME_MAP.get(prefix_key, "unknown")


def _get_tool_definitions(
    tools: list[dict[str, Any]] | None,
    tool_choice: str | None,
) -> str | None:
    """Flatten tool definitions into a tracing payload."""
    if not tools or tool_choice == "none":
        return None

    flattened = []
    for tool in tools:
        function = tool.get("function")
        if not isinstance(function, dict):
            continue
        flattened.append(
            {
                "type": tool.get("type", "function"),
                "name": function.get("name"),
                "description": function.get("description"),
                "parameters": function.get("parameters"),
            },
        )

    if not flattened:
        return None
    return _serialize_to_str(flattened)


def _get_agent_messages(msg: Msg | list[Msg] | None) -> list[dict[str, Any]]:
    """Normalize one or more AgentScope messages into tracing messages."""
    if msg is None:
        return []

    msgs = [msg] if isinstance(msg, Msg) else list(msg)
    normalized = []
    for item in msgs:
        normalized.append(
            {
                "role": item.role,
                "name": item.name,
                "content": [
                    part
                    for block in item.get_content_blocks()
                    if (part := _convert_block_to_part(block)) is not None
                ],
            },
        )
    return normalized


def _get_agent_request_attributes(
    agent: Any,
    args: tuple[Any, ...],
    kwargs: dict[str, Any],
) -> dict[str, Any]:
    """Build request attributes for an agent reply span."""
    input_msg = kwargs.get("msg")
    if input_msg is None and args:
        input_msg = args[0]

    return {
        SpanAttributes.GEN_AI_CONVERSATION_ID: _config.run_id,
        SpanAttributes.GEN_AI_OPERATION_NAME: OperationNameValues.INVOKE_AGENT,
        SpanAttributes.GEN_AI_INPUT_MESSAGES: _serialize_to_str(
            _get_agent_messages(input_msg),
        ),
        SpanAttributes.META: _serialize_to_str(
            {
                "id": getattr(agent, "id", None),
                "name": getattr(agent, "name", None),
            },
        ),
    }


def _get_agent_response_attributes(msg: Msg) -> dict[str, Any]:
    """Build response attributes for an agent reply span."""
    return {
        SpanAttributes.GEN_AI_OUTPUT_MESSAGES: _serialize_to_str(
            _get_agent_messages(msg),
        ),
        SpanAttributes.OUTPUT: _serialize_to_str(msg),
    }


def _get_tool_request_attributes(
    toolkit: Any,
    tool_call: ToolUseBlock,
) -> dict[str, Any]:
    """Build request attributes for a tool-execution span."""
    return {
        SpanAttributes.GEN_AI_CONVERSATION_ID: _config.run_id,
        SpanAttributes.GEN_AI_OPERATION_NAME: OperationNameValues.EXECUTE_TOOL,
        SpanAttributes.GEN_AI_TOOL_CALL_ID: tool_call.get("id", ""),
        SpanAttributes.GEN_AI_TOOL_NAME: tool_call.get("name", ""),
        SpanAttributes.GEN_AI_TOOL_CALL_ARGUMENTS: _serialize_to_str(
            tool_call.get("input", {}),
        ),
        SpanAttributes.META: _serialize_to_str(tool_call),
    }


def _get_tool_response_attributes(response: Any) -> dict[str, Any]:
    """Build response attributes for a tool span."""
    return {
        SpanAttributes.GEN_AI_TOOL_CALL_RESULT: _serialize_to_str(response),
        SpanAttributes.OUTPUT: _serialize_to_str(response),
    }


def _get_llm_request_attributes(
    model: Any,
    args: tuple[Any, ...],
    kwargs: dict[str, Any],
) -> dict[str, Any]:
    """Build request attributes for an LLM span."""
    return {
        SpanAttributes.GEN_AI_CONVERSATION_ID: _config.run_id,
        SpanAttributes.GEN_AI_OPERATION_NAME: OperationNameValues.CHAT,
        SpanAttributes.GEN_AI_PROVIDER_NAME: _get_provider_name(model),
        SpanAttributes.GEN_AI_REQUEST_MODEL: getattr(
            model,
            "model_name",
            "unknown_model",
        ),
        SpanAttributes.GEN_AI_TOOL_DEFINITIONS: _get_tool_definitions(
            kwargs.get("tools"),
            kwargs.get("tool_choice"),
        ),
        SpanAttributes.INPUT: _serialize_to_str(
            {
                "args": args,
                "kwargs": kwargs,
            },
        ),
    }


def _get_llm_response_attributes(response: Any) -> dict[str, Any]:
    """Build response attributes for an LLM span."""
    attrs = {
        SpanAttributes.OUTPUT: _serialize_to_str(response),
    }

    content = getattr(response, "content", None)
    if content is not None:
        attrs[SpanAttributes.GEN_AI_OUTPUT_MESSAGES] = _serialize_to_str(
            [
                {
                    "role": "assistant",
                    "content": [
                        part
                        for block in content
                        if (part := _convert_block_to_part(block)) is not None
                    ],
                },
            ],
        )

    return attrs


def _get_formatter_request_attributes(
    formatter: Any,
    args: tuple[Any, ...],
    kwargs: dict[str, Any],
) -> dict[str, Any]:
    """Build request attributes for a formatter span."""
    return {
        SpanAttributes.GEN_AI_CONVERSATION_ID: _config.run_id,
        SpanAttributes.GEN_AI_OPERATION_NAME: OperationNameValues.FORMATTER,
        SpanAttributes.AGENTSCOPE_FORMAT_TARGET: _get_formatter_target(
            formatter,
        ),
        SpanAttributes.AGENTSCOPE_FUNCTION_INPUT: _serialize_to_str(
            {
                "args": args,
                "kwargs": kwargs,
            },
        ),
    }


def _get_formatter_response_attributes(response: Any) -> dict[str, Any]:
    """Build response attributes for a formatter span."""
    attrs = {
        SpanAttributes.AGENTSCOPE_FUNCTION_OUTPUT: _serialize_to_str(
            response,
        ),
    }
    if isinstance(response, list):
        attrs[SpanAttributes.AGENTSCOPE_FORMAT_COUNT] = len(response)
    return attrs


def _get_generic_function_request_attributes(
    function_name: str,
    args: tuple[Any, ...],
    kwargs: dict[str, Any],
) -> dict[str, Any]:
    """Build request attributes for a generic traced function."""
    return {
        SpanAttributes.GEN_AI_CONVERSATION_ID: _config.run_id,
        SpanAttributes.GEN_AI_OPERATION_NAME: (
            OperationNameValues.INVOKE_GENERIC_FUNCTION
        ),
        SpanAttributes.AGENTSCOPE_FUNCTION_NAME: function_name,
        SpanAttributes.AGENTSCOPE_FUNCTION_INPUT: _serialize_to_str(
            {
                "args": args,
                "kwargs": kwargs,
            },
        ),
    }


def _get_generic_function_response_attributes(
    response: Any,
) -> dict[str, Any]:
    """Build response attributes for a generic traced function."""
    return {
        SpanAttributes.AGENTSCOPE_FUNCTION_OUTPUT: _serialize_to_str(
            response,
        ),
    }


def _get_embedding_request_attributes(
    model: Any,
    args: tuple[Any, ...],
    kwargs: dict[str, Any],
) -> dict[str, Any]:
    """Build request attributes for an embedding span."""
    dimensions = kwargs.get("dimensions")
    if dimensions is None:
        dimensions = getattr(model, "dimensions", None)

    return {
        SpanAttributes.GEN_AI_CONVERSATION_ID: _config.run_id,
        SpanAttributes.GEN_AI_OPERATION_NAME: OperationNameValues.EMBEDDINGS,
        SpanAttributes.GEN_AI_PROVIDER_NAME: _get_provider_name(model),
        SpanAttributes.GEN_AI_REQUEST_MODEL: getattr(
            model,
            "model_name",
            "unknown_model",
        ),
        SpanAttributes.GEN_AI_EMBEDDINGS_DIMENSION_COUNT: dimensions,
        SpanAttributes.AGENTSCOPE_FUNCTION_INPUT: _serialize_to_str(
            {
                "args": args,
                "kwargs": kwargs,
            },
        ),
    }


def _get_embedding_response_attributes(response: Any) -> dict[str, Any]:
    """Build response attributes for an embedding span."""
    return {
        SpanAttributes.AGENTSCOPE_FUNCTION_OUTPUT: _serialize_to_str(
            response,
        ),
    }
