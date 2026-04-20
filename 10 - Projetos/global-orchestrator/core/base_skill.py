from abc import ABC, abstractmethod
from typing import Any, Dict

class BaseSkill(ABC):
    """
    Classe base abstrata para todas as habilidades do orquestrador.
    Cada nova habilidade deve herdar desta classe.
    """
    
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
