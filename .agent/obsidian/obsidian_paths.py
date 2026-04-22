from __future__ import annotations

import os
from pathlib import Path

DEFAULT_VAULT_FALLBACK = "/home/antaris/Documentos/Antaris"

IGNORE_DIRS = {
    ".obsidian",
    ".git",
    ".venv",
    ".smart-env",
    ".space",
    ".makemd",
    "__pycache__",
    "Sem título",
    "Tags",
    ".agent",
    "copilot",
    "node_modules",
    "dist",
    "build",
}


def get_vault_path() -> Path:
    return Path(os.environ.get("OBSIDIAN_VAULT_PATH", DEFAULT_VAULT_FALLBACK)).expanduser()


def get_agent_paths(vault: Path | None = None) -> dict[str, Path]:
    resolved_vault = vault or get_vault_path()
    agent_dir = resolved_vault / ".agent"
    return {
        "vault": resolved_vault,
        "agent": agent_dir,
        "scripts": agent_dir / "scripts",
        "memory": agent_dir / "memory",
        "manifest": agent_dir / "context-manifest.md",
        "index": agent_dir / "vault-index.json",
    }


def resolve_note_path(path_arg: str, vault: Path | None = None) -> Path:
    candidate = Path(path_arg)
    if candidate.is_absolute():
        return candidate
    return (vault or get_vault_path()) / path_arg
