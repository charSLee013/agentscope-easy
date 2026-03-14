# -*- coding: utf-8 -*-
"""Tracing utils tests."""
from datetime import datetime, timedelta
from unittest import TestCase

from pydantic import BaseModel

from agentscope.message import Msg
from agentscope.tracing._utils import _serialize_to_str, _to_serializable


class ExampleModel(BaseModel):
    """Simple model used by tracing utility tests."""

    value: int


class TracingUtilsTest(TestCase):
    """Tests for tracing serialization helpers."""

    def test_to_serializable_supports_msg_model_and_datetime(self) -> None:
        """Known rich objects should serialize into stable JSON shapes."""
        msg = Msg("user", "hello", "user")
        model = ExampleModel(value=3)
        now = datetime(2026, 1, 2, 3, 4, 5)
        delta = timedelta(seconds=7)

        payload = _to_serializable(
            {
                "msg": msg,
                "model": model,
                "time": now,
                "delta": delta,
            },
        )

        self.assertEqual(payload["msg"], repr(msg))
        self.assertEqual(payload["model"], repr(model))
        self.assertEqual(payload["time"], now.isoformat())
        self.assertEqual(payload["delta"], 7.0)

    def test_serialize_to_str_handles_nested_values(self) -> None:
        """Nested payloads should serialize without raising."""
        payload = {
            "items": [
                Msg("assistant", "done", "assistant"),
                ExampleModel(value=9),
            ],
        }

        rendered = _serialize_to_str(payload)

        self.assertIn('"items"', rendered)
        self.assertIn("ExampleModel", rendered)
