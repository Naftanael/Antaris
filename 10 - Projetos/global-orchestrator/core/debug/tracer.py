from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Iterable, Mapping, Optional

from .events import DebugEvent, EventLevel
from .sinks import EventSink


class Tracer(ABC):
    @abstractmethod
    def emit(self, event: DebugEvent) -> None:
        """Emite um evento estruturado."""

    def trace(
        self,
        name: str,
        *,
        level: EventLevel = EventLevel.INFO,
        message: str | None = None,
        component: str | None = None,
        correlation_id: str | None = None,
        payload: Optional[Mapping[str, Any]] = None,
    ) -> DebugEvent:
        event = DebugEvent(
            name=name,
            level=level,
            message=message,
            component=component,
            correlation_id=correlation_id,
            payload=dict(payload or {}),
        )
        self.emit(event)
        return event

    def flush(self) -> None:
        return None

    def close(self) -> None:
        return None


class NullTracer(Tracer):
    def emit(self, event: DebugEvent) -> None:
        return None


class SinkTracer(Tracer):
    def __init__(self, sinks: Iterable[EventSink] | None = None):
        self.sinks = [sink for sink in (sinks or []) if sink is not None]

    def emit(self, event: DebugEvent) -> None:
        for sink in self.sinks:
            sink.write(event)

    def flush(self) -> None:
        for sink in self.sinks:
            sink.flush()

    def close(self) -> None:
        for sink in self.sinks:
            sink.close()


class CompositeTracer(Tracer):
    def __init__(self, tracers: Iterable[Tracer] | None = None):
        self.tracers = [tracer for tracer in (tracers or []) if tracer is not None]

    def emit(self, event: DebugEvent) -> None:
        for tracer in self.tracers:
            tracer.emit(event)

    def flush(self) -> None:
        for tracer in self.tracers:
            tracer.flush()

    def close(self) -> None:
        for tracer in self.tracers:
            tracer.close()


def ensure_tracer(tracer: Tracer | None) -> Tracer:
    return tracer if tracer is not None else NullTracer()
