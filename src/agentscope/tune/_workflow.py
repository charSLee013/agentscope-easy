# -*- coding: utf-8 -*-
"""Workflow typing helpers for AgentScope training."""
from __future__ import annotations

import inspect
from typing import Awaitable, Callable, Dict

from .._logging import logger
from ..model import TrinityChatModel

WorkflowType = Callable[[Dict, TrinityChatModel], Awaitable[float]]


def _validate_function_signature(func: Callable) -> bool:
    """Validate whether a workflow matches the Trinity training contract."""
    if not inspect.iscoroutinefunction(func):
        logger.warning("The workflow function is not asynchronous.")
        return False

    func_signature = inspect.signature(func)
    parameters = list(func_signature.parameters.values())

    try:
        func_signature.bind_partial({}, TrinityChatModel)
    except TypeError:
        logger.warning(
            "The workflow must accept at least two positional arguments.",
        )
        return False

    for param in parameters[2:]:
        if param.kind in (
            inspect.Parameter.VAR_POSITIONAL,
            inspect.Parameter.VAR_KEYWORD,
        ):
            continue
        if param.default is inspect.Parameter.empty:
            logger.warning(
                "The workflow cannot require parameters beyond the first two.",
            )
            return False

    return True
