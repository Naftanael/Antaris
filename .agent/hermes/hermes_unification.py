from __future__ import annotations
import sys

import argparse
import json
import os
import re
import shutil
import subprocess
from pathlib import Path
from typing import Callable

REPO_ROOT = Path(__file__).resolve().parents[2]
AGENT_DIR = REPO_ROOT / ".agent"
HERMES_DIR = AGENT_DIR / "hermes"
DEFAULT_HERMES_HOME = Path(os.environ.get("HERMES_HOME", Path.home() / ".hermes")).expanduser()
DEFAULT_ANTARIS_SKIN_NAME = "antaris"
DEFAULT_ANTARIS_BIN = Path.home() / ".local" / "bin" / "antaris"
DEFAULT_PREFILL_PATH = DEFAULT_HERMES_HOME / "antaris_prefill.jsonl"


def print_json(payload: object) -> None:
    print(json.dumps(payload, indent=2, ensure_ascii=False))


def resolve_hermes_binary() -> Path | None:
    candidates = [
        shutil.which("hermes"),
        str(Path.home() / ".local" / "bin" / "hermes"),
    ]
    for candidate in candidates:
        if not candidate:
            continue
        path = Path(candidate).expanduser()
        if path.exists():
            return path
    return None


def get_hermes_paths(hermes_home: Path | None = None) -> dict[str, Path]:
    home = (hermes_home or DEFAULT_HERMES_HOME).expanduser()
    return {
        "home": home,
        "config": home / "config.yaml",
        "soul": home / "SOUL.md",
        "skins_dir": home / "skins",
        "skin": home / "skins" / f"{DEFAULT_ANTARIS_SKIN_NAME}.yaml",
    }


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8") if path.exists() else ""


def install_antaris_skin(hermes_home: Path | None = None) -> Path:
    paths = get_hermes_paths(hermes_home)
    source = HERMES_DIR / "antaris-skin.yaml"
    if not source.exists():
        raise FileNotFoundError(f"skin template not found: {source}")
    paths["skins_dir"].mkdir(parents=True, exist_ok=True)
    paths["skin"].write_text(source.read_text(encoding="utf-8"), encoding="utf-8")
    return paths["skin"]


def install_antaris_soul(hermes_home: Path | None = None) -> dict[str, str]:
    paths = get_hermes_paths(hermes_home)
    source = HERMES_DIR / "ANTARIS_SOUL.md"
    if not source.exists():
        raise FileNotFoundError(f"SOUL template not found: {source}")

    current = read_text(paths["soul"])
    target = source.read_text(encoding="utf-8")
    backup_path = paths["home"] / "SOUL.md.pre-antaris.bak"
    backup_written = False

    paths["home"].mkdir(parents=True, exist_ok=True)
    if current and current != target and not backup_path.exists():
        backup_path.write_text(current, encoding="utf-8")
        backup_written = True

    paths["soul"].write_text(target, encoding="utf-8")
    return {
        "soul_path": str(paths["soul"]),
        "backup_path": str(backup_path) if backup_written else "",
    }


def install_antaris_launcher(bin_path: Path | None = None) -> Path:
    target = (bin_path or DEFAULT_ANTARIS_BIN).expanduser()
    template = HERMES_DIR / "antaris-launcher.sh"
    if not template.exists():
        raise FileNotFoundError(f"launcher template not found: {template}")

    content = template.read_text(encoding="utf-8").replace("__ANTARIS_VAULT_ROOT__", str(REPO_ROOT))
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(content, encoding="utf-8")
    target.chmod(0o755)
    return target


def set_hermes_skin(skin_name: str = DEFAULT_ANTARIS_SKIN_NAME) -> dict[str, str]:
    hermes_bin = resolve_hermes_binary()
    if hermes_bin is None:
        return {
            "status": "warn",
            "details": "Hermes binary not found; skin file was installed but config was not updated.",
        }

    completed = subprocess.run(
        [str(hermes_bin), "config", "set", "display.skin", skin_name],
        capture_output=True,
        text=True,
    )
    if completed.returncode == 0:
        return {
            "status": "ok",
            "details": completed.stdout.strip() or f"display.skin -> {skin_name}",
        }

    details = completed.stderr.strip() or completed.stdout.strip() or "unknown error"
    return {
        "status": "warn",
        "details": f"failed to update Hermes config automatically: {details}",
    }


def configured_skin_name(config_text: str) -> str:
    match = re.search(r"(?m)^\s*skin:\s*([^\s#]+)", config_text)
    if not match:
        return ""
    return match.group(1).strip().strip("'\"")


def generate_prefill(output_path: Path | None = None) -> Path:
    """Generate the session prefill JSONL from vault memory."""
    script = HERMES_DIR / "generate_prefill.py"
    if not script.exists():
        raise FileNotFoundError(f"prefill generator not found: {script}")
    target = output_path or DEFAULT_PREFILL_PATH
    completed = subprocess.run(
        [sys.executable, str(script), "--output", str(target)],
        capture_output=True,
        text=True,
        cwd=REPO_ROOT,
    )
    if completed.returncode != 0:
        raise RuntimeError(f"prefill generation failed: {completed.stderr}")
    return target


def unify_hermes(json_mode: bool = False) -> int:
    skin_path = install_antaris_skin()
    soul_info = install_antaris_soul()
    launcher_path = install_antaris_launcher()
    config_result = set_hermes_skin(DEFAULT_ANTARIS_SKIN_NAME)
    prefill_path = generate_prefill()
    payload = {
        "ok": True,
        "skin_path": str(skin_path),
        "soul_path": soul_info["soul_path"],
        "soul_backup_path": soul_info["backup_path"],
        "launcher_path": str(launcher_path),
        "prefill_path": str(prefill_path),
        "config": config_result,
        "launch_hint": "antaris",
    }
    if json_mode:
        print_json(payload)
    else:
        print(f"[OK] Skin instalada em {skin_path}")
        print(f"[OK] SOUL aplicada em {soul_info['soul_path']}")
        print(f"[OK] Launcher instalado em {launcher_path}")
        print(f"[OK] Prefill gerado em {prefill_path}")
        if soul_info["backup_path"]:
            print(f"[OK] Backup da SOUL anterior salvo em {soul_info['backup_path']}")
        marker = "OK" if config_result["status"] == "ok" else "WARN"
        print(f"[{marker}] Hermes config: {config_result['details']}")
        print(f"[OK] Launcher recomendado: {payload['launch_hint']}")
    return 0


def install_launcher_cli(json_mode: bool = False) -> int:
    launcher_path = install_antaris_launcher()
    payload = {"ok": True, "launcher_path": str(launcher_path)}
    if json_mode:
        print_json(payload)
    else:
        print(f"[OK] Launcher instalado em {launcher_path}")
        print("[OK] Use `antaris` para iniciar o Hermes no contexto do vault.")
    return 0


def launch_hermes(extra_args: list[str]) -> int:
    hermes_bin = resolve_hermes_binary()
    if hermes_bin is None:
        print("Hermes binary not found in PATH or ~/.local/bin/hermes", file=os.sys.stderr)
        return 1

    env = os.environ.copy()
    env.setdefault("OBSIDIAN_VAULT_PATH", str(REPO_ROOT))
    command = [str(hermes_bin), *extra_args]
    completed = subprocess.run(command, cwd=REPO_ROOT, env=env)
    return completed.returncode


def generate_prefill_cli(json_mode: bool = False) -> int:
    prefill_path = generate_prefill()
    payload = {"ok": True, "prefill_path": str(prefill_path)}
    if json_mode:
        print_json(payload)
    else:
        print(f"[OK] Prefill gerado em {prefill_path}")
    return 0


def register_cli(subparsers: argparse._SubParsersAction) -> None:
    unify_parser = subparsers.add_parser(
        "unify-hermes",
        help="Install Antaris branding and identity into the local Hermes home.",
    )
    unify_parser.add_argument("--json", action="store_true")

    launcher_parser = subparsers.add_parser(
        "install-launcher",
        help="Install the antaris launcher into ~/.local/bin.",
    )
    launcher_parser.add_argument("--json", action="store_true")

    prefill_parser = subparsers.add_parser(
        "generate-prefill",
        help="Regenerate the session prefill context from vault memory.",
    )
    prefill_parser.add_argument("--json", action="store_true")

    launch_parser = subparsers.add_parser(
        "launch-hermes",
        help="Launch Hermes with OBSIDIAN_VAULT_PATH pointed at this Antaris vault.",
    )
    launch_parser.add_argument("hermes_args", nargs=argparse.REMAINDER)


def handle_cli(command: str, args: argparse.Namespace) -> int | None:
    if command == "unify-hermes":
        return unify_hermes(args.json)
    if command == "install-launcher":
        return install_launcher_cli(args.json)
    if command == "generate-prefill":
        return generate_prefill_cli(args.json)
    if command == "launch-hermes":
        return launch_hermes(args.hermes_args)
    return None


def extend_doctor_checks(add_check: Callable[[str, str, str], None]) -> set[str]:
    hermes_bin = resolve_hermes_binary()
    add_check("hermes-binary", "ok" if hermes_bin else "warn", str(hermes_bin) if hermes_bin else "nao encontrado")

    hermes_paths = get_hermes_paths()
    add_check("hermes-home", "ok" if hermes_paths["home"].exists() else "warn", str(hermes_paths["home"]))
    add_check("hermes-skin-template", "ok" if (HERMES_DIR / "antaris-skin.yaml").exists() else "warn", str(HERMES_DIR / "antaris-skin.yaml"))
    add_check("hermes-soul-template", "ok" if (HERMES_DIR / "ANTARIS_SOUL.md").exists() else "warn", str(HERMES_DIR / "ANTARIS_SOUL.md"))
    add_check("hermes-launcher-template", "ok" if (HERMES_DIR / "antaris-launcher.sh").exists() else "warn", str(HERMES_DIR / "antaris-launcher.sh"))
    add_check("hermes-docs", "ok" if (HERMES_DIR / "README.md").exists() else "warn", str(HERMES_DIR / "README.md"))
    add_check("hermes-module", "ok" if (HERMES_DIR / "hermes_unification.py").exists() else "warn", str(HERMES_DIR / "hermes_unification.py"))
    add_check("hermes-skin-installed", "ok" if hermes_paths["skin"].exists() else "warn", str(hermes_paths["skin"]))
    add_check("antaris-launcher", "ok" if DEFAULT_ANTARIS_BIN.exists() else "warn", str(DEFAULT_ANTARIS_BIN))
    add_check("hermes-prefill", "ok" if DEFAULT_PREFILL_PATH.exists() else "warn", str(DEFAULT_PREFILL_PATH))
    add_check("hermes-prefill-generator", "ok" if (HERMES_DIR / "generate_prefill.py").exists() else "warn", str(HERMES_DIR / "generate_prefill.py"))

    config_text = read_text(hermes_paths["config"])
    active_skin = configured_skin_name(config_text)
    add_check(
        "hermes-active-skin",
        "ok" if active_skin == DEFAULT_ANTARIS_SKIN_NAME else "warn",
        active_skin or "nao configurado",
    )

    soul_text = read_text(hermes_paths["soul"])
    add_check(
        "hermes-soul",
        "ok" if "You are Antaris operating on top of the Hermes Agent runtime." in soul_text else "warn",
        str(hermes_paths["soul"]),
    )

    # Check external_dirs config
    external_dirs_ok = "external_dirs" in config_text and "/Antaris/.agent/skills" in config_text
    add_check(
        "hermes-external-skills",
        "ok" if external_dirs_ok else "warn",
        "Antigravity skills linkados" if external_dirs_ok else "external_dirs nao configurado",
    )

    return {
        "hermes-skin-template",
        "hermes-soul-template",
        "hermes-launcher-template",
        "hermes-docs",
        "hermes-module",
        "hermes-skin-installed",
        "antaris-launcher",
        "hermes-active-skin",
        "hermes-soul",
        "hermes-prefill",
        "hermes-prefill-generator",
        "hermes-external-skills",
    }
