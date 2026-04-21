from typing import Any, Dict

from core.debug.config import build_runtime_tracer
from core.debug.tracer import Tracer
from core.orchestrator import GlobalOrchestrator

class GlobalAgent:
    """
    Interface de biblioteca para o Global Orchestrator.
    Uso:
        agent = GlobalAgent()
        res = agent.ask("Quanto é 2 + 2?")
    """
    def __init__(
        self,
        tracer: Tracer | None = None,
        *,
        debug: bool = False,
        trace: bool = False,
        jsonl_path: str | None = None,
    ):
        runtime_tracer = tracer or build_runtime_tracer(
            debug=debug,
            trace=trace,
            jsonl_path=jsonl_path,
        )
        self.orchestrator = GlobalOrchestrator(tracer=runtime_tracer)

    def ask(self, message: str) -> Dict[str, Any]:
        """Envia uma mensagem para o orquestrador e retorna o resultado estruturado."""
        return self.orchestrator.process_request(message)

    def list_capabilities(self) -> Dict[str, str]:
        """Retorna um dicionário de habilidades e suas descrições."""
        return {name: skill.description for name, skill in self.orchestrator.skills.items()}
