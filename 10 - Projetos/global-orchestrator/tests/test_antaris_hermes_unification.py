from __future__ import annotations

import importlib.util
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch


REPO_ROOT = Path(__file__).resolve().parents[3]
MODULE_PATH = REPO_ROOT / ".agent" / "hermes" / "hermes_unification.py"
SPEC = importlib.util.spec_from_file_location("antaris_hermes_unification", MODULE_PATH)
if SPEC is None or SPEC.loader is None:
    raise RuntimeError(f"failed to load module from {MODULE_PATH}")
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


class AntarisHermesUnificationTests(unittest.TestCase):
    def test_ensure_hermes_config_text_adds_antaris_runtime_settings(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            hermes_home = Path(tmp)
            config_text = "display:\n  compact: false\n"

            updated = MODULE.ensure_hermes_config_text(config_text, hermes_home=hermes_home)

            self.assertIn("display:\n  compact: false\n  skin: antaris\n", updated)
            self.assertIn(f"prefill_messages_file: {hermes_home / 'antaris_prefill.jsonl'}", updated)
            self.assertIn(f"  - {REPO_ROOT / '.agent' / 'skills'}", updated)
            self.assertIn(f"  - {REPO_ROOT / '.agent' / 'workflows'}", updated)

    def test_ensure_hermes_config_text_preserves_existing_values_and_merges_dirs(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            hermes_home = Path(tmp)
            custom_dir = "/tmp/custom-skills"
            config_text = (
                "display:\n"
                "  compact: false\n"
                "  personality: technical\n"
                "skills:\n"
                "  timeout: 10\n"
                "  external_dirs:\n"
                f"  - {custom_dir}\n"
                f"  - {REPO_ROOT / '.agent' / 'skills'}\n"
                "prefill_messages_file: /tmp/old-prefill.jsonl\n"
            )

            updated = MODULE.ensure_hermes_config_text(config_text, hermes_home=hermes_home)

            self.assertIn("  compact: false", updated)
            self.assertIn("  personality: technical", updated)
            self.assertIn("  timeout: 10", updated)
            self.assertIn(f"  - {custom_dir}", updated)
            self.assertIn(f"prefill_messages_file: {hermes_home / 'antaris_prefill.jsonl'}", updated)
            self.assertEqual(updated.count(f"  - {REPO_ROOT / '.agent' / 'skills'}"), 1)
            self.assertEqual(updated.count(f"  - {REPO_ROOT / '.agent' / 'workflows'}"), 1)

    def test_configure_hermes_runtime_writes_config_file(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            hermes_home = Path(tmp)

            result = MODULE.configure_hermes_runtime(hermes_home)

            config_path = hermes_home / "config.yaml"
            self.assertEqual(result["status"], "ok")
            self.assertTrue(config_path.exists())
            config_text = config_path.read_text(encoding="utf-8")
            self.assertIn("  skin: antaris", config_text)
            self.assertIn(f"prefill_messages_file: {hermes_home / 'antaris_prefill.jsonl'}", config_text)
            self.assertIn(f"  - {REPO_ROOT / '.agent' / 'skills'}", config_text)
            self.assertIn(f"  - {REPO_ROOT / '.agent' / 'workflows'}", config_text)

    def test_is_usable_executable_rejects_stale_shebang(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            broken_script = root / "broken-hermes"
            broken_script.write_text("#!/does/not/exist/python3\nprint('x')\n", encoding="utf-8")
            broken_script.chmod(0o755)

            self.assertFalse(MODULE.is_usable_executable(broken_script))

    def test_resolve_hermes_binary_supports_antaris_agent_venv_layout(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            local_bin = root / ".local" / "bin" / "hermes"
            antaris_agent_venv_bin = root / ".hermes" / "antaris-agent" / "venv" / "bin" / "hermes"
            antaris_agent_bin = root / ".hermes" / "antaris-agent" / "hermes"
            legacy_bin = root / ".hermes" / "hermes-agent" / "venv" / "bin" / "hermes"
            antaris_agent_venv_bin.parent.mkdir(parents=True, exist_ok=True)
            antaris_agent_venv_bin.write_text("#!/usr/bin/env bash\nexit 0\n", encoding="utf-8")
            antaris_agent_venv_bin.chmod(0o755)
            antaris_agent_bin.parent.mkdir(parents=True, exist_ok=True)
            antaris_agent_bin.write_text("#!/usr/bin/env bash\nexit 0\n", encoding="utf-8")
            antaris_agent_bin.chmod(0o755)

            with patch("shutil.which", return_value=None):
                with patch.object(MODULE, "DEFAULT_LOCAL_HERMES_BIN", local_bin):
                    with patch.object(MODULE, "DEFAULT_ANTARIS_AGENT_VENV_BIN", antaris_agent_venv_bin):
                        with patch.object(MODULE, "DEFAULT_ANTARIS_AGENT_BIN", antaris_agent_bin):
                            with patch.object(MODULE, "DEFAULT_LEGACY_HERMES_AGENT_BIN", legacy_bin):
                                resolved = MODULE.resolve_hermes_binary()

            self.assertEqual(resolved, antaris_agent_venv_bin)
            self.assertTrue(os.access(resolved, os.X_OK))

    def test_repair_local_hermes_symlink_repoints_broken_link(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            local_bin = root / ".local" / "bin" / "hermes"
            broken_target = root / ".hermes" / "hermes-agent" / "venv" / "bin" / "hermes"
            antaris_agent_bin = root / ".hermes" / "antaris-agent" / "hermes"
            legacy_bin = root / ".hermes" / "hermes-agent" / "venv" / "bin" / "hermes"

            local_bin.parent.mkdir(parents=True, exist_ok=True)
            antaris_agent_venv_bin = root / ".hermes" / "antaris-agent" / "venv" / "bin" / "hermes"
            antaris_agent_venv_bin.parent.mkdir(parents=True, exist_ok=True)
            antaris_agent_venv_bin.write_text("#!/usr/bin/env bash\nexit 0\n", encoding="utf-8")
            antaris_agent_venv_bin.chmod(0o755)
            antaris_agent_bin.parent.mkdir(parents=True, exist_ok=True)
            antaris_agent_bin.write_text("#!/usr/bin/env bash\nexit 0\n", encoding="utf-8")
            antaris_agent_bin.chmod(0o755)
            local_bin.symlink_to(broken_target)

            with patch("shutil.which", return_value=None):
                with patch.object(MODULE, "DEFAULT_LOCAL_HERMES_BIN", local_bin):
                    with patch.object(MODULE, "DEFAULT_ANTARIS_AGENT_VENV_BIN", antaris_agent_venv_bin):
                        with patch.object(MODULE, "DEFAULT_ANTARIS_AGENT_BIN", antaris_agent_bin):
                            with patch.object(MODULE, "DEFAULT_LEGACY_HERMES_AGENT_BIN", legacy_bin):
                                result = MODULE.repair_local_hermes_symlink()

            self.assertEqual(result["status"], "ok")
            self.assertTrue(local_bin.is_symlink())
            self.assertEqual(local_bin.resolve(strict=True), antaris_agent_venv_bin)


if __name__ == "__main__":
    unittest.main()
