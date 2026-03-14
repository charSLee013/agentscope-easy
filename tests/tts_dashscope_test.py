# -*- coding: utf-8 -*-
# pylint: disable=protected-access
"""The unittests for DashScope TTS models."""
import base64
from typing import AsyncGenerator
from unittest import IsolatedAsyncioTestCase
from unittest.mock import AsyncMock, MagicMock, Mock, patch

from agentscope.message import AudioBlock, Base64Source, Msg
from agentscope.tts import (
    DashScopeRealtimeTTSModel,
    DashScopeTTSModel,
    TTSResponse,
)
from agentscope.tts._dashscope_realtime_tts_model import (
    _get_qwen_tts_realtime_callback_class,
)


class DashScopeRealtimeTTSModelTest(IsolatedAsyncioTestCase):
    """The unittests for DashScope realtime TTS model."""

    def setUp(self) -> None:
        self.api_key = "test_api_key"
        self.mock_audio_data = base64.b64encode(b"fake_audio_data").decode(
            "utf-8",
        )

    def _create_mock_tts_client(self) -> Mock:
        mock_client = Mock()
        mock_client.connect = Mock()
        mock_client.close = Mock()
        mock_client.finish = Mock()
        mock_client.commit = Mock()
        mock_client.update_session = Mock()
        mock_client.append_text = Mock()
        return mock_client

    def _create_mock_dashscope_modules(self) -> dict:
        mock_qwen_tts_realtime = MagicMock()
        mock_qwen_tts_realtime.QwenTtsRealtime = Mock
        mock_qwen_tts_realtime.QwenTtsRealtimeCallback = Mock

        mock_audio = MagicMock()
        mock_audio.qwen_tts_realtime = mock_qwen_tts_realtime

        mock_dashscope = MagicMock()
        mock_dashscope.api_key = None
        mock_dashscope.audio = mock_audio

        return {
            "dashscope": mock_dashscope,
            "dashscope.audio": mock_audio,
            "dashscope.audio.qwen_tts_realtime": mock_qwen_tts_realtime,
        }

    def test_init(self) -> None:
        """Test initialization of DashScopeRealtimeTTSModel."""
        mock_modules = self._create_mock_dashscope_modules()
        mock_tts_client = self._create_mock_tts_client()
        mock_tts_class = Mock(return_value=mock_tts_client)
        mock_modules[
            "dashscope.audio.qwen_tts_realtime"
        ].QwenTtsRealtime = mock_tts_class

        with patch.dict("sys.modules", mock_modules):
            model = DashScopeRealtimeTTSModel(
                api_key=self.api_key,
                stream=False,
            )
            self.assertEqual(model.model_name, "qwen3-tts-flash-realtime")
            self.assertFalse(model.stream)
            self.assertFalse(model._connected)

    async def test_push_incremental_text(self) -> None:
        """Test push method with incremental text chunks."""
        mock_modules = self._create_mock_dashscope_modules()
        mock_client = self._create_mock_tts_client()
        mock_tts_class = Mock(return_value=mock_client)
        mock_modules[
            "dashscope.audio.qwen_tts_realtime"
        ].QwenTtsRealtime = mock_tts_class

        with patch.dict("sys.modules", mock_modules):
            async with DashScopeRealtimeTTSModel(
                api_key=self.api_key,
                stream=False,
            ) as model:
                model._dashscope_callback.get_audio_data = AsyncMock(
                    return_value=TTSResponse(
                        content=AudioBlock(
                            type="audio",
                            source=Base64Source(
                                type="base64",
                                data=self.mock_audio_data,
                                media_type="audio/pcm;rate=24000",
                            ),
                        ),
                    ),
                )

                msg_id = "test_msg_001"
                text_chunks = ["Hello there!\n\n", "This is a test message."]
                accumulated_text = ""
                for chunk in text_chunks:
                    accumulated_text += chunk
                    msg = Msg(
                        name="user",
                        content=accumulated_text,
                        role="user",
                    )
                    msg.id = msg_id
                    response = await model.push(msg)
                    self.assertIsInstance(response, TTSResponse)

                self.assertGreater(mock_client.append_text.call_count, 0)

    async def test_synthesize_non_streaming(self) -> None:
        """Test synthesize method in non-streaming mode."""
        mock_modules = self._create_mock_dashscope_modules()
        mock_client = self._create_mock_tts_client()
        mock_tts_class = Mock(return_value=mock_client)
        mock_modules[
            "dashscope.audio.qwen_tts_realtime"
        ].QwenTtsRealtime = mock_tts_class

        with patch.dict("sys.modules", mock_modules):
            async with DashScopeRealtimeTTSModel(
                api_key=self.api_key,
                stream=False,
            ) as model:
                model._dashscope_callback.get_audio_data = AsyncMock(
                    return_value=TTSResponse(
                        content=AudioBlock(
                            type="audio",
                            source=Base64Source(
                                type="base64",
                                data=self.mock_audio_data,
                                media_type="audio/pcm;rate=24000",
                            ),
                        ),
                    ),
                )

                msg = Msg(
                    name="user",
                    content="Hello! Test message.",
                    role="user",
                )
                response = await model.synthesize(msg)
                self.assertIsInstance(response, TTSResponse)
                self.assertEqual(response.content["type"], "audio")
                mock_client.commit.assert_called_once()

    async def test_synthesize_streaming(self) -> None:
        """Test synthesize method in streaming mode."""
        mock_modules = self._create_mock_dashscope_modules()
        mock_client = self._create_mock_tts_client()
        mock_tts_class = Mock(return_value=mock_client)
        mock_modules[
            "dashscope.audio.qwen_tts_realtime"
        ].QwenTtsRealtime = mock_tts_class

        with patch.dict("sys.modules", mock_modules):
            async with DashScopeRealtimeTTSModel(
                api_key=self.api_key,
                stream=True,
            ) as model:

                async def mock_generator() -> AsyncGenerator[
                    TTSResponse,
                    None,
                ]:
                    yield TTSResponse(
                        content=AudioBlock(
                            type="audio",
                            source=Base64Source(
                                type="base64",
                                data=self.mock_audio_data,
                                media_type="audio/pcm;rate=24000",
                            ),
                        ),
                    )
                    yield TTSResponse(content=None)

                model._dashscope_callback.get_audio_chunk = mock_generator
                msg = Msg(name="user", content="Test streaming.", role="user")
                response = await model.synthesize(msg)
                self.assertIsInstance(response, AsyncGenerator)
                chunk_count = 0
                async for chunk in response:
                    self.assertIsInstance(chunk, TTSResponse)
                    chunk_count += 1
                self.assertGreater(chunk_count, 0)

    async def test_connect_close_and_error_guards(self) -> None:
        """Realtime model should guard lifecycle and mismatched message ids."""
        mock_modules = self._create_mock_dashscope_modules()
        mock_client = self._create_mock_tts_client()
        mock_tts_class = Mock(return_value=mock_client)
        mock_modules[
            "dashscope.audio.qwen_tts_realtime"
        ].QwenTtsRealtime = mock_tts_class

        with patch.dict("sys.modules", mock_modules):
            model = DashScopeRealtimeTTSModel(
                api_key=self.api_key,
                stream=False,
            )

            with self.assertRaises(RuntimeError):
                await model.push(Msg("user", "hello", "user"))

            with self.assertRaises(RuntimeError):
                await model.synthesize(Msg("user", "hello", "user"))

            await model.connect()
            await model.connect()
            self.assertTrue(model._connected)
            mock_client.connect.assert_called_once()

            model._current_msg_id = "msg-1"
            with self.assertRaises(RuntimeError):
                await model.push(Msg("user", "hello", "user"))
            with self.assertRaises(RuntimeError):
                await model.synthesize(Msg("user", "hello", "user"))

            await model.close()
            await model.close()
            self.assertFalse(model._connected)
            mock_client.close.assert_called_once()

    async def test_cold_start_and_empty_text_paths(self) -> None:
        """Realtime model should respect cold-start gates and empty input."""
        mock_modules = self._create_mock_dashscope_modules()
        mock_client = self._create_mock_tts_client()
        mock_tts_class = Mock(return_value=mock_client)
        mock_modules[
            "dashscope.audio.qwen_tts_realtime"
        ].QwenTtsRealtime = mock_tts_class

        with patch.dict("sys.modules", mock_modules):
            async with DashScopeRealtimeTTSModel(
                api_key=self.api_key,
                stream=False,
                cold_start_length=10,
                cold_start_words=3,
            ) as model:
                model._dashscope_callback.get_audio_data = AsyncMock(
                    return_value=TTSResponse(content=None),
                )
                msg = Msg(name="user", content="hi", role="user")
                response = await model.push(msg)
                self.assertIsNone(response.content)
                mock_client.append_text.assert_not_called()

                empty_msg = Msg(name="user", content="", role="user")
                empty_msg.id = msg.id
                empty_response = await model.push(
                    empty_msg,
                )
                self.assertIsNone(empty_response.content)

                await model.synthesize(None)
                mock_client.commit.assert_called_once()

    async def test_callback_class_handles_events_and_chunks(self) -> None:
        """The realtime callback should accumulate, stream, and reset audio."""

        class DummyCallbackBase:
            """Subclassable stand-in for the SDK callback base."""

        mock_modules = self._create_mock_dashscope_modules()
        mock_modules[
            "dashscope.audio.qwen_tts_realtime"
        ].QwenTtsRealtimeCallback = DummyCallbackBase

        with patch.dict("sys.modules", mock_modules):
            callback_cls = _get_qwen_tts_realtime_callback_class()
            callback = callback_cls()

            callback.on_event({"type": "session.created"})
            callback.on_event({"type": "response.audio.delta", "delta": b"abc"})
            response = await callback.get_audio_data(block=False)
            self.assertEqual(response.content["source"]["data"], "YWJj")

            class EventStub:
                """Deterministic stand-in for threading.Event."""

                def __init__(self, state: bool = False) -> None:
                    self.state = state

                def is_set(self) -> bool:
                    return self.state

                def set(self) -> None:
                    self.state = True

                def clear(self) -> None:
                    self.state = False

                def wait(self) -> None:
                    return None

            await callback._reset()
            callback._audio_data = "delta"
            callback.finish_event = EventStub(False)
            callback.chunk_event = EventStub(True)
            generator = callback.get_audio_chunk()
            first_chunk = await generator.__anext__()
            self.assertFalse(first_chunk["is_last"])
            callback.finish_event.set()
            last_chunk = await generator.__anext__()
            self.assertTrue(last_chunk["is_last"])
            with self.assertRaises(StopAsyncIteration):
                await generator.__anext__()
            self.assertEqual(callback._audio_data, "")

    async def test_callback_exception_path_sets_finish_event(self) -> None:
        """Callback errors should be swallowed and mark the stream finished."""

        class DummyCallbackBase:
            """Subclassable stand-in for the SDK callback base."""

        class BadResponse(dict):
            """Response whose get method raises to hit the exception branch."""

            def get(self, key, default=None):
                raise RuntimeError("boom")

        mock_modules = self._create_mock_dashscope_modules()
        mock_modules[
            "dashscope.audio.qwen_tts_realtime"
        ].QwenTtsRealtimeCallback = DummyCallbackBase

        with patch.dict("sys.modules", mock_modules):
            callback_cls = _get_qwen_tts_realtime_callback_class()
            callback = callback_cls()
            with patch("traceback.print_exc") as mock_print_exc:
                callback.on_event(BadResponse())
            self.assertTrue(callback.finish_event.is_set())
            mock_print_exc.assert_called_once()


class DashScopeTTSModelTest(IsolatedAsyncioTestCase):
    """The unittests for DashScope TTS model."""

    def setUp(self) -> None:
        self.api_key = "test_api_key"

    def _create_mock_response_chunk(self, audio_data: str) -> Mock:
        mock_chunk = Mock()
        mock_chunk.output = Mock()
        mock_chunk.output.audio = Mock()
        mock_chunk.output.audio.data = audio_data
        return mock_chunk

    def test_init(self) -> None:
        """Test initialization of DashScopeTTSModel."""
        model = DashScopeTTSModel(
            api_key=self.api_key,
            model_name="qwen3-tts-flash",
            voice="Cherry",
            stream=False,
        )
        self.assertEqual(model.model_name, "qwen3-tts-flash")
        self.assertEqual(model.voice, "Cherry")
        self.assertFalse(model.stream)
        self.assertFalse(model.supports_streaming_input)

    async def test_synthesize_non_streaming(self) -> None:
        """Test synthesize method in non-streaming mode."""
        model = DashScopeTTSModel(
            api_key=self.api_key,
            stream=False,
        )

        mock_chunks = [
            self._create_mock_response_chunk("audio1"),
            self._create_mock_response_chunk("audio2"),
        ]

        with patch("dashscope.MultiModalConversation.call") as mock_call:
            mock_call.return_value = iter(mock_chunks)
            msg = Msg(name="user", content="Hello! Test message.", role="user")
            response = await model.synthesize(msg)

        expected_content = AudioBlock(
            type="audio",
            source=Base64Source(
                type="base64",
                data="audio1audio2",
                media_type="audio/pcm;rate=24000",
            ),
        )
        self.assertEqual(response.content, expected_content)

    async def test_synthesize_streaming(self) -> None:
        """Test synthesize method in streaming mode."""
        model = DashScopeTTSModel(
            api_key=self.api_key,
            stream=True,
        )

        mock_chunks = [
            self._create_mock_response_chunk("audio1"),
            self._create_mock_response_chunk("audio2"),
        ]

        with patch("dashscope.MultiModalConversation.call") as mock_call:
            mock_call.return_value = iter(mock_chunks)
            msg = Msg(name="user", content="Test streaming.", role="user")
            response = await model.synthesize(msg)

        self.assertIsInstance(response, AsyncGenerator)
        chunks = [chunk async for chunk in response]
        self.assertEqual(len(chunks), 3)
        self.assertEqual(
            chunks[0].content,
            AudioBlock(
                type="audio",
                source=Base64Source(
                    type="base64",
                    data="audio1",
                    media_type="audio/pcm;rate=24000",
                ),
            ),
        )
        self.assertEqual(
            chunks[1].content,
            AudioBlock(
                type="audio",
                source=Base64Source(
                    type="base64",
                    data="audio1audio2",
                    media_type="audio/pcm;rate=24000",
                ),
            ),
        )
        self.assertEqual(
            chunks[2].content,
            AudioBlock(
                type="audio",
                source=Base64Source(
                    type="base64",
                    data="audio1audio2",
                    media_type="audio/pcm;rate=24000",
                ),
            ),
        )
        self.assertTrue(chunks[2].is_last)

    async def test_synthesize_handles_none_empty_and_sparse_chunks(self) -> None:
        """DashScope TTS should handle no text and sparse output chunks."""
        model = DashScopeTTSModel(
            api_key=self.api_key,
            stream=False,
        )

        self.assertIsNone((await model.synthesize(None)).content)
        self.assertIsNone(
            (
                await model.synthesize(
                    Msg(name="user", content="", role="user"),
                )
            ).content,
        )

        chunk_without_output = Mock()
        chunk_without_output.output = None
        chunk_without_audio = Mock()
        chunk_without_audio.output = Mock()
        chunk_without_audio.output.audio = None

        with patch("dashscope.MultiModalConversation.call") as mock_call:
            mock_call.return_value = iter(
                [chunk_without_output, chunk_without_audio],
            )
            response = await model.synthesize(
                Msg(name="user", content="hello", role="user"),
            )

        self.assertEqual(response.content["source"]["data"], "")
