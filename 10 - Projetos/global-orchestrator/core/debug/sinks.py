from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Protocol, TextIO

from .events import DebugEvent, EventLevel


_LEVEL_ORDER = {
    EventLevel.DEBUG: 10,
    EventLevel.INFO: 20,
    EventLevel.WARNING: 30,
    EventLevel.ERROR: 40,
}


class EventSink(Protocol):
    def write(self, event: DebugEvent) -> None:
        ...

    def flush(self) -> None:
        ...

    def close(self) -> None:
        ...


class ConsoleSink:
    def __init__(
        self,
        stream: TextIO | None = None,
        *,
        include_payload: bool = True,
        min_level: EventLevel = EventLevel.DEBUG,
    ):
        self.stream = stream or sys.stdout
        self.include_payload = include_payload
        self.min_level = min_level

    def _is_enabled_for(self, event: DebugEvent) -> bool:
        return _LEVEL_ORDER[event.level] >= _LEVEL_ORDER[self.min_level]

    def write(self, event: DebugEvent) -> None:
        if not self._is_enabled_for(event):
            return

        payload_text = ""
        if self.include_payload and event.payload:
            payload_text = f" | payload={json.dumps(event.payload, ensure_ascii=False, sort_keys=True)}"

        message_text = f" - {event.message}" if event.message else ""
        component_text = f" [{event.component}]" if event.component else ""
        line = (
            f"[{event.timestamp.isoformat()}] "
            f"{event.level.value.upper()} "
            f"{event.name}{component_text}{message_text}{payload_text}\n"
        )
        self.stream.write(line)
        self.flush()

    def flush(self) -> None:
        self.stream.flush()

    def close(self) -> None:
        self.flush()


class JSONLSink:
    def __init__(self, path: str | Path):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def write(self, event: DebugEvent) -> None:
        with self.path.open("a", encoding="utf-8") as handle:
            handle.write(event.to_json())
            handle.write("\n")

    def flush(self) -> None:
        return None

    def close(self) -> None:
        return None
