# -*- coding: utf-8 -*-
"""The ReAct agent unittests."""
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Any, AsyncGenerator
from unittest import IsolatedAsyncioTestCase
from unittest.mock import AsyncMock

from pydantic import BaseModel, Field

from agentscope.agent import ReActAgent
from agentscope.formatter import DashScopeChatFormatter
from agentscope.memory import InMemoryMemory, LongTermMemoryBase
from agentscope.message import (
    AudioBlock,
    Base64Source,
    Msg,
    TextBlock,
    ToolUseBlock,
)
from agentscope.model import ChatModelBase, ChatResponse
from agentscope.tool import Toolkit
from agentscope.tts import TTSModelBase, TTSResponse


class MyModel(ChatModelBase):
    """Test model class."""

    def __init__(self) -> None:
        """Initialize the test model."""
        super().__init__("test_model", stream=False)
        self.fake_content = [TextBlock(type="text", text="123")]

    async def __call__(
        self,
        _messages: list[dict],
        **kwargs: Any,
    ) -> ChatResponse:
        """Mock model call."""
        return ChatResponse(
            content=self.fake_content,
        )


class SequenceModel(ChatModelBase):
    """Deterministic model that returns a queued sequence of outputs."""

    def __init__(self, responses: list[list[dict]]) -> None:
        super().__init__("sequence_model", stream=False)
        self._responses = list(responses)

    async def __call__(
        self,
        _messages: list[dict],
        **kwargs: Any,
    ) -> ChatResponse:
        return ChatResponse(content=self._responses.pop(0))


class StreamingSequenceModel(ChatModelBase):
    """Streaming model that yields queued chunks."""

    def __init__(self, responses: list[list[dict]]) -> None:
        super().__init__("streaming_sequence_model", stream=True)
        self._responses = list(responses)

    async def __call__(
        self,
        _messages: list[dict],
        **kwargs: Any,
    ) -> AsyncGenerator[ChatResponse, None]:
        del kwargs

        async def _stream() -> AsyncGenerator[ChatResponse, None]:
            for response in self._responses:
                yield ChatResponse(content=response)

        return _stream()


class FakeTTSModel(TTSModelBase):
    """Simple fake TTS model used to verify agent integration."""

    supports_streaming_input: bool = False

    def __init__(
        self,
        *,
        stream: bool = False,
        supports_streaming_input: bool = False,
    ) -> None:
        super().__init__("fake_tts", stream)
        self.supports_streaming_input = supports_streaming_input
        self.pushed_texts: list[str | None] = []
        self.synthesized_texts: list[str | None] = []

    @staticmethod
    def _audio(label: str) -> AudioBlock:
        return AudioBlock(
            type="audio",
            source=Base64Source(
                type="base64",
                data=label,
                media_type="audio/pcm",
            ),
        )

    async def connect(self) -> None:
        return None

    async def close(self) -> None:
        return None

    async def push(
        self,
        msg: Msg,
        **kwargs: Any,
    ) -> TTSResponse:
        del kwargs
        self.pushed_texts.append(msg.get_text_content())
        return TTSResponse(
            content=self._audio(f"push-{len(self.pushed_texts)}"),
        )

    async def synthesize(
        self,
        msg: Msg | None = None,
        **kwargs: Any,
    ) -> TTSResponse | AsyncGenerator[TTSResponse, None]:
        del kwargs
        self.synthesized_texts.append(
            None if msg is None else msg.get_text_content(),
        )
        if not self.stream:
            return TTSResponse(content=self._audio("final"))

        async def _stream() -> AsyncGenerator[TTSResponse, None]:
            yield TTSResponse(
                content=self._audio("stream-1"),
                is_last=False,
            )
            yield TTSResponse(
                content=self._audio("stream-2"),
                is_last=True,
            )

        return _stream()


class StructuredReplyModel(BaseModel):
    """Structured payload returned through the finish tool."""

    result: str = Field(description="Structured result.")


class RecordingLongTermMemory(LongTermMemoryBase):
    """Spy object capturing static long-term memory writes."""

    def __init__(self) -> None:
        super().__init__()
        self.record_calls: list[list[Msg | None]] = []

    async def record(
        self,
        msgs: list[Msg | None],
        **kwargs: Any,
    ) -> None:
        self.record_calls.append(list(msgs))

    async def retrieve(
        self,
        msg: Msg | list[Msg] | None,
        **kwargs: Any,
    ) -> str:
        return ""


async def pre_reasoning_hook(self: ReActAgent, _kwargs: Any) -> None:
    """Mock pre-reasoning hook."""
    if hasattr(self, "cnt_pre_reasoning"):
        self.cnt_pre_reasoning += 1
    else:
        self.cnt_pre_reasoning = 1


async def post_reasoning_hook(
    self: ReActAgent,
    _kwargs: Any,
    _output: Msg | None,
) -> None:
    """Mock post-reasoning hook."""
    if hasattr(self, "cnt_post_reasoning"):
        self.cnt_post_reasoning += 1
    else:
        self.cnt_post_reasoning = 1


async def pre_acting_hook(self: ReActAgent, _kwargs: Any) -> None:
    """Mock pre-acting hook."""
    if hasattr(self, "cnt_pre_acting"):
        self.cnt_pre_acting += 1
    else:
        self.cnt_pre_acting = 1


async def post_acting_hook(
    self: ReActAgent,
    _kwargs: Any,
    _output: Msg | None,
) -> None:
    """Mock post-acting hook."""
    if hasattr(self, "cnt_post_acting"):
        self.cnt_post_acting += 1
    else:
        self.cnt_post_acting = 1


class ReActAgentTest(IsolatedAsyncioTestCase):
    """Test class for ReActAgent."""

    async def test_react_agent(self) -> None:
        """Test the ReActAgent class"""
        model = MyModel()
        agent = ReActAgent(
            name="Friday",
            sys_prompt="You are a helpful assistant named Friday.",
            model=model,
            formatter=DashScopeChatFormatter(),
            memory=InMemoryMemory(),
            toolkit=Toolkit(),
        )

        agent.register_instance_hook(
            "pre_reasoning",
            "test_hook",
            pre_reasoning_hook,
        )

        agent.register_instance_hook(
            "post_reasoning",
            "test_hook",
            post_reasoning_hook,
        )

        agent.register_instance_hook(
            "pre_acting",
            "test_hook",
            pre_acting_hook,
        )

        agent.register_instance_hook(
            "post_acting",
            "test_hook",
            post_acting_hook,
        )

        await agent()
        self.assertEqual(
            getattr(agent, "cnt_pre_reasoning"),
            1,
        )
        self.assertEqual(
            getattr(agent, "cnt_post_reasoning"),
            1,
        )
        self.assertEqual(
            getattr(agent, "cnt_pre_acting"),
            1,
        )
        self.assertEqual(
            getattr(agent, "cnt_post_acting"),
            1,
        )

        model.fake_content = [
            ToolUseBlock(
                type="tool_use",
                name=agent.finish_function_name,
                id="xx",
                input={"response": "123"},
            ),
        ]

        await agent()
        self.assertEqual(
            getattr(agent, "cnt_pre_reasoning"),
            2,
        )
        self.assertEqual(
            getattr(agent, "cnt_post_reasoning"),
            2,
        )
        self.assertEqual(
            getattr(agent, "cnt_pre_acting"),
            2,
        )
        self.assertEqual(
            getattr(agent, "cnt_post_acting"),
            2,
        )

    async def test_sys_prompt_includes_agent_skill_prompt(self) -> None:
        """Registered agent skills should extend the system prompt."""
        model = MyModel()
        agent = ReActAgent(
            name="Friday",
            sys_prompt="You are a helpful assistant named Friday.",
            model=model,
            formatter=DashScopeChatFormatter(),
            memory=InMemoryMemory(),
            toolkit=Toolkit(),
        )

        self.assertEqual(
            agent.sys_prompt,
            "You are a helpful assistant named Friday.",
        )

        with TemporaryDirectory() as tmpdir:
            skill_dir = Path(tmpdir) / "code-reader"
            skill_dir.mkdir()
            (skill_dir / "SKILL.md").write_text(
                "---\n"
                "name: Code Reader\n"
                "description: Read code safely.\n"
                "---\n",
                encoding="utf-8",
            )
            agent.toolkit.register_agent_skill(str(skill_dir))

            self.assertIn(
                "You are a helpful assistant named Friday.",
                agent.sys_prompt,
            )
            self.assertIn("Code Reader", agent.sys_prompt)
            self.assertIn("Read code safely.", agent.sys_prompt)
            self.assertIn(f"{skill_dir}/SKILL.md", agent.sys_prompt)

    async def test_structured_output_returns_metadata(self) -> None:
        """Structured output should survive the finish-tool reply path."""
        model = MyModel()
        agent = ReActAgent(
            name="Friday",
            sys_prompt="You are a helpful assistant named Friday.",
            model=model,
            formatter=DashScopeChatFormatter(),
            memory=InMemoryMemory(),
            toolkit=Toolkit(),
        )

        model.fake_content = [
            ToolUseBlock(
                type="tool_use",
                name=agent.finish_function_name,
                id="structured-1",
                input={
                    "response": "Structured reply",
                    "result": "ok",
                },
            ),
        ]

        reply_msg = await agent.reply(structured_model=StructuredReplyModel)

        self.assertEqual(reply_msg.get_text_content(), "Structured reply")
        self.assertEqual(reply_msg.metadata, {"result": "ok"})
        memory_msgs = await agent.memory.get_memory()
        self.assertEqual(memory_msgs[-1].metadata, {"result": "ok"})

    async def test_static_long_term_memory_records_final_reply(self) -> None:
        """Static long-term memory should see the final reply before record."""
        model = MyModel()
        long_term_memory = RecordingLongTermMemory()
        agent = ReActAgent(
            name="Friday",
            sys_prompt="You are a helpful assistant named Friday.",
            model=model,
            formatter=DashScopeChatFormatter(),
            memory=InMemoryMemory(),
            toolkit=Toolkit(),
            long_term_memory=long_term_memory,
            long_term_memory_mode="static_control",
        )

        model.fake_content = [
            ToolUseBlock(
                type="tool_use",
                name=agent.finish_function_name,
                id="structured-2",
                input={
                    "response": "Persist me",
                    "result": "saved",
                },
            ),
        ]

        reply_msg = await agent.reply(structured_model=StructuredReplyModel)

        self.assertEqual(reply_msg.metadata, {"result": "saved"})
        self.assertEqual(len(long_term_memory.record_calls), 1)
        recorded_reply = long_term_memory.record_calls[0][-1]
        assert recorded_reply is not None
        self.assertEqual(recorded_reply.get_text_content(), "Persist me")
        self.assertEqual(recorded_reply.metadata, {"result": "saved"})

    async def test_structured_output_then_text_reply(self) -> None:
        """Structured output can be captured before the final text reply."""
        model = SequenceModel(
            [
                [
                    ToolUseBlock(
                        type="tool_use",
                        name="generate_response",
                        id="structured-3",
                        input={"result": "queued"},
                    ),
                ],
                [
                    TextBlock(
                        type="text",
                        text="Final response after structured output.",
                    ),
                ],
            ],
        )
        agent = ReActAgent(
            name="Friday",
            sys_prompt="You are a helpful assistant named Friday.",
            model=model,
            formatter=DashScopeChatFormatter(),
            memory=InMemoryMemory(),
            toolkit=Toolkit(),
        )

        reply_msg = await agent.reply(structured_model=StructuredReplyModel)

        self.assertEqual(
            reply_msg.get_text_content(),
            "Final response after structured output.",
        )
        self.assertEqual(reply_msg.metadata, {"result": "queued"})

    async def test_structured_schema_does_not_leak_to_next_reply(
        self,
    ) -> None:
        """Finish-tool schema should reset after a structured reply."""
        model = MyModel()
        agent = ReActAgent(
            name="Friday",
            sys_prompt="You are a helpful assistant named Friday.",
            model=model,
            formatter=DashScopeChatFormatter(),
            memory=InMemoryMemory(),
            toolkit=Toolkit(),
        )

        model.fake_content = [
            ToolUseBlock(
                type="tool_use",
                name=agent.finish_function_name,
                id="structured-4",
                input={
                    "response": "Structured once",
                    "result": "ok",
                },
            ),
        ]
        await agent.reply(structured_model=StructuredReplyModel)

        model.fake_content = [
            ToolUseBlock(
                type="tool_use",
                name=agent.finish_function_name,
                id="plain-1",
                input={"response": "Plain follow-up"},
            ),
        ]
        reply_msg = await agent.reply()

        self.assertEqual(reply_msg.get_text_content(), "Plain follow-up")
        self.assertIsNone(reply_msg.metadata)

        finish_schema = next(
            schema
            for schema in agent.toolkit.get_json_schemas()
            if schema["function"]["name"] == agent.finish_function_name
        )
        self.assertNotIn(
            "result",
            finish_schema["function"]["parameters"]["properties"],
        )

    async def test_tts_model_adds_speech_to_text_reply(self) -> None:
        """A configured TTS model should synthesize speech for text replies."""
        model = MyModel()
        tts_model = FakeTTSModel()
        agent = ReActAgent(
            name="Friday",
            sys_prompt="You are a helpful assistant named Friday.",
            model=model,
            formatter=DashScopeChatFormatter(),
            memory=InMemoryMemory(),
            toolkit=Toolkit(),
            tts_model=tts_model,
        )
        agent.print = AsyncMock()

        await agent.reply()

        self.assertEqual(tts_model.synthesized_texts, ["123"])
        self.assertEqual(
            agent.print.await_args_list[-1].kwargs["speech"],
            FakeTTSModel._audio("final"),
        )

    async def test_streaming_tts_model_pushes_and_synthesizes(self) -> None:
        """Realtime TTS should use push during stream and synthesize at end."""
        model = StreamingSequenceModel(
            [
                [TextBlock(type="text", text="Hello")],
                [TextBlock(type="text", text="Hello world")],
            ],
        )
        tts_model = FakeTTSModel(
            stream=False,
            supports_streaming_input=True,
        )
        agent = ReActAgent(
            name="Friday",
            sys_prompt="You are a helpful assistant named Friday.",
            model=model,
            formatter=DashScopeChatFormatter(),
            memory=InMemoryMemory(),
            toolkit=Toolkit(),
            tts_model=tts_model,
        )
        agent.print = AsyncMock()

        await agent.reply()

        self.assertEqual(tts_model.pushed_texts, ["Hello", "Hello world"])
        self.assertEqual(tts_model.synthesized_texts, ["Hello world"])

    async def test_model_audio_skips_tts_synthesis(self) -> None:
        """Model-provided audio should win over external TTS synthesis."""
        model = MyModel()
        audio_block = AudioBlock(
            type="audio",
            source=Base64Source(
                type="base64",
                data="model-audio",
                media_type="audio/pcm",
            ),
        )
        model.fake_content = [
            TextBlock(type="text", text="123"),
            audio_block,
        ]
        tts_model = FakeTTSModel()
        agent = ReActAgent(
            name="Friday",
            sys_prompt="You are a helpful assistant named Friday.",
            model=model,
            formatter=DashScopeChatFormatter(),
            memory=InMemoryMemory(),
            toolkit=Toolkit(),
            tts_model=tts_model,
        )
        agent.print = AsyncMock()

        await agent.reply()

        self.assertEqual(tts_model.synthesized_texts, [])
        self.assertEqual(
            agent.print.await_args_list[-1].kwargs["speech"],
            [audio_block],
        )

    async def test_streaming_tts_output_prints_intermediate_chunks(
        self,
    ) -> None:
        """Streaming TTS output should be forwarded chunk by chunk."""
        model = MyModel()
        tts_model = FakeTTSModel(stream=True)
        agent = ReActAgent(
            name="Friday",
            sys_prompt="You are a helpful assistant named Friday.",
            model=model,
            formatter=DashScopeChatFormatter(),
            memory=InMemoryMemory(),
            toolkit=Toolkit(),
            tts_model=tts_model,
        )
        agent.print = AsyncMock()

        await agent.reply()

        speeches = [
            call.kwargs["speech"]
            for call in agent.print.await_args_list
            if "speech" in call.kwargs
        ]
        self.assertIn(FakeTTSModel._audio("stream-1"), speeches)
        self.assertIn(FakeTTSModel._audio("stream-2"), speeches)

    async def test_summarizing_path_uses_tts_model(self) -> None:
        """The summary fallback should also synthesize speech."""
        model = MyModel()
        tts_model = FakeTTSModel()
        agent = ReActAgent(
            name="Friday",
            sys_prompt="You are a helpful assistant named Friday.",
            model=model,
            formatter=DashScopeChatFormatter(),
            memory=InMemoryMemory(),
            toolkit=Toolkit(),
            tts_model=tts_model,
            max_iters=0,
        )
        agent.print = AsyncMock()

        reply_msg = await agent.reply()

        self.assertEqual(reply_msg.get_text_content(), "123")
        self.assertEqual(tts_model.synthesized_texts, ["123"])
