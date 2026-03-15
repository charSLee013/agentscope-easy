# -*- coding: utf-8 -*-
"""Unittests for context-local runtime configuration."""
import asyncio
import threading
from unittest.async_case import IsolatedAsyncioTestCase

import agentscope
from agentscope import _config


result = {}


async def async_task(field: str):
    """Mutate config inside an async task and return the local value."""
    prefix = "async_task"
    agentscope.init(
        run_id=f"{prefix}_run_id",
        project=f"{prefix}_project",
        name=f"{prefix}_name",
    )
    if field == "trace_enabled":
        _config.trace_enabled = True
        return _config.trace_enabled
    if field == "audio_playback_enabled":
        _config.audio_playback_enabled = True
        return _config.audio_playback_enabled
    return getattr(_config, field)


def sync_task(field: str) -> None:
    """Mutate config inside a thread and store the local value."""
    prefix = "sync_task"
    agentscope.init(
        run_id=f"{prefix}_run_id",
        project=f"{prefix}_project",
        name=f"{prefix}_name",
    )
    if field == "trace_enabled":
        _config.trace_enabled = True
    elif field == "audio_playback_enabled":
        _config.audio_playback_enabled = True
    result["value"] = getattr(_config, field)


class ConfigTest(IsolatedAsyncioTestCase):
    """Unittests for the config module."""

    async def test_config_attributes_are_context_local(self) -> None:
        """Config writes should stay isolated across tasks and threads."""
        agentscope.init(
            project="root_project",
            name="root_name",
            run_id="root_run_id",
        )
        _config.trace_enabled = False
        _config.audio_playback_enabled = False

        expected_root = {
            "project": "root_project",
            "name": "root_name",
            "run_id": "root_run_id",
            "trace_enabled": False,
            "audio_playback_enabled": False,
        }
        expected_async = {
            "project": "async_task_project",
            "name": "async_task_name",
            "run_id": "async_task_run_id",
            "trace_enabled": True,
            "audio_playback_enabled": True,
        }
        expected_sync = {
            "project": "sync_task_project",
            "name": "sync_task_name",
            "run_id": "sync_task_run_id",
            "trace_enabled": True,
            "audio_playback_enabled": True,
        }

        for field, root_value in expected_root.items():
            self.assertEqual(getattr(_config, field), root_value)

            async_value = await asyncio.create_task(async_task(field))
            self.assertEqual(async_value, expected_async[field])
            self.assertEqual(getattr(_config, field), root_value)

            thread = threading.Thread(target=sync_task, args=(field,))
            thread.start()
            thread.join()

            self.assertEqual(result["value"], expected_sync[field])
            self.assertEqual(getattr(_config, field), root_value)
