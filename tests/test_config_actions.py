"""Tests for the reusable ``config`` command group."""

from __future__ import annotations

import contextlib
import io
import json
import unittest
from pathlib import Path

from support_python.cli import ToolHarness
from support_python.config import add_config_actions
from tests.test_config import _SettingsFixture


class ConfigActionsTests(_SettingsFixture):
    def run_cli(self, *argv: str, launcher=None, **env: str) -> tuple[int, str, str]:
        self.environ.update(env)
        harness = ToolHarness("demo", "Demo tool.", version="1.0.0", repo_dir=self.root)
        add_config_actions(harness, self.schema(), launcher=launcher)
        out, err = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            code = harness.run(["config", *argv])
        return code, out.getvalue(), err.getvalue()

    def user_file(self) -> Path:
        return Path(self.environ["XDG_CONFIG_HOME"]) / "demo" / "config.json"

    def test_get_prints_bare_value_and_source_card(self) -> None:
        self.write(self.project_dir / ".demo.json", {"retries": 9})
        code, out, _ = self.run_cli("get", "retries")
        self.assertEqual((code, out.strip()), (0, "9"))
        code, out, _ = self.run_cli("get", "retries", "--source")
        self.assertEqual(code, 0)
        for text in ("9", "project", "integer", "3", "Number of retries."):
            self.assertIn(text, out)

    def test_set_rejects_invalid_value_and_leaves_file_untouched(self) -> None:
        path = self.project_dir / ".demo.json"
        self.write(path, {"retries": 9})
        before = path.read_text(encoding="utf-8")
        code, _, err = self.run_cli("set", "retries", "many")
        self.assertEqual(code, 2)
        self.assertIn("retries", err)
        self.assertEqual(path.read_text(encoding="utf-8"), before)
        self.assertEqual(self.run_cli("set", "nope", "1")[0], 2)
        self.assertEqual(self.run_cli("get", "nope")[0], 2)
        self.assertEqual(self.run_cli("delete", "nope")[0], 2)

    def test_set_and_delete_user_file_use_kebab_case_key(self) -> None:
        self.assertEqual(self.run_cli("set", "verbose-mode", "true", "--user")[0], 0)
        self.assertEqual(json.loads(self.user_file().read_text(encoding="utf-8")), {"verbose-mode": True})
        self.assertEqual(self.run_cli("delete", "verbose-mode", "--user")[0], 0)
        self.assertEqual(json.loads(self.user_file().read_text(encoding="utf-8")), {})

    def test_set_preserves_unrelated_keys_and_delete_touches_only_selected_file(self) -> None:
        project = self.project_dir / ".demo.json"
        self.write(project, {"other": 1, "retries": 4})
        self.write(self.user_file(), {"retries": 2})
        self.assertEqual(self.run_cli("set", "endpoint", "https://x")[0], 0)
        self.assertEqual(json.loads(project.read_text(encoding="utf-8")), {"endpoint": "https://x", "other": 1, "retries": 4})
        self.assertEqual(self.run_cli("delete", "retries")[0], 0)
        self.assertEqual(self.run_cli("get", "retries")[1].strip(), "2")

    def test_list_json_is_one_document_with_masked_secrets(self) -> None:
        self.write(self.project_dir / ".demo.json", {"token": "s3cret"})
        code, out, _ = self.run_cli("list", "--format", "json")
        self.assertEqual(code, 0)
        self.assertNotIn("s3cret", out)
        by_name = {item["name"]: item for item in json.loads(out)["settings"]}
        self.assertEqual(by_name["token"]["value"], "***")
        self.assertEqual(by_name["token"]["source"], "project")
        self.assertEqual(self.run_cli("get", "token")[1].strip(), "***")

    def test_secret_value_is_not_echoed_in_errors_and_config_conflicts_exit_2(self) -> None:
        from support_python.config import Setting, SettingsSchema

        secret = Setting("pin", "integer", None, "PIN.", secret=True)
        schema = SettingsSchema("demo", [secret], project_dir=self.project_dir, environ=self.environ)
        harness = ToolHarness("demo", "Demo tool.", version="1.0.0", repo_dir=self.root)
        add_config_actions(harness, schema)
        err = io.StringIO()
        with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(err):
            self.assertEqual(harness.run(["config", "set", "pin", "hunter2"]), 2)
        self.assertNotIn("hunter2", err.getvalue())
        self.assertEqual(self.run_cli("list", "--config", str(self.root / "c.json"), "--user")[0], 0)
        self.assertEqual(self.run_cli("path", "--config", str(self.root / "c.json"), "--user")[0], 2)

    def test_missing_config_file_warns(self) -> None:
        _, _, err = self.run_cli("list", "--config", str(self.root / "typo.json"))
        self.assertIn("typo.json", err)

    def test_list_is_default_and_verbose_adds_details(self) -> None:
        code, out, _ = self.run_cli()
        self.assertEqual(code, 0)
        self.assertIn("retries", out)
        self.assertNotIn("Number of retries.", out)
        self.assertIn("Number of retries.", self.run_cli("list", "--verbose")[1])
        self.assertIn("verbose-mode", self.run_cli("names")[1].split())
        self.assertIn("Service endpoint.", self.run_cli("names", "--verbose")[1])

    def test_path_prints_selected_and_all_tiers(self) -> None:
        _, out, _ = self.run_cli("path")
        self.assertEqual(Path(out.strip()), self.project_dir / ".demo.json")
        _, out, _ = self.run_cli("path", "--all")
        for tier in ("project", "user", "system"):
            self.assertIn(tier, out)
        _, out, _ = self.run_cli("path", "--system")
        self.assertEqual(Path(out.strip()), self.system_file)

    def test_edit_prefers_visual_over_editor(self) -> None:
        calls: list[list[str]] = []

        def launcher(command: list[str]) -> int:
            calls.append(command)
            return 0

        code, _, _ = self.run_cli("edit", launcher=launcher, VISUAL="visual-ed", EDITOR="plain-ed")
        self.assertEqual(code, 0)
        self.assertEqual(calls[0][0], "visual-ed")
        self.assertEqual(Path(calls[0][-1]), self.project_dir / ".demo.json")
        self.environ.pop("VISUAL")
        self.run_cli("edit", launcher=launcher)
        self.assertEqual(calls[1][0], "plain-ed")


class ConfigIntegrationTests(_SettingsFixture):
    def test_sample_tool_end_to_end(self) -> None:
        harness = ToolHarness("demo", "Demo tool.", version="1.0.0", repo_dir=self.root)
        add_config_actions(harness, self.schema())

        def run(*argv: str) -> tuple[int, str]:
            out = io.StringIO()
            with contextlib.redirect_stdout(out), contextlib.redirect_stderr(io.StringIO()):
                return harness.run(list(argv)), out.getvalue()

        self.assertEqual(run("config", "set", "retries", "8")[0], 0)
        code, out = run("config", "get", "retries", "--source")
        self.assertEqual(code, 0)
        self.assertIn("project", out)
        self.assertIn("8", out)
        code, out = run("config", "path", "--all")
        self.assertEqual(code, 0)
        self.assertIn(".demo.json", out)
        self.assertIn("config.json", out)
        self.assertIn("config", harness.format_help())


if __name__ == "__main__":
    unittest.main()
