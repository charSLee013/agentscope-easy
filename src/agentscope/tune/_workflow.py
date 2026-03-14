# -*- coding: utf-8 -*-
"""Workflow typing helpers for AgentScope training."""
from __future__ import annotations

import inspect
from typing import Awaitable, Callable, Dict, get_type_hints

from .._logging import logger
from ..model import TrinityChatModel

WorkflowType = Callable[[Dict, TrinityChatModel], Awaitable[float]]


def _validate_function_signature(func: Callable) -> bool:
    """Validate whether a workflow matches the Trinity training contract."""
    if not inspect.iscoroutinefunction(func):
        logger.warning("The workflow function is not asynchronous.")
        return False

    expected_params = [
        ("task", Dict),
        ("model", TrinityChatModel),
    ]
    expected_return = float

    func_signature = inspect.signature(func)
    func_hints = get_type_hints(func)

    if len(func_signature.parameters) != len(expected_params):
        logger.warning(
            "Expected %d parameters, but got %d",
            len(expected_params),
            len(func_signature.parameters),
        )
        return False

    for (param_name, _), (expected_name, expected_type) in zip(
        func_signature.parameters.items(),
        expected_params,
    ):
        if (
            param_name != expected_name
            or func_hints.get(param_name) != expected_type
        ):
            logger.warning(
                "Expected parameter %s of type %s, but got %s of type %s",
                expected_name,
                expected_type,
                param_name,
                func_hints.get(param_name),
            )
            return False

    if func_hints.get("return") != expected_return:
        logger.warning(
            "Expected return type %s, but got %s",
            expected_return,
            func_hints.get("return"),
        )
        return False

    return True
