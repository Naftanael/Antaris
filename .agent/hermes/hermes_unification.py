from __future__ import annotations
import sys

import argparse
import json
import os
import re
import shutil
import subprocess
from pathlib import Path
from typing import Callable, Sequence

REPO_ROOT = Path(__file__).resolve().parents[2]
AGENT_DIR = REPO_ROOT / ".agent"
HERMES_DIR = AGENT_DIR / "hermes"
DEFAULT_HERMES_HOME = Path(os.environ.get("HERMES_HOME", Path.home() / ".hermes")).expanduser()
DEFAULT_ANTARIS_SKIN_NAME = "antaris"
DEFAULT_ANTARIS_BIN = Path.home() / ".local" / "bin" / "antaris"
DEFAULT_LOCAL_HERMES_BIN = Path.home() / ".local" / "bin" / "hermes"
DEFAULT_ANTARIS_AGENT_VENV_BIN = DEFAULT_HERMES_HOME / "antaris-agent" / "venv" / "bin" / "hermes"
DEFAULT_ANTARIS_AGENT_BIN = DEFAULT_HERMES_HOME / "antaris-agent" / "hermes"
DEFAULT_LEGACY_HERMES_AGENT_BIN = DEFAULT_HERMES_HOME / "hermes-agent" / "venv" / "bin" / "hermes"
DEFAULT_PREFILL_FILENAME = "antaris_prefill.jsonl"
DEFAULT_PREFILL_PATH = DEFAULT_HERMES_HOME / DEFAULT_PREFILL_FILENAME
DEFAULT_EXTERNAL_DIRS = [
    REPO_ROOT / ".agent" / "skills",
    REPO_ROOT / ".agent" / "workflows",
]


def print_json(payload: object) -> None:
    print(json.dumps(payload, indent=2, ensure_ascii=False))


def get_script_interpreter(path: Path) -> Path | None:
    try:
        with path.open("r", encoding="utf-8", errors="ignore") as handle:
            first_line = handle.readline().strip()
    except OSError:
        return None
    if not first_line.startswith("#!"):
        return None
    parts = first_line[2:].strip().split()
    if not parts:
        return None
    interpreter = parts[0]
    if interpreter == "/usr/bin/env":
        return Path(interpreter)
    if os.path.isabs(interpreter):
        return Path(interpreter)
    return None


def is_usable_executable(path: Path) -> bool:
    if not (path.exists() and path.is_file() and os.access(path, os.X_OK)):
        return False
    interpreter = get_script_interpreter(path)
    return interpreter.exists() if interpreter is not None else True


def iter_hermes_binary_candidates(include_local_bin: bool = True) -> list[Path]:
    candidates: list[Path] = []
    candidates.extend([
        DEFAULT_ANTARIS_AGENT_VENV_BIN,
        DEFAULT_ANTARIS_AGENT_BIN,
        DEFAULT_LEGACY_HERMES_AGENT_BIN,
    ])
    if include_local_bin:
        candidates.append(DEFAULT_LOCAL_HERMES_BIN)
    from_shell = shutil.which("hermes")
    if from_shell:
        candidates.append(Path(from_shell).expanduser())
    return candidates


def resolve_hermes_binary(include_local_bin: bool = True) -> Path | None:
    seen: set[Path] = set()
    for path in iter_hermes_binary_candidates(include_local_bin=include_local_bin):
        if path in seen:
            continue
        seen.add(path)
        if is_usable_executable(path):
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


def get_prefill_path(hermes_home: Path | None = None) -> Path:
    home = (hermes_home or DEFAULT_HERMES_HOME).expanduser()
    return home / DEFAULT_PREFILL_FILENAME


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


def repair_local_hermes_symlink() -> dict[str, str]:
    runtime_bin = resolve_hermes_binary(include_local_bin=False)
    if runtime_bin is None:
        return {
            "status": "warn",
            "details": "nenhum binario Hermes/Antaris executavel foi encontrado para linkar em ~/.local/bin/hermes.",
        }

    target = DEFAULT_LOCAL_HERMES_BIN
    target.parent.mkdir(parents=True, exist_ok=True)

    if target.exists() and not target.is_symlink():
        return {
            "status": "ok",
            "details": f"binario local Hermes ja presente em {target}.",
        }

    if target.is_symlink():
        try:
            current = target.resolve(strict=True)
        except FileNotFoundError:
            current = None
        if current == runtime_bin:
            return {
                "status": "ok",
                "details": f"link local Hermes ja aponta para {runtime_bin}.",
            }
        target.unlink()

    target.symlink_to(runtime_bin)
    return {
        "status": "ok",
        "details": f"link local Hermes reparado: {target} -> {runtime_bin}",
    }


def configured_skin_name(config_text: str) -> str:
    match = re.search(r"(?m)^\s*skin:\s*([^\s#]+)", config_text)
    if not match:
        return ""
    return match.group(1).strip().strip("'\"")


def _split_config_lines(config_text: str) -> list[str]:
    return config_text.splitlines()


def _render_config_lines(lines: Sequence[str]) -> str:
    if not lines:
        return ""
    text = "\n".join(lines).rstrip()
    return f"{text}\n" if text else ""


def _find_top_level_key(lines: Sequence[str], key: str) -> int | None:
    pattern = re.compile(rf"^{re.escape(key)}:(?:\s|$)")
    for index, line in enumerate(lines):
        if line.startswith((" ", "\t")):
            continue
        if pattern.match(line):
            return index
    return None


def _find_top_level_block_end(lines: Sequence[str], start: int) -> int:
    end = start + 1
    while end < len(lines):
        line = lines[end]
        if line and not line.startswith((" ", "\t")):
            break
        end += 1
    return end


def _append_top_level_entry(lines: list[str], new_lines: Sequence[str]) -> None:
    if lines and lines[-1] != "":
        lines.append("")
    lines.extend(new_lines)


def ensure_top_level_scalar(lines: list[str], key: str, value: str) -> None:
    target = f"{key}: {value}"
    index = _find_top_level_key(lines, key)
    if index is not None:
        lines[index] = target
        return
    _append_top_level_entry(lines, [target])


def ensure_nested_scalar(lines: list[str], section: str, key: str, value: str, *, indent: str = "  ") -> None:
    section_index = _find_top_level_key(lines, section)
    if section_index is None:
        _append_top_level_entry(lines, [f"{section}:", f"{indent}{key}: {value}"])
        return

    block_end = _find_top_level_block_end(lines, section_index)
    target = f"{indent}{key}: {value}"
    pattern = re.compile(rf"^{re.escape(indent)}{re.escape(key)}:(?:\s|$)")
    for index in range(section_index + 1, block_end):
        if pattern.match(lines[index]):
            lines[index] = target
            return

    insert_at = block_end
    while insert_at > section_index + 1 and lines[insert_at - 1] == "":
        insert_at -= 1
    lines.insert(insert_at, target)


def ensure_nested_list(
    lines: list[str],
    section: str,
    key: str,
    values: Sequence[str],
    *,
    indent: str = "  ",
) -> None:
    section_index = _find_top_level_key(lines, section)
    if section_index is None:
        _append_top_level_entry(lines, [f"{section}:", f"{indent}{key}:", *[f"{indent}- {value}" for value in values]])
        return

    block_end = _find_top_level_block_end(lines, section_index)
    key_pattern = re.compile(rf"^{re.escape(indent)}{re.escape(key)}:\s*(?:#.*)?$")
    item_pattern = re.compile(rf"^{re.escape(indent)}-\s*(.+?)\s*$")
    key_index: int | None = None
    list_end = block_end
    existing_items: list[str] = []

    for index in range(section_index + 1, block_end):
        if key_pattern.match(lines[index]):
            key_index = index
            list_end = index + 1
            while list_end < block_end:
                line = lines[list_end]
                if not line.strip():
                    break
                item_match = item_pattern.match(line)
                if item_match:
                    existing_items.append(item_match.group(1).strip())
                    list_end += 1
                    continue
                if line.startswith(indent + " "):
                    list_end += 1
                    continue
                break
            break

    merged_items: list[str] = []
    for item in [*existing_items, *values]:
        if item not in merged_items:
            merged_items.append(item)

    new_lines = [f"{indent}{key}:", *[f"{indent}- {item}" for item in merged_items]]
    if key_index is not None:
        lines[key_index:list_end] = new_lines
        return

    insert_at = block_end
    while insert_at > section_index + 1 and lines[insert_at - 1] == "":
        insert_at -= 1
    lines[insert_at:insert_at] = new_lines


def ensure_hermes_config_text(config_text: str, hermes_home: Path | None = None) -> str:
    lines = _split_config_lines(config_text)
    prefill_path = get_prefill_path(hermes_home)
    external_dirs = [str(path) for path in DEFAULT_EXTERNAL_DIRS]

    ensure_nested_scalar(lines, "display", "skin", DEFAULT_ANTARIS_SKIN_NAME)
    ensure_top_level_scalar(lines, "prefill_messages_file", str(prefill_path))
    ensure_nested_list(lines, "skills", "external_dirs", external_dirs)

    return _render_config_lines(lines)


def configure_hermes_runtime(hermes_home: Path | None = None) -> dict[str, str]:
    paths = get_hermes_paths(hermes_home)
    current = read_text(paths["config"])
    target = ensure_hermes_config_text(current, hermes_home=paths["home"])

    paths["home"].mkdir(parents=True, exist_ok=True)
    if current != target:
        paths["config"].write_text(target, encoding="utf-8")
        return {
            "status": "ok",
            "details": "config.yaml atualizado com display.skin, prefill_messages_file e skills.external_dirs.",
        }

    return {
        "status": "ok",
        "details": "config.yaml ja estava alinhado com a identidade Antaris.",
    }


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
    binary_result = repair_local_hermes_symlink()
    config_result = configure_hermes_runtime()
    prefill_path = generate_prefill()
    payload = {
        "ok": True,
        "skin_path": str(skin_path),
        "soul_path": soul_info["soul_path"],
        "soul_backup_path": soul_info["backup_path"],
        "launcher_path": str(launcher_path),
        "prefill_path": str(prefill_path),
        "runtime_binary": binary_result,
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
        binary_marker = "OK" if binary_result["status"] == "ok" else "WARN"
        print(f"[{binary_marker}] Hermes runtime: {binary_result['details']}")
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

    prefill_config_ok = f"prefill_messages_file: {get_prefill_path()}" in config_text
    add_check(
        "hermes-prefill-config",
        "ok" if prefill_config_ok else "warn",
        str(get_prefill_path()) if prefill_config_ok else "prefill_messages_file nao configurado",
    )

    external_dirs_ok = "external_dirs" in config_text and all(str(path) in config_text for path in DEFAULT_EXTERNAL_DIRS)
    add_check(
        "hermes-external-skills",
        "ok" if external_dirs_ok else "warn",
        "Antigravity skills e workflows linkados" if external_dirs_ok else "external_dirs nao configurado por completo",
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
        "hermes-prefill-config",
        "hermes-prefill-generator",
        "hermes-external-skills",
    }
