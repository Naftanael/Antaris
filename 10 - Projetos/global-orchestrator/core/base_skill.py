from abc import ABC, abstractmethod
from typing import Any, Dict

from core.debug.events import EventLevel
from core.debug.tracer import Tracer, ensure_tracer


class BaseSkill(ABC):
    """
    Classe base abstrata para todas as habilidades do orquestrador.
    Cada nova habilidade deve herdar desta classe.
    """
    def __init__(self, tracer: Tracer | None = None):
        self._tracer = ensure_tracer(tracer)
        self._trace_context: Dict[str, Any] = {}

    def set_tracer(self, tracer: Tracer | None) -> None:
        self._tracer = ensure_tracer(tracer)

    @property
    def tracer(self) -> Tracer:
        return self._tracer

    def set_trace_context(self, **context: Any) -> None:
        self._trace_context = {
            key: value for key, value in context.items() if value is not None
        }

    def clear_trace_context(self) -> None:
        self._trace_context = {}

    def trace_event(
        self,
        name: str,
        *,
        level: EventLevel = EventLevel.INFO,
        message: str | None = None,
        payload: Dict[str, Any] | None = None,
    ) -> None:
        merged_payload = dict(self._trace_context)
        merged_payload.update(dict(payload or {}))
        self._tracer.trace(
            name,
            level=level,
            message=message,
            component=f"skills.{self.name}",
            payload=merged_payload,
        )
    
    @property
    @abstractmethod
    def name(self) -> str:
        """Nome único da habilidade."""
        pass

    @property
    @abstractmethod
    def description(self) -> str:
        """Descrição detalhada para que o LLM saiba quando usar esta skill."""
        pass

    @abstractmethod
    def execute(self, arguments: Dict[str, Any]) -> Any:
        """
        Executa a lógica da habilidade.
        Recebe um dicionário de argumentos extraído pelo LLM.
        """
        pass
