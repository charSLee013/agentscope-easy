# -*- coding: utf-8 -*-
"""Tests for the agentscope logger lifecycle."""

import logging
import shutil
from pathlib import Path
from tempfile import TemporaryDirectory

from agentscope._logging import logger, setup_logger


def _get_file_handler(filepath: Path) -> logging.FileHandler:
    for handler in logger.handlers:
        if (
            isinstance(handler, logging.FileHandler)
            and Path(handler.baseFilename) == filepath
        ):
            return handler
    raise AssertionError(f"No file handler registered for {filepath}")


def test_setup_logger_closes_replaced_file_handlers() -> None:
    """Replacing logger config should not leak an open file handler."""
    with TemporaryDirectory() as tmpdir:
        log_file = Path(tmpdir) / "log" / "demo.md"
        setup_logger("INFO", str(log_file))
        file_handler = _get_file_handler(log_file)

        setup_logger("INFO")

        assert file_handler.stream is None


def test_file_logger_recreates_parent_directory_when_reopened() -> None:
    """A reopened file handler should honor the originally requested path."""
    with TemporaryDirectory() as tmpdir:
        log_file = Path(tmpdir) / "log" / "demo.md"
        setup_logger("INFO", str(log_file))
        logger.info("before close")
        file_handler = _get_file_handler(log_file)

        file_handler.close()
        shutil.rmtree(log_file.parent)

        logger.info("after close")

        assert log_file.exists()
        setup_logger("INFO")
        assert file_handler.stream is None
