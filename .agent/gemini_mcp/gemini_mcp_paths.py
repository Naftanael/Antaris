from __future__ import annotations

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
AGENT_DIR = REPO_ROOT / ".agent"
CANONICAL_TEMPLATE_PATH = AGENT_DIR / "gemini_mcp" / "mcp_config.template.json"
LEGACY_TEMPLATE_PATH = AGENT_DIR / "mcp_config.json"
DEFAULT_OUTPUT = Path.home() / ".gemini" / "antigravity" / "mcp_config.json"


def get_template_path() -> Path:
    if CANONICAL_TEMPLATE_PATH.exists():
        return CANONICAL_TEMPLATE_PATH
    return LEGACY_TEMPLATE_PATH
