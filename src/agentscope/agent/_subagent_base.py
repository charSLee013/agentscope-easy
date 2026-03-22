# -*- coding: utf-8 -*-
"""Framework skeleton for SubAgent V1 delegation flows."""
from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass, field
import json
import logging
from typing import TYPE_CHECKING, Any, Callable, cast, TypedDict

from pydantic import BaseModel

from .._logging import logger
from ..message import AudioBlock, ImageBlock, Msg, TextBlock, VideoBlock
from ..types import JSONSerializableObject
from ._agent_base import AgentBase

if TYPE_CHECKING:  # pragma: no cover
    from ..formatter import FormatterBase
    from ..memory import MemoryBase
    from ..model import ChatModelBase
    from ..tool import ToolResponse, Toolkit


@dataclass(slots=True)
class PermissionBundle:
    """Shared resources copied from the host agent."""

    logger: logging.Logger
    filesystem_service: object | None = None
    safety_limits: dict[str, JSONSerializableObject] = field(
        default_factory=dict,
    )
    supervisor_name: str = "host"


@dataclass(slots=True)
class ContextBundle:
    """Snapshot of the host agent state before delegation."""

    conversation: list[Msg] = field(default_factory=list)
    recent_tool_results: list[Msg] = field(default_factory=list)
    long_term_refs: list[dict[str, JSONSerializableObject]] = field(
        default_factory=list,
    )
    workspace_handles: list[str] = field(default_factory=list)
    safety_flags: dict[str, JSONSerializableObject] = field(
        default_factory=dict,
    )


@dataclass(slots=True)
class DelegationContext:
    """Normalized payload shared with subagents."""

    input_payload: dict[str, JSONSerializableObject]
    recent_events: list[dict[str, JSONSerializableObject]]
    long_term_refs: list[dict[str, JSONSerializableObject]]
    workspace_pointers: list[str]
    safety_flags: dict[str, JSONSerializableObject]
    input_preview: str | None = None

    def to_payload(self) -> dict[str, JSONSerializableObject]:
        """Convert the context into tool metadata."""
        payload = cast_json_dict(
            {
                "input_payload": self.input_payload,
                "recent_events": self.recent_events,
                "long_term_refs": self.long_term_refs,
                "workspace_pointers": self.workspace_pointers,
                "safety_flags": self.safety_flags,
            },
        )
        if self.input_preview is not None:
            payload["input_preview"] = self.input_preview
        return payload

    @classmethod
    def from_payload(
        cls,
        payload: dict[str, JSONSerializableObject],
    ) -> "DelegationContext":
        """Hydrate a context from tool metadata."""
        preview = payload.get("input_preview")
        return cls(
            input_payload=_json_object_dict(payload.get("input_payload")),
            recent_events=_json_object_dict_list(payload.get("recent_events")),
            long_term_refs=_json_object_dict_list(
                payload.get("long_term_refs"),
            ),
            workspace_pointers=_json_string_list(
                payload.get("workspace_pointers"),
            ),
            safety_flags=_json_object_dict(payload.get("safety_flags")),
            input_preview=str(preview) if preview is not None else None,
        )


class SubAgentUnavailable(RuntimeError):
    """Raised when a subagent cannot be registered or exported."""


class ToolSpec(TypedDict, total=False):
    """Declarative tool registration entry for subagent-local toolkits."""

    func: Callable[..., Any]
    group: str
    preset_kwargs: dict[str, Any]
    func_description: str
    json_schema: dict[str, Any]


class SubAgentBase(AgentBase):
    """Skeleton agent dedicated to delegation-as-tool flows."""

    spec_name: str = "subagent"
    InputModel: type[BaseModel] | None = None

    def __init__(
        self,
        *,
        permissions: PermissionBundle,
        spec_name: str,
        toolkit: "Toolkit | None" = None,
        memory: "MemoryBase | None" = None,
        tools: list[Callable[..., Any] | ToolSpec] | None = None,
        model_override: "ChatModelBase | None" = None,
        formatter_override: "FormatterBase | None" = None,
        ephemeral_memory: bool = True,
    ) -> None:
        super().__init__()

        self.permissions = permissions
        self.spec_name = spec_name
        self.model_override = model_override
        self.formatter_override = formatter_override
        if toolkit is None:
            from ..tool import Toolkit as _Toolkit

            toolkit = _Toolkit()
            if tools:
                self._hydrate_toolkit(toolkit, tools)
        self.toolkit = toolkit

        if memory is None:
            from ..memory import InMemoryMemory

            memory = InMemoryMemory()
        self.memory = memory
        self._delegation_context: DelegationContext | None = None
        self._current_input: BaseModel | None = None
        self._ephemeral_memory = ephemeral_memory

        self.filesystem_service = permissions.filesystem_service
        if self.filesystem_service is not None and hasattr(
            self.filesystem_service,
            "tool_functions",
        ):
            for tool_func in self.filesystem_service.tool_functions():
                tool_name = getattr(tool_func, "__name__", None)
                if tool_name and tool_name in self.toolkit.tools:
                    continue
                self.toolkit.register_tool_function(
                    tool_func,
                    preset_kwargs=cast_json_dict(
                        {"service": self.filesystem_service},
                    ),
                )

        self.set_console_output_enabled(False)
        self.set_msg_queue_enabled(False)

    async def observe(self, msg: Msg | list[Msg] | None) -> None:
        """Record observed messages into the subagent-local memory."""
        if msg is not None:
            await self.memory.add(msg)

    async def reply(self, *args: Any, **kwargs: Any) -> Msg:
        """Subclasses must implement the delegated reply logic."""
        del args, kwargs
        raise NotImplementedError(
            f"{self.__class__.__name__} must implement `reply`.",
        )

    async def handle_interrupt(self, *args: Any, **kwargs: Any) -> Msg:
        """Return a stable interruption message for delegated runs."""
        del args, kwargs
        return Msg(
            name=self.spec_name,
            content="Subagent interrupted.",
            role="assistant",
            metadata={"interrupted": True},
        )

    def _hydrate_toolkit(
        self,
        toolkit: "Toolkit",
        tools: list[Callable[..., Any] | ToolSpec],
    ) -> None:
        """Batch-register provided tools into the subagent-local toolkit."""
        for entry in tools:
            if callable(entry):
                toolkit.register_tool_function(entry)
                continue

            func = entry.get("func")
            if not callable(func):
                continue
            toolkit.register_tool_function(
                func,  # type: ignore[arg-type]
                group_name=entry.get("group", "basic"),
                preset_kwargs=dict(entry.get("preset_kwargs", {})),
                func_description=entry.get("func_description"),
                json_schema=entry.get("json_schema"),
            )

    @classmethod
    def get_input_model(cls) -> type[BaseModel]:
        """Return the declared Pydantic input model."""
        if cls.InputModel is None:
            raise NotImplementedError(
                f"{cls.__name__} must set `InputModel` to a Pydantic "
                "BaseModel subclass.",
            )
        return cls.InputModel

    @classmethod
    def build_delegation_context(
        cls,
        parent_context: ContextBundle,
        input_obj: BaseModel,
    ) -> DelegationContext:
        """Build the minimal delegation payload."""
        recent_events = [
            _summarize_msg(msg) for msg in parent_context.recent_tool_results
        ][:4]

        if not recent_events and parent_context.conversation:
            recent_events = [_summarize_msg(parent_context.conversation[-1])]

        payload = cast_json_dict(input_obj.model_dump())
        try:
            preview = json.dumps(payload, ensure_ascii=False)
        except TypeError:
            preview = str(payload)

        return DelegationContext(
            input_payload=payload,
            recent_events=recent_events,
            long_term_refs=list(parent_context.long_term_refs),
            workspace_pointers=list(parent_context.workspace_handles),
            safety_flags=dict(parent_context.safety_flags),
            input_preview=preview[:200],
        )

    @classmethod
    def _pre_context_compress(
        cls,
        parent_context: ContextBundle,
        input_obj: BaseModel,
    ) -> DelegationContext:
        """Backward-compatible alias for delegation context building."""
        return cls.build_delegation_context(parent_context, input_obj)

    @classmethod
    async def export_agent(
        cls,
        *,
        permissions: PermissionBundle,
        parent_context: ContextBundle,
        spec_name: str,
        ephemeral_memory: bool = True,
        tools: list[Callable[..., Any] | ToolSpec] | None = None,
        model_override: "ChatModelBase | None" = None,
        formatter_override: "FormatterBase | None" = None,
        input_obj: BaseModel,
        delegation_context: DelegationContext | None = None,
    ) -> "SubAgentBase":
        """Construct a fresh subagent instance."""
        del parent_context, input_obj
        instance = cls(
            permissions=permissions,
            spec_name=spec_name,
            tools=tools,
            model_override=model_override,
            formatter_override=formatter_override,
            ephemeral_memory=ephemeral_memory,
        )

        if delegation_context is not None:
            instance.load_delegation_context(delegation_context)
        return instance

    def load_delegation_context(
        self,
        context: DelegationContext | dict[str, JSONSerializableObject],
    ) -> None:
        """Store the delegation context for later retrieval."""
        if isinstance(context, dict):
            context = DelegationContext.from_payload(context)
        self._delegation_context = context

    async def delegate(
        self,
        input_obj: BaseModel,
        *,
        delegation_context: DelegationContext | None = None,
        **kwargs: Any,
    ) -> "ToolResponse":
        """Uniform delegate entrypoint invoked by the host tool wrapper."""
        from ..tool import ToolResponse

        context = delegation_context or self._delegation_context
        if context is None:
            payload = cast_json_dict(input_obj.model_dump())
            context = DelegationContext(
                input_payload=payload,
                recent_events=[],
                long_term_refs=[],
                workspace_pointers=[],
                safety_flags={},
                input_preview=json.dumps(payload, ensure_ascii=False)[:200],
            )

        self.load_delegation_context(context)
        self._current_input = input_obj

        await self.memory.add(
            Msg(
                name=self.permissions.supervisor_name,
                content=json.dumps(
                    context.input_payload,
                    ensure_ascii=False,
                ),
                role="user",
                metadata={"delegation_context": context.to_payload()},
            ),
        )

        try:
            reply_msg = await self.reply(input_obj, **kwargs)
        except Exception as error:  # noqa: BLE001
            logger.warning(
                "Subagent `%s` failed: %s",
                self.spec_name,
                error,
                exc_info=True,
            )
            return ToolResponse(
                content=[
                    TextBlock(
                        type="text",
                        text=(
                            "Subagent execution unavailable. "
                            "See metadata for diagnostics."
                        ),
                    ),
                ],
                metadata={
                    "unavailable": True,
                    "error": str(error),
                    "subagent": self.spec_name,
                    "supervisor": self.permissions.supervisor_name,
                },
                is_last=True,
            )
        finally:
            if self._ephemeral_memory:
                await self.memory.clear()

        if not isinstance(reply_msg, Msg):
            return ToolResponse(
                content=[
                    TextBlock(
                        type="text",
                        text="Subagent produced invalid reply payload.",
                    ),
                ],
                metadata={
                    "unavailable": True,
                    "error": "invalid_reply",
                    "subagent": self.spec_name,
                    "supervisor": self.permissions.supervisor_name,
                },
                is_last=True,
            )

        return _msg_to_tool_response(
            reply_msg,
            subagent_name=self.spec_name,
            supervisor=self.permissions.supervisor_name,
            context=context,
        )


def cast_json_dict(
    payload: dict[str, Any],
) -> dict[str, JSONSerializableObject]:
    """Best-effort cast helper for Pydantic model dumps."""
    return payload  # type: ignore[return-value]


def _summarize_msg(msg: Msg) -> dict[str, JSONSerializableObject]:
    """Produce a compact representation of a message."""
    if isinstance(msg.content, str):
        preview = msg.content[:200]
    else:
        preview_chunks: list[str] = []
        for block in msg.get_content_blocks():
            block_type = block.get("type")
            if block_type == "text":
                preview_chunks.append(str(block.get("text", "")))
            elif block_type == "tool_result":
                preview_chunks.append(
                    f"[tool_result:{block.get('name', '')}]",
                )
        preview = " ".join(preview_chunks)[:200]

    return {
        "id": msg.id,
        "role": msg.role,
        "name": msg.name,
        "preview": preview,
        "timestamp": msg.timestamp,
    }


def _msg_to_tool_response(
    msg: Msg,
    *,
    subagent_name: str,
    supervisor: str,
    context: DelegationContext,
) -> "ToolResponse":
    """Convert a message into a ToolResponse chunk."""
    from ..tool import ToolResponse

    if isinstance(msg.content, str):
        content_blocks: list[TextBlock | ImageBlock | AudioBlock | VideoBlock]
        content_blocks = [
            TextBlock(
                type="text",
                text=msg.content,
            ),
        ]
    else:
        allowed_types = {"text", "image", "audio"}
        content_blocks = []
        for block in msg.get_content_blocks():
            if block.get("type") in allowed_types:
                content_blocks.append(
                    cast(
                        TextBlock | ImageBlock | AudioBlock | VideoBlock,
                        block,
                    ),
                )
        if not content_blocks:
            content_blocks = [TextBlock(type="text", text="")]

    metadata: dict[str, Any] = {
        "subagent": subagent_name,
        "supervisor": supervisor,
        "delegation_context": context.to_payload(),
    }
    if msg.metadata:
        metadata["response_metadata"] = deepcopy(msg.metadata)

    return ToolResponse(
        content=content_blocks,
        metadata=metadata,
        is_last=True,
    )


def _json_object_dict(
    value: JSONSerializableObject | None,
) -> dict[str, JSONSerializableObject]:
    """Cast a JSON object payload into a dictionary shape."""
    return cast(dict[str, JSONSerializableObject], value or {})


def _json_object_dict_list(
    value: JSONSerializableObject | None,
) -> list[dict[str, JSONSerializableObject]]:
    """Cast a JSON array payload into a list of JSON-object dictionaries."""
    return cast(list[dict[str, JSONSerializableObject]], value or [])


def _json_string_list(value: JSONSerializableObject | None) -> list[str]:
    """Cast a JSON array payload into a list of strings."""
    return cast(list[str], value or [])
