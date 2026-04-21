from __future__ import annotations

import subprocess
import sys
from pathlib import Path
from typing import Any, Dict

from core.base_skill import BaseSkill


class AntarisVaultSkill(BaseSkill):
    @property
    def name(self) -> str:
        return "antaris_vault_skill"

    @property
    def description(self) -> str:
        return (
            "Consulta e opera o vault Antaris/Obsidian e o brain local. "
            "Use para bootstrap de contexto, busca em notas, notas relacionadas, "
            "notas recentes, resumo de notas, health check das integracoes e busca hibrida no brain."
        )

    @property
    def repo_root(self) -> Path:
        return Path(__file__).resolve().parents[3]

    @property
    def hub_script(self) -> Path:
        return self.repo_root / ".agent" / "scripts" / "antigravity_hub.py"

    def _run_hub(self, *hub_args: str) -> str:
        completed = subprocess.run(
            [sys.executable, str(self.hub_script), *hub_args],
            cwd=self.repo_root,
            capture_output=True,
            text=True,
        )
        if completed.returncode != 0:
            stderr = completed.stderr.strip()
            stdout = completed.stdout.strip()
            details = stderr or stdout or f"hub exited with code {completed.returncode}"
            return f"Erro na integracao Antaris: {details}"
        return completed.stdout.strip() or "Operacao concluida sem saida."

    def execute(self, arguments: Dict[str, Any]) -> Any:
        action = str(arguments.get("action", "search")).strip().lower()
        limit = str(arguments.get("limit", 5))

        if action == "bootstrap":
            return self._run_hub("bootstrap")

        if action == "search":
            query = str(arguments.get("query", "")).strip()
            if not query:
                return "Nenhuma query fornecida para busca no vault."
            return self._run_hub("search", query, "--limit", limit)

        if action == "related":
            target = str(arguments.get("target", arguments.get("title", ""))).strip()
            if not target:
                return "Nenhum alvo fornecido para relacionadas."
            return self._run_hub("related", target)

        if action == "recent":
            days = str(arguments.get("days", 7))
            return self._run_hub("recent", "--days", days, "--limit", limit)

        if action == "summary":
            path = str(arguments.get("path", "")).strip()
            if not path:
                return "Nenhum caminho de nota fornecido para resumo."
            words = str(arguments.get("words", 200))
            return self._run_hub("summary", path, "--words", words)

        if action in {"brain_search", "brain-query", "brain"}:
            query = str(arguments.get("query", "")).strip()
            if not query:
                return "Nenhuma query fornecida para o brain."
            mode = str(arguments.get("mode", "hybrid"))
            return self._run_hub("brain-query", query, "--mode", mode, "--limit", limit, "--json")

        if action == "doctor":
            return self._run_hub("doctor", "--json")

        if action == "checkpoint":
            summary = str(arguments.get("summary", "")).strip()
            if not summary:
                return "Nenhum resumo fornecido para checkpoint."
            return self._run_hub("checkpoint", "--summary", summary)

        return (
            "Acao nao suportada. Use uma das seguintes: bootstrap, search, related, recent, "
            "summary, brain_search, doctor ou checkpoint."
        )
