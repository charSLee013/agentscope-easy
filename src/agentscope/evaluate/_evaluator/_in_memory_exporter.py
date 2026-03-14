# -*- coding: utf-8 -*-
"""In-memory trace exporter for evaluation statistics."""
import json
from collections import defaultdict
from typing import Any, Sequence

from opentelemetry import baggage
from opentelemetry.sdk.trace import ReadableSpan
from opentelemetry.sdk.trace.export import SpanExporter, SpanExportResult

from ...tracing._types import SpanAttributes, SpanKind


def _decode_trace_attr(value: Any) -> Any:
    """Decode JSON-serialized trace attributes when needed."""
    if isinstance(value, str):
        try:
            return json.loads(value)
        except json.JSONDecodeError:
            return value
    return value


class _InMemoryExporter(SpanExporter):
    """Collect lightweight evaluation statistics from tracing spans."""

    def __init__(self) -> None:
        """Initialize the exporter."""
        self.cnt: dict[str, dict[str, dict[str, Any]]] = {}
        self._stopped = False

    def export(self, spans: Sequence[ReadableSpan]) -> SpanExportResult:
        """Export a batch of spans into the in-memory counters."""
        for span in spans:
            task_id = baggage.get_baggage("task_id")
            repeat_id = baggage.get_baggage("repeat_id")
            if task_id is None or repeat_id is None:
                continue

            if task_id not in self.cnt:
                self.cnt[task_id] = {}
            if repeat_id not in self.cnt[task_id]:
                self.cnt[task_id][repeat_id] = {
                    "llm": defaultdict(int),
                    "agent": 0,
                    "tool": defaultdict(int),
                    "embedding": defaultdict(int),
                    "chat_usage": {},
                }

            current = self.cnt[task_id][repeat_id]
            span_kind = _decode_trace_attr(
                span.attributes.get(SpanAttributes.SPAN_KIND),
            )
            meta = _decode_trace_attr(
                span.attributes.get(SpanAttributes.META, "{}"),
            )
            output = _decode_trace_attr(
                span.attributes.get(SpanAttributes.OUTPUT, "{}"),
            )

            if span_kind == SpanKind.LLM.value:
                model_name = meta.get("model_name", "unknown")
                current["llm"][model_name] += 1
                if model_name not in current["chat_usage"]:
                    current["chat_usage"][model_name] = defaultdict(int)

                usage = output.get("usage", {}) if isinstance(output, dict) else {}
                current["chat_usage"][model_name]["input_tokens"] += usage.get(
                    "input_tokens",
                    0,
                )
                current["chat_usage"][model_name]["output_tokens"] += usage.get(
                    "output_tokens",
                    0,
                )

            elif span_kind == SpanKind.AGENT.value:
                current["agent"] += 1

            elif span_kind == SpanKind.TOOL.value:
                tool_name = meta.get("name", "unknown")
                current["tool"][tool_name] += 1

            elif span_kind == SpanKind.EMBEDDING.value:
                model_name = meta.get("model_name", "unknown")
                current["embedding"][model_name] += 1

        return SpanExportResult.SUCCESS

    def shutdown(self) -> None:
        """Mark the exporter as stopped."""
        self._stopped = True
