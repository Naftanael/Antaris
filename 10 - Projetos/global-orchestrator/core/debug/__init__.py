from .config import build_runtime_tracer
from .events import DebugEvent, EventLevel
from .sinks import ConsoleSink, EventSink, JSONLSink
from .tracer import CompositeTracer, NullTracer, SinkTracer, Tracer, ensure_tracer


def read_jsonl(*args, **kwargs):
    # Lazy import avoids runpy warnings on `python -m core.debug.replay`.
    from .replay import read_jsonl as _read_jsonl

    return _read_jsonl(*args, **kwargs)


def replay_by_request_id(*args, **kwargs):
    # Lazy import avoids runpy warnings on `python -m core.debug.replay`.
    from .replay import replay_by_request_id as _replay_by_request_id

    return _replay_by_request_id(*args, **kwargs)

__all__ = [
    "build_runtime_tracer",
    "CompositeTracer",
    "ConsoleSink",
    "DebugEvent",
    "EventLevel",
    "EventSink",
    "JSONLSink",
    "NullTracer",
    "read_jsonl",
    "replay_by_request_id",
    "SinkTracer",
    "Tracer",
    "ensure_tracer",
]
