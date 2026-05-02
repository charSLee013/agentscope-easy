# -*- coding: utf-8 -*-
"""Set up an A2A server with a ReAct agent to handle the input query"""
import os
import tempfile
import uuid
import copy
from typing import AsyncGenerator, Any

from a2a.server.apps import A2AStarletteApplication
from a2a.server.events import Event
from a2a.types import (
    Task,
    TaskStatus,
    TaskState,
    MessageSendParams,
    TaskStatusUpdateEvent,
)
from starlette.middleware.cors import CORSMiddleware

from agent_card import agent_card
from prompt_builder import get_ui_prompt
from a2ui_utils import (
    pre_process_request_with_ui_event,
)
from runtime_helpers import build_sample_toolkit, prepare_final_a2a_message
from agentscope._logging import logger
from agentscope.agent import ReActAgent
from agentscope.formatter import DashScopeChatFormatter, A2AChatFormatter
from agentscope.model import DashScopeChatModel
from agentscope.pipeline import stream_printing_messages
from agentscope.session import JSONSession


class SimpleStreamHandler:
    """A simple request handler that handles the input query by a
    ReAct agent.

    This handler processes A2A protocol messages by using a ReAct agent
    to generate responses. It supports both streaming and non-streaming
    message handling, and manages session state for conversation continuity.
    """

    def __init__(self) -> None:
        self._session_dir = tempfile.mkdtemp(
            prefix="agentscope-a2ui-sessions-",
        )

    async def on_message_send(
        self,  # pylint: disable=unused-argument
        params: MessageSendParams,
        *args: Any,
        **kwargs: Any,
    ) -> Task:
        """Handles non-streaming message_send requests by collecting
        events from the stream and returning the final Task.

        Args:
            params (`MessageSendParams`):
                The parameters for sending the message.
            *args (`Any`):
                Additional positional arguments.
            **kwargs (`Any`):
                Additional keyword arguments.

        Returns:
            `Task`:
                The final Task object.
        """
        logger.info("--- params: %s ---", params)
        logger.info("args: %s ---", args)
        logger.info("kwargs: %s ---", kwargs)
        # Collect all events from the stream
        final_event = None
        task_id = params.message.task_id or uuid.uuid4().hex
        context_id = params.message.context_id or "default-context"

        async for event in self.on_message_send_stream(
            params,
            *args,
            task_id=task_id,
            context_id=context_id,
            **kwargs,
        ):
            if event.final:
                final_event = event
                break

        # Ensure we always return a valid Task
        if final_event is None:
            # If no final event was found, create one with completed state
            logger.warning(
                "No final event found in stream, "
                "creating default completed event",
            )
            final_event = TaskStatusUpdateEvent(
                task_id=task_id,
                context_id=context_id,
                status=TaskStatus(state=TaskState.failed),
                final=True,
            )

        # Convert TaskStatusUpdateEvent to Task
        # A2A protocol expects on_message_send to return a Task,
        # not TaskStatusUpdateEvent
        return Task(
            id=final_event.task_id,
            context_id=final_event.context_id,
            status=final_event.status,
            artifacts=[],
        )

    async def on_message_send_stream(
        self,  # pylint: disable=unused-argument
        params: MessageSendParams,
        *args: Any,
        task_id: str | None = None,
        context_id: str | None = None,
        **kwargs: Any,
    ) -> AsyncGenerator[Event, None]:
        """Handles the message_send method by the agent.

        Args:
            params (`MessageSendParams`):
                The parameters for sending the message.
            *args (`Any`):
                Additional positional arguments.
            **kwargs (`Any`):
                Additional keyword arguments.

        Returns:
            `AsyncGenerator[Event, None]`:
                An asynchronous generator that yields task status update
                events.
        """

        task_id = task_id or params.message.task_id or uuid.uuid4().hex
        context_id = context_id or params.message.context_id or "default-context"
        # ============ Agent Logic ============
        toolkit = build_sample_toolkit()

        # Create the agent instance
        agent = ReActAgent(
            name="Friday",
            sys_prompt=get_ui_prompt(),
            model=DashScopeChatModel(
                model_name="qwen3-max",
                api_key=os.getenv("DASHSCOPE_API_KEY"),
            ),
            formatter=DashScopeChatFormatter(),
            toolkit=toolkit,
            max_iters=10,
        )
        logger.info("Agent system prompt: %s", agent.sys_prompt)

        session = JSONSession(save_dir=self._session_dir)
        session_id = task_id
        await session.load_session_state(
            session_id=session_id,
            agent=agent,
        )

        # pre-process the A2A message with UI event,
        # and then convert to AgentScope Msg objects
        formatter = A2AChatFormatter()
        as_msg = await formatter.format_a2a_message(
            name="Friday",
            message=pre_process_request_with_ui_event(
                params.message,
            ),
        )

        yield TaskStatusUpdateEvent(
            task_id=task_id,
            context_id=context_id,
            status=TaskStatus(state=TaskState.working),
            final=False,
        )

        # Collect all messages from the stream
        # The 'last' flag indicates the last chunk of a streaming message,
        # not the last message from the agent
        message_count = 0
        final_msg = None
        try:
            async for msg, last in stream_printing_messages(
                agents=[agent],
                coroutine_task=agent(as_msg),
            ):
                message_count += 1
                if last:
                    final_msg = copy.deepcopy(msg)
        except Exception as e:
            logger.error(
                "--- Error in message stream: %s ---",
                e,
                exc_info=True,
            )
            raise
        finally:
            logger.info(
                "--- Message stream collection completed. "
                "Total messages: %s, "
                "Last message: %s ---",
                message_count,
                final_msg,
            )

        # Save session state (move before final message processing
        # to avoid blocking yield)
        await session.save_session_state(
            session_id=session_id,
            agent=agent,
        )

        final_a2a_message = await prepare_final_a2a_message(
            formatter,
            final_msg,
        )

        logger.info("--- Yielding final TaskStatusUpdateEvent ---")
        yield TaskStatusUpdateEvent(
            task_id=task_id,
            context_id=context_id,
            status=TaskStatus(
                state=TaskState.input_required,
                message=final_a2a_message,
            ),
            final=True,
        )


handler = SimpleStreamHandler()
app_instance = A2AStarletteApplication(
    agent_card,
    handler,
)
app = app_instance.build()

# Add CORS middleware to handle OPTIONS requests
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins for development
    allow_credentials=False,  # Cannot use "*" with credentials=True
    allow_methods=["*"],  # Allow all HTTP methods including OPTIONS
    allow_headers=["*"],  # Allow all headers
)
