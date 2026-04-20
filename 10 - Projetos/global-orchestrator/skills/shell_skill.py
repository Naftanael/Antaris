from core.base_skill import BaseSkill
from typing import Any, Dict
import subprocess

class ShellSkill(BaseSkill):
    @property
    def name(self) -> str:
        return "shell_skill"

    @property
    def description(self) -> str:
        return "Executa comandos bash no sistema. Use com cautela para operações de arquivo ou sistema."

    def execute(self, arguments: Dict[str, Any]) -> Any:
        command = arguments.get("command", "")
        
        # Bloqueio simples de comandos perigosos para este exemplo
        forbidden = ["rm -rf /", "mkfs", "dd"]
        if any(f in command for f in forbidden):
            return "Operação bloqueada por segurança."

        try:
            result = subprocess.check_output(command, shell=True, stderr=subprocess.STDOUT, text=True)
            return result if result else "Comando executado com sucesso (sem saída)."
        except subprocess.CalledProcessError as e:
            return f"Erro ao executar comando: {e.output}"
        except Exception as e:
            return f"Erro inesperado: {str(e)}"
