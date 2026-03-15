# -*- coding: utf-8 -*-
"""Task-memory implementation backed by ReMe."""
from typing import Any
import warnings

from ._reme_long_term_memory_base import ReMeLongTermMemoryBase
from ._reme_personal_long_term_memory import _msg_to_text
from ..._logging import logger
from ...message import Msg, TextBlock
from ...tool import ToolResponse


class ReMeTaskLongTermMemory(ReMeLongTermMemoryBase):
    """Task memory implementation using ReMe."""

    async def record_to_memory(
        self,
        thinking: str,
        content: list[str],
        **kwargs: Any,
    ) -> ToolResponse:
        """Record task execution experience."""
        if not self._app_started:
            raise RuntimeError(
                "ReMeApp context not started. Please use 'async with' "
                "to initialize the app.",
            )

        try:
            messages = []
            if thinking:
                messages.append({"role": "user", "content": thinking})
            for item in content:
                messages.append({"role": "user", "content": item})
                messages.append(
                    {
                        "role": "assistant",
                        "content": "Task information recorded.",
                    },
                )

            result = await self.app.async_execute(
                name="summary_task_memory",
                workspace_id=self.workspace_id,
                trajectories=[
                    {
                        "messages": messages,
                        "score": kwargs.pop("score", 1.0),
                    },
                ],
                **kwargs,
            )
            return ToolResponse(
                content=[
                    TextBlock(
                        type="text",
                        text=(
                            "Successfully recorded "
                            f"{len(content)} task memory/memories."
                        ),
                    ),
                ],
                metadata={"result": result},
            )
        except Exception as exc:  # pragma: no cover - exercised in tests
            logger.exception("Error recording task memory: %s", str(exc))
            return ToolResponse(
                content=[
                    TextBlock(
                        type="text",
                        text=f"Error recording task memory: {str(exc)}",
                    ),
                ],
            )

    async def retrieve_from_memory(
        self,
        keywords: list[str],
        limit: int = 5,
        **kwargs: Any,
    ) -> ToolResponse:
        """Retrieve task experiences by keyword."""
        if not self._app_started:
            raise RuntimeError(
                "ReMeApp context not started. Please use 'async with' "
                "to initialize the app.",
            )

        try:
            results = []
            for keyword in keywords:
                result = await self.app.async_execute(
                    name="retrieve_task_memory",
                    workspace_id=self.workspace_id,
                    query=keyword,
                    top_k=limit,
                    **kwargs,
                )
                answer = result.get("answer", "")
                if answer:
                    results.append(f"Keyword '{keyword}':\n{answer}")

            text = (
                "\n\n".join(results)
                if results
                else "No task experiences found for the given keywords."
            )
            return ToolResponse(content=[TextBlock(type="text", text=text)])
        except Exception as exc:  # pragma: no cover - exercised in tests
            logger.exception("Error retrieving task memory: %s", str(exc))
            return ToolResponse(
                content=[
                    TextBlock(
                        type="text",
                        text=f"Error retrieving task memory: {str(exc)}",
                    ),
                ],
            )

    async def record(
        self,
        msgs: list[Msg | None],
        **kwargs: Any,
    ) -> None:
        """Record AgentScope messages as a task trajectory."""
        if isinstance(msgs, Msg):
            msgs = [msgs]
        msg_list = [_ for _ in msgs if _]
        if not msg_list:
            return
        if not all(isinstance(_, Msg) for _ in msg_list):
            raise TypeError(
                "The input messages must be a list of Msg objects.",
            )
        if not self._app_started:
            raise RuntimeError(
                "ReMeApp context not started. Please use 'async with' "
                "to initialize the app.",
            )

        try:
            messages = [
                {"role": msg.role, "content": _msg_to_text(msg)}
                for msg in msg_list
            ]
            await self.app.async_execute(
                name="summary_task_memory",
                workspace_id=self.workspace_id,
                trajectories=[
                    {
                        "messages": messages,
                        "score": kwargs.pop("score", 1.0),
                    },
                ],
                **kwargs,
            )
        except Exception as exc:  # pragma: no cover - exercised in tests
            logger.exception(
                "Error recording messages to task memory: %s",
                str(exc),
            )
            warnings.warn(
                f"Error recording messages to task memory: {str(exc)}",
                stacklevel=2,
            )

    async def retrieve(
        self,
        msg: Msg | list[Msg] | None,
        limit: int = 5,
        **kwargs: Any,
    ) -> str:
        """Retrieve relevant task experience text for a message."""
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
            query = _msg_to_text(msg[-1])
            if not query:
                return ""
            result = await self.app.async_execute(
                name="retrieve_task_memory",
                workspace_id=self.workspace_id,
                query=query,
                top_k=limit,
                **kwargs,
            )
            return result.get("answer", "")
        except Exception as exc:  # pragma: no cover - exercised in tests
            logger.exception("Error retrieving task memory: %s", str(exc))
            warnings.warn(
                f"Error retrieving task memory: {str(exc)}",
                stacklevel=2,
            )
            return ""
