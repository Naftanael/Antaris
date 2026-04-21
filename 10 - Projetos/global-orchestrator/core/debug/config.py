from __future__ import annotations

import sys
from pathlib import Path

from .events import EventLevel
from .sinks import ConsoleSink, JSONLSink
from .tracer import SinkTracer, Tracer


def build_runtime_tracer(
    *,
    debug: bool = False,
    trace: bool = False,
    jsonl_path: str | Path | None = None,
) -> Tracer | None:
    """
    Builds an optional runtime tracer for CLI/API consumption.

    - Normal mode: returns None (no tracing output).
    - Debug mode: console events at INFO+ without payload.
    - Trace mode: console events at DEBUG+ with payload.
    - JSONL sink: enabled whenever `jsonl_path` is provided.
    """
    sinks = []

    if debug or trace:
        sinks.append(
            ConsoleSink(
                stream=sys.stderr,
                include_payload=trace,
                min_level=EventLevel.DEBUG if trace else EventLevel.INFO,
            )
        )

    if jsonl_path:
        sinks.append(JSONLSink(jsonl_path))

    if not sinks:
        return None

    return SinkTracer(sinks)
