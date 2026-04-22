from __future__ import annotations

import re
import subprocess
from pathlib import Path
from typing import Any, Dict

from core.base_skill import BaseSkill
from core.debug.events import EventLevel


class JarvisFrontendSkill(BaseSkill):
    @property
    def name(self) -> str:
        return "jarvis_frontend_skill"

    @property
    def description(self) -> str:
        return (
            "Gera e valida paginas frontend do projeto Jarvis usando pipeline deterministico "
            "(generate-page, review-page e test-page com Playwright + axe)."
        )

    @property
    def repo_root(self) -> Path:
        return Path(__file__).resolve().parents[3]

    @property
    def jarvis_dir(self) -> Path:
        return self.repo_root / "10 - Projetos" / "jarvis"

    def _run_npm(self, *npm_args: str) -> Dict[str, Any]:
        command = ["npm", *npm_args]
        self.trace_event(
            "skill_execution_started",
            level=EventLevel.INFO,
            payload={
                "skill_name": self.name,
                "command": command,
                "cwd": str(self.jarvis_dir),
            },
        )

        completed = subprocess.run(
            command,
            cwd=self.jarvis_dir,
            capture_output=True,
            text=True,
        )

        payload = {
            "returncode": completed.returncode,
            "stdout": completed.stdout.strip(),
            "stderr": completed.stderr.strip(),
        }

        event_level = EventLevel.INFO if completed.returncode == 0 else EventLevel.ERROR
        self.trace_event(
            "skill_execution_finished",
            level=event_level,
            payload={
                "skill_name": self.name,
                "returncode": completed.returncode,
                "stdout_length": len(completed.stdout or ""),
                "stderr_length": len(completed.stderr or ""),
            },
        )
        return payload

    def _ensure_jarvis_dependencies(self) -> Dict[str, Any] | None:
        node_modules = self.jarvis_dir / "node_modules"
        if node_modules.exists():
            return None

        install_result = self._run_npm("install")
        if install_result["returncode"] != 0:
            return {
                "status": "error",
                "error": "Falha ao instalar dependencias do Jarvis.",
                "details": install_result,
            }
        return None

    def _extract_artifact_dir(self, stdout: str) -> str | None:
        match = re.search(r"Artifacts saved at:\s*(.+)", stdout)
        if not match:
            return None
        return match.group(1).strip()

    def _extract_preview_url(self, stdout: str) -> str | None:
        match = re.search(r"Preview URL:\s*(.+)", stdout)
        if not match:
            return None
        return match.group(1).strip()

    def _extract_page_id(self, stdout: str) -> str | None:
        match = re.search(r"Page ID:\s*(.+)", stdout)
        if not match:
            return None
        return match.group(1).strip()

    def _resolve_page_path(self, arguments: Dict[str, Any]) -> str | None:
        page_path = str(arguments.get("page_path", arguments.get("page", ""))).strip()
        artifact_dir = str(arguments.get("artifact_dir", "")).strip()
        if page_path:
            return page_path
        if artifact_dir:
            return str(Path(artifact_dir) / "generated-page.tsx")
        return None

    def _resolve_output_path(self, arguments: Dict[str, Any], default_name: str) -> str | None:
        out = str(arguments.get("out", "")).strip()
        if out:
            return out
        artifact_dir = str(arguments.get("artifact_dir", "")).strip()
        if artifact_dir:
            return str(Path(artifact_dir) / default_name)
        return None

    def _action_generate(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        prompt = str(
            arguments.get("prompt")
            or arguments.get("page_type")
            or arguments.get("description")
            or arguments.get("request")
            or arguments.get("query")
            or ""
        ).strip()
        if not prompt:
            return {
                "status": "error",
                "error": "Para gerar pagina, informe 'prompt'.",
            }

        command = ["run", "generate-page", "--", "--prompt", prompt]
        style_preset = str(arguments.get("style_preset", "")).strip()
        out_dir = str(arguments.get("out_dir", "")).strip()

        if style_preset:
            command.extend(["--style-preset", style_preset])
        if out_dir:
            command.extend(["--out-dir", out_dir])

        result = self._run_npm(*command)
        if result["returncode"] != 0:
            return {
                "status": "error",
                "error": "Falha ao executar generate-page.",
                "details": result,
            }

        stdout = result["stdout"]
        return {
            "status": "success",
            "action": "generate",
            "artifact_dir": self._extract_artifact_dir(stdout),
            "preview_url": self._extract_preview_url(stdout),
            "page_id": self._extract_page_id(stdout),
            "details": result,
        }

    def _action_review(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        page_path = self._resolve_page_path(arguments)
        if not page_path:
            return {
                "status": "error",
                "error": "Para review, informe 'page_path' ou 'artifact_dir'.",
            }

        command = ["run", "review-page", "--", "--page", page_path]
        url = str(arguments.get("url", "")).strip()
        if url:
            command.extend(["--url", url])

        out_path = self._resolve_output_path(arguments, "review-report.json")
        if out_path:
            command.extend(["--out", out_path])

        strict_snapshots = bool(arguments.get("strict_snapshots", False))
        if strict_snapshots:
            command.append("--strict-snapshots")

        result = self._run_npm(*command)
        if result["returncode"] != 0:
            return {
                "status": "error",
                "error": "Falha ao executar review-page.",
                "details": result,
            }

        return {
            "status": "success",
            "action": "review",
            "report_path": out_path,
            "details": result,
        }

    def _action_test(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        page_path = self._resolve_page_path(arguments)
        if not page_path:
            return {
                "status": "error",
                "error": "Para test, informe 'page_path' ou 'artifact_dir'.",
            }

        command = ["run", "test-page", "--", "--page", page_path]
        url = str(arguments.get("url", "")).strip()
        if url:
            command.extend(["--url", url])

        out_path = self._resolve_output_path(arguments, "visual-test-report.json")
        if out_path:
            command.extend(["--out", out_path])

        if bool(arguments.get("update_baseline", False)):
            command.append("--update-baseline")

        if bool(arguments.get("allow_missing_baseline", False)):
            command.append("--allow-missing-baseline")

        result = self._run_npm(*command)
        if result["returncode"] != 0:
            return {
                "status": "error",
                "error": "Falha ao executar test-page.",
                "details": result,
            }

        return {
            "status": "success",
            "action": "test",
            "report_path": out_path,
            "details": result,
        }

    def _action_build_registry(self) -> Dict[str, Any]:
        result = self._run_npm("run", "build-registry")
        if result["returncode"] != 0:
            return {
                "status": "error",
                "error": "Falha ao executar build-registry.",
                "details": result,
            }

        return {
            "status": "success",
            "action": "build_registry",
            "details": result,
        }

    def _action_pipeline(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        generation = self._action_generate(arguments)
        if generation.get("status") != "success":
            return generation

        artifact_dir = generation.get("artifact_dir")
        if not artifact_dir:
            return {
                "status": "error",
                "error": "Nao foi possivel identificar artifact_dir apos generate-page.",
                "details": generation,
            }

        page_path = str(Path(artifact_dir) / "generated-page.tsx")
        preview_url = generation.get("preview_url")

        review_result = self._action_review(
            {
                **arguments,
                "page_path": page_path,
                "artifact_dir": artifact_dir,
                "url": preview_url,
            }
        )

        test_result = self._action_test(
            {
                **arguments,
                "page_path": page_path,
                "artifact_dir": artifact_dir,
                "url": preview_url,
                "allow_missing_baseline": arguments.get("allow_missing_baseline", True),
            }
        )

        status = "success" if review_result.get("status") == "success" and test_result.get("status") == "success" else "error"
        return {
            "status": status,
            "action": "pipeline",
            "artifact_dir": artifact_dir,
            "preview_url": preview_url,
            "generate": generation,
            "review": review_result,
            "test": test_result,
        }

    def execute(self, arguments: Dict[str, Any]) -> Any:
        if not self.jarvis_dir.exists():
            return {
                "status": "error",
                "error": f"Diretorio Jarvis nao encontrado: {self.jarvis_dir}",
            }

        dependency_error = self._ensure_jarvis_dependencies()
        if dependency_error is not None:
            return dependency_error

        raw_action = str(arguments.get("action", "pipeline")).strip().lower()
        action = raw_action.replace(" ", "_")
        aliases = {
            "generate-page": "generate",
            "generate_page": "generate",
            "create-page": "generate",
            "create_page": "generate",
            "gerar-pagina": "generate",
            "gerar_pagina": "generate",
            "review-page": "review",
            "review_page": "review",
            "revisar-pagina": "review",
            "revisar_pagina": "review",
            "test-page": "test",
            "test_page": "test",
            "visual_test": "test",
            "playwright": "test",
            "axe": "test",
            "build-registry": "build_registry",
            "pipeline_completo": "pipeline",
        }
        action = aliases.get(action, action)

        if action in {"generate", "gen", "gerar", "criar"}:
            return self._action_generate(arguments)

        if action in {"review", "rev", "revisar", "avaliar"}:
            return self._action_review(arguments)

        if action in {"test", "visual-test", "validate", "testar", "validar"}:
            return self._action_test(arguments)

        if action in {"build_registry", "registry", "registro"}:
            return self._action_build_registry()

        if action in {"pipeline", "full", "run", "completo", "completa"}:
            return self._action_pipeline(arguments)

        return {
            "status": "error",
            "error": "Acao nao suportada. Use: pipeline, generate, review, test ou build_registry.",
        }
