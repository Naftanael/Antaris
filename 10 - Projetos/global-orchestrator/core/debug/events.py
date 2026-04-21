from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field as dataclass_field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, Optional
from uuid import uuid4

try:
    from pydantic import BaseModel, Field
except ImportError:  # pragma: no cover - fallback para ambientes sem pydantic instalado
    BaseModel = None
    Field = None


class EventLevel(str, Enum):
    DEBUG = "debug"
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"


if BaseModel is not None:
    class DebugEvent(BaseModel):
        event_id: str = Field(default_factory=lambda: str(uuid4()))
        name: str
        level: EventLevel = EventLevel.INFO
        timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
        message: Optional[str] = None
        component: Optional[str] = None
        correlation_id: Optional[str] = None
        payload: Dict[str, Any] = Field(default_factory=dict)

        def to_dict(self) -> Dict[str, Any]:
            if hasattr(self, "model_dump"):
                return self.model_dump(mode="json")

            data = self.dict()
            timestamp = data.get("timestamp")
            if isinstance(timestamp, datetime):
                data["timestamp"] = timestamp.isoformat()

            level = data.get("level")
            if isinstance(level, EventLevel):
                data["level"] = level.value

            return data

        def to_json(self) -> str:
            return json.dumps(self.to_dict(), ensure_ascii=False)
else:
    @dataclass
    class DebugEvent:
        name: str
        level: EventLevel = EventLevel.INFO
        timestamp: datetime = dataclass_field(default_factory=lambda: datetime.now(timezone.utc))
        event_id: str = dataclass_field(default_factory=lambda: str(uuid4()))
        message: Optional[str] = None
        component: Optional[str] = None
        correlation_id: Optional[str] = None
        payload: Dict[str, Any] = dataclass_field(default_factory=dict)

        def to_dict(self) -> Dict[str, Any]:
            data = asdict(self)
            data["timestamp"] = self.timestamp.isoformat()
            data["level"] = self.level.value
            return data

        def to_json(self) -> str:
            return json.dumps(self.to_dict(), ensure_ascii=False)
