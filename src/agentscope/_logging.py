# -*- coding: utf-8 -*-
"""The logger for agentscope."""

import logging
import os


_DEFAULT_FORMAT = (
    "%(asctime)s | %(levelname)-7s | "
    "%(module)s:%(funcName)s:%(lineno)s - %(message)s"
)

logger = logging.getLogger("as")


class _DirectoryCreatingFileHandler(logging.FileHandler):
    """FileHandler that recreates its parent directory before opening."""

    def _open(self):  # type: ignore[no-untyped-def]
        os.makedirs(os.path.dirname(self.baseFilename), exist_ok=True)
        return super()._open()


def setup_logger(
    level: str,
    filepath: str | None = None,
) -> None:
    """Set up the agentscope logger.

    Args:
        level (`str`):
            The logging level, chosen from "INFO", "DEBUG", "WARNING",
            "ERROR", "CRITICAL".
        filepath (`str | None`, optional):
            The filepath to save the logging output.
    """
    if level not in ["INFO", "DEBUG", "WARNING", "ERROR", "CRITICAL"]:
        raise ValueError(
            f"Invalid logging level: {level}. Must be one of "
            f"'INFO', 'DEBUG', 'WARNING', 'ERROR', 'CRITICAL'.",
        )
    for handler in list(logger.handlers):
        logger.removeHandler(handler)
        handler.close()

    logger.setLevel(level)
    handler = logging.StreamHandler()
    handler.setFormatter(logging.Formatter(_DEFAULT_FORMAT))
    logger.addHandler(handler)

    if filepath:
        handler = _DirectoryCreatingFileHandler(filepath)
        handler.setFormatter(logging.Formatter(_DEFAULT_FORMAT))
        logger.addHandler(handler)

    logger.propagate = False


setup_logger("INFO")
