#!/usr/bin/env python3
"""
Generate the Hermes prefill context file.

This script produces a lightweight JSONL file that Hermes reads at session start,
injecting Antaris context automatically — no manual bootstrap needed.

Usage:
    python3 generate_prefill.py [--output PATH]

Default output: ~/.hermes/antaris_prefill.jsonl
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
AGENT_DIR = REPO_ROOT / ".agent"
MEMORY_DIR = AGENT_DIR / "memory"
HERMES_HOME = Path.home() / ".hermes"
DEFAULT_OUTPUT = HERMES_HOME / "antaris_prefill.jsonl"


def read_text(path: Path, max_chars: int = 2000) -> str:
    if not path.exists():
        return ""
    text = path.read_text(encoding="utf-8").strip()
    if len(text) > max_chars:
        text = text[:max_chars] + "\n[...truncado]"
    return text


def build_context() -> str:
    """Build a compact context string from vault memory files."""
    sections = []

    # Identity
    sections.append(
        "Voce e Antaris, operando sobre o Hermes runtime. "
        "Vault Obsidian: /home/antaris/Documentos/Antaris. "
        "Responda em pt-BR, seja direto."
    )

    # Project state
    project_state = read_text(MEMORY_DIR / "project-state.md", max_chars=1200)
    if project_state:
        sections.append(f"## Estado dos Projetos\n{project_state}")

    # Lessons learned
    lessons = read_text(MEMORY_DIR / "lessons-learned.md", max_chars=800)
    if lessons:
        sections.append(f"## Aprendizados\n{lessons}")

    # Recent session log (last 500 chars)
    session_log = read_text(MEMORY_DIR / "session-log.md", max_chars=500)
    if session_log:
        # Get the tail
        lines = session_log.split("\n")
        tail = "\n".join(lines[-15:])
        sections.append(f"## Ultimas sessoes\n{tail}")

    # Tools hint
    sections.append(
        "## Ferramentas disponíveis\n"
        "- `antigravity_hub.py bootstrap` - contexto completo\n"
        "- `antigravity_hub.py brain-query \"...\" --mode hybrid` - busca semantica\n"
        "- `antigravity_hub.py search \"...\"` - busca no vault\n"
        "- `antigravity_hub.py checkpoint --summary \"...\"` - salvar sessao\n"
        "- `antigravity_hub.py doctor` - health check"
    )

    return "\n\n".join(sections)


def main() -> None:
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("--output", default=str(DEFAULT_OUTPUT))
    args = parser.parse_args()

    output_path = Path(args.output)
    context = build_context()

    # Hermes prefill format: one JSON object per line with role/content
    messages = [
        {"role": "system", "content": context},
    ]

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        for msg in messages:
            f.write(json.dumps(msg, ensure_ascii=False) + "\n")

    token_estimate = len(context) // 4
    print(f"[OK] Prefill gerado: {output_path}")
    print(f"[OK] Estimativa: ~{token_estimate} tokens")


if __name__ == "__main__":
    main()
