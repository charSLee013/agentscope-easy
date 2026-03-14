# -*- coding: utf-8 -*-
"""Tool-memory implementation backed by ReMe."""
from typing import Any
import json
import warnings

from ._reme_long_term_memory_base import ReMeLongTermMemoryBase
from ._reme_personal_long_term_memory import _msg_to_text
from ..._logging import logger
from ...message import Msg, TextBlock
from ...tool import ToolResponse


class ReMeToolLongTermMemory(ReMeLongTermMemoryBase):
    """Tool memory implementation using ReMe."""

    async def record_to_memory(
        self,
        thinking: str,
        content: list[str],
        **kwargs: Any,
    ) -> ToolResponse:
        """Record tool execution results and summarize guidelines."""
        if not self._app_started:
            raise RuntimeError(
                "ReMeApp context not started. Please use 'async with' "
                "to initialize the app.",
            )

        try:
            tool_call_results, tool_names_set = self._parse_tool_call_results(
                content,
            )
            if not tool_call_results:
                return ToolResponse(
                    content=[
                        TextBlock(
                            type="text",
                            text="No valid tool call results to record.",
                        ),
                    ],
                )

            await self.app.async_execute(
                name="add_tool_call_result",
                workspace_id=self.workspace_id,
                tool_call_results=tool_call_results,
                **kwargs,
            )

            if tool_names_set:
                await self.app.async_execute(
                    name="summary_tool_memory",
                    workspace_id=self.workspace_id,
                    tool_names=list(tool_names_set),
                    **kwargs,
                )

            num_results = len(tool_call_results)
            return ToolResponse(
                content=[
                    TextBlock(
                        type="text",
                        text=(
                            f"Successfully recorded {num_results} tool "
                            "execution result"
                            f"{'s' if num_results > 1 else ''} and "
                            "generated usage guidelines."
                        ),
                    ),
                ],
            )
        except Exception as exc:  # pragma: no cover - exercised in tests
            logger.exception("Error recording tool memory: %s", str(exc))
            return ToolResponse(
                content=[
                    TextBlock(
                        type="text",
                        text=f"Error recording tool memory: {str(exc)}",
                    ),
                ],
            )

    async def retrieve_from_memory(
        self,
        keywords: list[str],
        limit: int = 5,
        **kwargs: Any,
    ) -> ToolResponse:
        """Retrieve tool usage guidelines."""
        if not self._app_started:
            raise RuntimeError(
                "ReMeApp context not started. Please use 'async with' "
                "to initialize the app.",
            )

        try:
            tool_names = ",".join(keywords)
            result = await self.app.async_execute(
                name="retrieve_tool_memory",
                workspace_id=self.workspace_id,
                tool_names=tool_names,
                top_k=limit,
                **kwargs,
            )
            answer = result.get("answer", "")
            text = answer or f"No tool guidelines found for: {tool_names}"
            return ToolResponse(content=[TextBlock(type="text", text=text)])
        except Exception as exc:  # pragma: no cover - exercised in tests
            logger.exception("Error retrieving tool memory: %s", str(exc))
            return ToolResponse(
                content=[
                    TextBlock(
                        type="text",
                        text=f"Error retrieving tool memory: {str(exc)}",
                    ),
                ],
            )

    def _parse_tool_call_results(
        self,
        content_list: list[str],
    ) -> tuple[list[dict[str, Any]], set[str]]:
        """Parse JSON content strings into tool call results."""
        tool_call_results = []
        tool_names_set = set()
        for item in content_list:
            try:
                tool_call_result = json.loads(item)
                tool_call_results.append(tool_call_result)
                if "tool_name" in tool_call_result:
                    tool_names_set.add(tool_call_result["tool_name"])
            except json.JSONDecodeError as exc:
                warnings.warn(
                    f"Failed to parse tool call result JSON: {item}. "
                    f"Error: {str(exc)}",
                    stacklevel=2,
                )
        return tool_call_results, tool_names_set

    async def record(
        self,
        msgs: list[Msg | None],
        **kwargs: Any,
    ) -> None:
        """Record AgentScope messages as tool call results."""
        if isinstance(msgs, Msg):
            msgs = [msgs]
        msg_list = [_ for _ in msgs if _]
        if not msg_list:
            return
        if not all(isinstance(_, Msg) for _ in msg_list):
            raise TypeError("The input messages must be a list of Msg objects.")
        if not self._app_started:
            raise RuntimeError(
                "ReMeApp context not started. Please use 'async with' "
                "to initialize the app.",
            )

        try:
            content_list = [_msg_to_text(msg) for msg in msg_list if _msg_to_text(msg)]
            if not content_list:
                return

            tool_call_results, tool_names_set = self._parse_tool_call_results(
                content_list,
            )
            if not tool_call_results:
                return

            await self.app.async_execute(
                name="add_tool_call_result",
                workspace_id=self.workspace_id,
                tool_call_results=tool_call_results,
                **kwargs,
            )
            if tool_names_set:
                await self.app.async_execute(
                    name="summary_tool_memory",
                    workspace_id=self.workspace_id,
                    tool_names=list(tool_names_set),
                    **kwargs,
                )
        except Exception as exc:  # pragma: no cover - exercised in tests
            logger.exception(
                "Error recording tool messages to memory: %s",
                str(exc),
            )
            warnings.warn(
                f"Error recording tool messages to memory: {str(exc)}",
                stacklevel=2,
            )

    async def retrieve(
        self,
        msg: Msg | list[Msg] | None,
        limit: int = 5,
        **kwargs: Any,
    ) -> str:
        """Retrieve tool guidance for a message query."""
        if msg is None:
            return ""
        if isinstance(msg, Msg):
            msg = [msg]
        if not isinstance(msg, list) or not all(
            isinstance(_, Msg) for _ in msg
        ):
            raise TypeError(
                "The input message must be a Msg or a list of Msg objects.",
            )
        if not self._app_started:
            raise RuntimeError(
                "ReMeApp context not started. Please use 'async with' "
                "to initialize the app.",
            )

        try:
            tool_names = _msg_to_text(msg[-1])
            if not tool_names:
                return ""
            result = await self.app.async_execute(
                name="retrieve_tool_memory",
                workspace_id=self.workspace_id,
                tool_names=tool_names,
                top_k=limit,
                **kwargs,
            )
            if isinstance(result, dict) and "answer" in result:
                return result["answer"]
            if isinstance(result, str):
                return result
            return str(result)
        except Exception as exc:  # pragma: no cover - exercised in tests
            logger.exception("Error retrieving tool guidelines: %s", str(exc))
            warnings.warn(
                f"Error retrieving tool guidelines: {str(exc)}",
                stacklevel=2,
            )
            return ""
