# -*- coding: utf-8 -*-
"""Contract tests for LongTermMemoryBase."""
import inspect
from unittest import TestCase

from agentscope.memory import LongTermMemoryBase


class LongTermMemoryBaseContractTest(TestCase):
    """Lock the public retrieve signatures used by long-term memory impls."""

    def test_retrieve_apis_expose_limit_parameter(self) -> None:
        """Both retrieve entry points should publish a `limit` kwarg."""
        retrieve_sig = inspect.signature(LongTermMemoryBase.retrieve)
        retrieve_from_sig = inspect.signature(
            LongTermMemoryBase.retrieve_from_memory,
        )

        self.assertIn("limit", retrieve_sig.parameters)
        self.assertEqual(retrieve_sig.parameters["limit"].default, 5)
        self.assertIn("limit", retrieve_from_sig.parameters)
        self.assertEqual(retrieve_from_sig.parameters["limit"].default, 5)
