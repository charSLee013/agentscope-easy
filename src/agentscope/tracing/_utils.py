# -*- coding: utf-8 -*-
"""Utility helpers for tracing payload normalization."""
import datetime
import enum
import inspect
import json
from dataclasses import is_dataclass
from typing import Any

from pydantic import BaseModel

from ..message import Msg


def _to_serializable(
    obj: Any,
) -> Any:
    """Convert an object to a JSON-serializable structure."""
    if isinstance(obj, (str, int, bool, float, type(None))):
        return obj

    if isinstance(obj, (list, tuple, set, frozenset)):
        return [_to_serializable(x) for x in obj]

    if isinstance(obj, dict):
        return {str(key): _to_serializable(val) for (key, val) in obj.items()}

    if isinstance(obj, (Msg, BaseModel)) or is_dataclass(obj):
        return repr(obj)

    if inspect.isclass(obj) and issubclass(obj, BaseModel):
        return repr(obj)

    if isinstance(obj, (datetime.date, datetime.datetime, datetime.time)):
        return obj.isoformat()

    if isinstance(obj, datetime.timedelta):
        return obj.total_seconds()

    if isinstance(obj, enum.Enum):
        return _to_serializable(obj.value)

    return str(obj)


def _serialize_to_str(value: Any) -> str:
    """Serialize arbitrary values into a JSON string."""
    try:
        return json.dumps(value, ensure_ascii=False)

    except TypeError:
        return json.dumps(
            _to_serializable(value),
            ensure_ascii=False,
        )
