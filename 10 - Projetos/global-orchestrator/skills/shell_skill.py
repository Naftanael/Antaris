from core.base_skill import BaseSkill
from core.debug.events import EventLevel
import hashlib
import re
import time
from typing import Any, Dict
import subprocess

class ShellSkill(BaseSkill):
    @property
    def name(self) -> str:
        return "shell_skill"

    @property
    def description(self) -> str:
        return "Executa comandos bash no sistema. Use com cautela para operações de arquivo ou sistema."

    def _sanitize_command(self, command: str) -> str:
        safe = command.strip()
        # Redact common key/value secret patterns.
        safe = re.sub(
            r"(?i)\b(api[_-]?key|token|secret|password)\s*=\s*([^\s]+)",
            r"\1=<redacted>",
            safe,
        )
        safe = re.sub(
            r"(?i)(--(?:api[_-]?key|token|secret|password)\s+)([^\s]+)",
            r"\1<redacted>",
            safe,
        )
        return safe[:240]

    def execute(self, arguments: Dict[str, Any]) -> Any:
        command = arguments.get("command", "")
        start = time.perf_counter()
        safe_command = self._sanitize_command(command)
        command_hash = hashlib.sha256(command.encode("utf-8", errors="ignore")).hexdigest()[:12]
        self.trace_event(
            "skill_execution_started",
            level=EventLevel.INFO,
            payload={
                "skill_name": self.name,
                "command_safe": safe_command,
                "command_hash": command_hash,
            },
        )
        
        # Bloqueio simples de comandos perigosos para este exemplo
        forbidden = ["rm -rf /", "mkfs", "dd"]
        if any(f in command for f in forbidden):
            duration_ms = round((time.perf_counter() - start) * 1000, 3)
            self.trace_event(
                "skill_execution_finished",
                level=EventLevel.WARNING,
                payload={
                    "skill_name": self.name,
                    "status": "blocked",
                    "duration_ms": duration_ms,
                    "command_safe": safe_command,
                    "command_hash": command_hash,
                },
            )
            return "Operação bloqueada por segurança."

        try:
            result = subprocess.check_output(command, shell=True, stderr=subprocess.STDOUT, text=True)
            duration_ms = round((time.perf_counter() - start) * 1000, 3)
            self.trace_event(
                "skill_execution_finished",
                level=EventLevel.INFO,
                payload={
                    "skill_name": self.name,
                    "status": "success",
                    "duration_ms": duration_ms,
                    "command_safe": safe_command,
                    "command_hash": command_hash,
                    "output_length": len(result or ""),
                },
            )
            return result if result else "Comando executado com sucesso (sem saída)."
        except subprocess.CalledProcessError as e:
            duration_ms = round((time.perf_counter() - start) * 1000, 3)
            self.trace_event(
                "skill_execution_error",
                level=EventLevel.ERROR,
                payload={
                    "skill_name": self.name,
                    "duration_ms": duration_ms,
                    "command_safe": safe_command,
                    "command_hash": command_hash,
                    "error_type": type(e).__name__,
                    "returncode": e.returncode,
                    "output_length": len(e.output or ""),
                },
            )
            return f"Erro ao executar comando: {e.output}"
        except Exception as e:
            duration_ms = round((time.perf_counter() - start) * 1000, 3)
            self.trace_event(
                "skill_execution_error",
                level=EventLevel.ERROR,
                payload={
                    "skill_name": self.name,
                    "duration_ms": duration_ms,
                    "command_safe": safe_command,
                    "command_hash": command_hash,
                    "error_type": type(e).__name__,
                    "error": str(e)[:200],
                },
            )
            return f"Erro inesperado: {str(e)}"
