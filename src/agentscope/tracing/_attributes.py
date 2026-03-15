# -*- coding: utf-8 -*-
"""Tracing attribute constants and compatibility exports."""

from ._utils import _serialize_to_str, _to_serializable  # noqa: F401


class SpanAttributes:
    """The span attributes."""

    SPAN_KIND = "span.kind"
    OUTPUT = "output"
    INPUT = "input"
    META = "metadata"
    PROJECT_RUN_ID = "project.run_id"

    GEN_AI_CONVERSATION_ID = "gen_ai.conversation.id"
    GEN_AI_OPERATION_NAME = "gen_ai.operation.name"
    GEN_AI_PROVIDER_NAME = "gen_ai.provider.name"
    GEN_AI_REQUEST_MODEL = "gen_ai.request.model"
    GEN_AI_INPUT_MESSAGES = "gen_ai.input.messages"
    GEN_AI_OUTPUT_MESSAGES = "gen_ai.output.messages"
    GEN_AI_TOOL_NAME = "gen_ai.tool.name"
    GEN_AI_TOOL_CALL_ID = "gen_ai.tool.call.id"
    GEN_AI_TOOL_CALL_ARGUMENTS = "gen_ai.tool.call.arguments"
    GEN_AI_TOOL_CALL_RESULT = "gen_ai.tool.call.result"
    GEN_AI_TOOL_DEFINITIONS = "gen_ai.tool.definitions"
    GEN_AI_EMBEDDINGS_DIMENSION_COUNT = "gen_ai.embeddings.dimension.count"

    AGENTSCOPE_FORMAT_TARGET = "agentscope.format.target"
    AGENTSCOPE_FORMAT_COUNT = "agentscope.format.count"
    AGENTSCOPE_FUNCTION_NAME = "agentscope.function.name"
    AGENTSCOPE_FUNCTION_INPUT = "agentscope.function.input"
    AGENTSCOPE_FUNCTION_OUTPUT = "agentscope.function.output"


class OperationNameValues:
    """Operation name values used by GenAI spans."""

    CHAT = "chat"
    FORMATTER = "format"
    EMBEDDINGS = "embeddings"
    INVOKE_AGENT = "invoke_agent"
    INVOKE_GENERIC_FUNCTION = "invoke_generic_function"
    EXECUTE_TOOL = "execute_tool"


class ProviderNameValues:
    """Provider name values used by GenAI spans."""

    ANTHROPIC = "anthropic"
    DASHSCOPE = "dashscope"
    DEEPSEEK = "deepseek"
    GCP_GEMINI = "gcp.gemini"
    OLLAMA = "ollama"
    OPENAI = "openai"


__all__ = [
    "_serialize_to_str",
    "_to_serializable",
    "SpanAttributes",
    "OperationNameValues",
    "ProviderNameValues",
]
