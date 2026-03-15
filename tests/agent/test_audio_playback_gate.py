# -*- coding: utf-8 -*-
"""Tests for runtime-gated audio playback in AgentBase."""
from __future__ import annotations

import asyncio
import sys
from io import BytesIO
from types import SimpleNamespace
from unittest import TestCase
from unittest.mock import Mock, patch

import numpy as np

from agentscope import _config
from agentscope.agent import AgentBase
from agentscope.message import AudioBlock, Msg


class DummyAgent(AgentBase):
    """Minimal agent used to exercise audio playback helpers."""

    async def observe(self, msg):
        raise NotImplementedError()

    async def reply(self, *args, **kwargs):
        raise NotImplementedError()


class AudioPlaybackGateTest(TestCase):
    """Tests for audio playback gating and URL playback support."""

    def setUp(self) -> None:
        _config.audio_playback_enabled = False

    def tearDown(self) -> None:
        _config.audio_playback_enabled = False

    def test_audio_playback_is_disabled_by_default(self) -> None:
        """Audio blocks should be ignored until playback is enabled."""
        agent = DummyAgent()
        audio_block = AudioBlock(
            type="audio",
            source={
                "type": "base64",
                "media_type": "audio/wav",
                "data": "AAAA",
            },
        )

        agent._process_audio_block("msg-1", audio_block)

        self.assertNotIn("msg-1", agent._stream_prefix)

    def test_base64_audio_plays_when_runtime_flag_is_enabled(self) -> None:
        """Base64 audio should stream through sounddevice when enabled."""
        agent = DummyAgent()
        _config.audio_playback_enabled = True

        stream = Mock()
        fake_sd = SimpleNamespace(
            OutputStream=Mock(return_value=stream),
        )
        audio_bytes = np.array([1, -1, 2], dtype=np.int16).tobytes()
        audio_block = AudioBlock(
            type="audio",
            source={
                "type": "base64",
                "media_type": "audio/wav",
                "data": audio_bytes.hex(),
            },
        )

        with patch.dict(sys.modules, {"sounddevice": fake_sd}):
            with patch("base64.b64decode", return_value=audio_bytes):
                agent._process_audio_block("msg-2", audio_block)

        fake_sd.OutputStream.assert_called_once()
        stream.start.assert_called_once()
        stream.write.assert_called_once()
        self.assertIn("msg-2", agent._stream_prefix)

    def test_url_audio_plays_when_runtime_flag_is_enabled(self) -> None:
        """URL audio should download and play only when enabled."""
        agent = DummyAgent()
        _config.audio_playback_enabled = True

        fake_sd = SimpleNamespace(
            play=Mock(),
            wait=Mock(),
        )
        audio_frames = np.array([1, 2, 3], dtype=np.int16).tobytes()
        response = BytesIO(b"wav-bytes")
        response.__enter__ = lambda self=response: self
        response.__exit__ = lambda *args: None
        wav_file = Mock()
        wav_file.getframerate.return_value = 16000
        wav_file.getnframes.return_value = 3
        wav_file.readframes.return_value = audio_frames
        wav_file.__enter__ = lambda self=wav_file: self
        wav_file.__exit__ = lambda *args: None
        audio_block = AudioBlock(
            type="audio",
            source={
                "type": "url",
                "url": "https://example.com/audio.wav",
            },
        )

        with patch.dict(sys.modules, {"sounddevice": fake_sd}):
            with patch(
                "urllib.request.urlopen",
                return_value=response,
            ):
                with patch("wave.open", return_value=wav_file):
                    agent._process_audio_block("msg-3", audio_block)

        fake_sd.play.assert_called_once()
        fake_sd.wait.assert_called_once()
        played_audio, samplerate = fake_sd.play.call_args[0]
        self.assertEqual(samplerate, 16000)
        self.assertTrue(
            np.array_equal(
                played_audio,
                np.frombuffer(audio_frames, dtype=np.int16),
            ),
        )

    def test_print_processes_speech_side_channel(self) -> None:
        """AgentBase.print should process the explicit speech side channel."""
        agent = DummyAgent()
        _config.audio_playback_enabled = True

        stream = Mock()
        fake_sd = SimpleNamespace(
            OutputStream=Mock(return_value=stream),
        )
        audio_bytes = np.array([1, -1, 2], dtype=np.int16).tobytes()
        audio_block = AudioBlock(
            type="audio",
            source={
                "type": "base64",
                "media_type": "audio/wav",
                "data": audio_bytes.hex(),
            },
        )

        with patch.dict(sys.modules, {"sounddevice": fake_sd}):
            with patch("base64.b64decode", return_value=audio_bytes):
                asyncio.run(
                    agent.print(
                        Msg("assistant", "hello", "assistant"),
                        speech=audio_block,
                    ),
                )

        fake_sd.OutputStream.assert_called_once()
        stream.start.assert_called_once()
        stream.write.assert_called_once()
