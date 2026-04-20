from core.orchestrator import GlobalOrchestrator
from typing import Any, Dict

class GlobalAgent:
    """
    Interface de biblioteca para o Global Orchestrator.
    Uso:
        agent = GlobalAgent()
        res = agent.ask("Quanto é 2 + 2?")
    """
    def __init__(self):
        self.orchestrator = GlobalOrchestrator()

    def ask(self, message: str) -> Dict[str, Any]:
        """Envia uma mensagem para o orquestrador e retorna o resultado estruturado."""
        return self.orchestrator.process_request(message)

    def list_capabilities(self) -> Dict[str, str]:
        """Retorna um dicionário de habilidades e suas descrições."""
        return {name: skill.description for name, skill in self.orchestrator.skills.items()}
