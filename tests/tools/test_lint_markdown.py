#!/usr/bin/env python3
"""Unit and integration tests for support_python.tools.lint_markdown."""

from __future__ import annotations

import contextlib
import io
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

from support_python.cli import COPYRIGHT, ToolHarness, get_full_version
from support_python.logging import ToolLogger, format_severity_indicator
from support_python.markdown.lint import MarkdownLinter
from support_python.tools import lint_markdown

SRC_DIR = Path(__file__).resolve().parents[2] / "src"
_MODULE_PATH = SRC_DIR / "support_python" / "tools" / "lint_markdown.py"
ERROR_INDICATOR = format_severity_indicator("ERROR")


def run_main(argv: list[str]) -> tuple[int, str, str]:
    """Run lint_markdown.main and capture its exit code, stdout, and stderr."""
    out, err = io.StringIO(), io.StringIO()
    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
        code = lint_markdown.main(argv)
    return code, out.getvalue(), err.getvalue()


class TestCLIAndMain(unittest.TestCase):
    def test_version_action_returns_zero(self) -> None:
        for argv in (["version"], ["--version"]):
            code, out, _ = run_main(argv)
            self.assertEqual(code, 0, argv)
            self.assertEqual(out, f"lint-markdown v{get_full_version()} - {COPYRIGHT}\n")

    def test_help_screens_start_with_version_header(self) -> None:
        header = f"lint-markdown v{get_full_version()} - {COPYRIGHT}\n"
        for argv in (["help"], ["help", "--verbose"], ["-h"], ["--help"], ["check", "--help"]):
            code, out, _ = run_main(argv)
            self.assertEqual(code, 0, argv)
            self.assertTrue(out.startswith(header), argv)
        self.assertIn("Automated markdown linter", run_main(["help"])[1])

    def test_help_documents_actions_options_and_exit_codes(self) -> None:
        _, out, _ = run_main(["help"])
        expected_tokens = (
            "lint-markdown check [{{path}}...] [options]",
            "lint-markdown fix [{{path}}...] [options]",
            "--exclude",
            "--rules",
            "--offline",
            "--timeout",
            "--fix",
            "--log-file",
            "--log-level",
            "Exit codes:",
            "lint violations found",
        )
        for expected in expected_tokens:
            self.assertIn(expected, out)

    def test_help_verbose_adds_action_details_and_rule_catalog(self) -> None:
        _, short_help, _ = run_main(["help"])
        _, verbose_help, _ = run_main(["help", "--verbose"])
        self.assertNotIn("Detailed Action Descriptions:", short_help)
        self.assertIn("Detailed Action Descriptions:", verbose_help)
        self.assertIn("Examples:", verbose_help)
        for rule_id, (name, _) in MarkdownLinter.RULES.items():
            self.assertNotIn(f"{rule_id}  {name}", short_help)
            self.assertIn(f"{rule_id}  {name}", verbose_help)

    def test_action_specific_help_shows_only_target_action(self) -> None:
        for action in ("check", "fix"):
            with self.subTest(action=action):
                code, out, err = run_main([action, "--help"])
                self.assertEqual((code, err), (0, ""))
                self.assertIn(f"Detailed Action Description: {action}", out)
                self.assertIn(f"Usage:\n  lint-markdown {action}", out)
                other_action = "fix" if action == "check" else "check"
                self.assertNotIn(f"Detailed Action Description: {other_action}", out)

    def test_help_subcommand_with_action_argument(self) -> None:
        code, out, err = run_main(["help", "check"])
        self.assertEqual((code, err), (0, ""))
        self.assertIn("Detailed Action Description: check", out)
        self.assertNotIn("Detailed Action Description: fix", out)

    def test_argument_error_routes_through_tool_logger(self) -> None:
        with patch.object(ToolLogger, "error") as mock_logger_error:
            code, _, _ = run_main(["check", "--bogus-flag"])
            self.assertEqual(code, 2)
            mock_logger_error.assert_called_once()
            self.assertIn("unrecognized arguments: --bogus-flag", mock_logger_error.call_args[0][0])

    def test_bare_invocation_shows_help_without_linting(self) -> None:
        with patch.object(lint_markdown, "discover_markdown_files") as discover:
            code, out, err = run_main([])
        self.assertEqual((code, err), (0, ""))
        discover.assert_not_called()
        self.assertEqual(out, run_main(["help"])[1])

    def test_unknown_subcommand_exits_two_with_standard_error_indicator(self) -> None:
        code, out, err = run_main(["lnt"])
        self.assertEqual((code, out), (2, ""))
        self.assertTrue(err.startswith(f"{ERROR_INDICATOR} Unknown subcommand: 'lnt'"), err)

    def test_check_clean_directory_returns_zero(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            (Path(tmp_dir) / "clean.md").write_bytes(b"# Clean Document\n\n- Item 1\n- Item 2\n")
            code, out, _ = run_main(["check", tmp_dir])
            self.assertEqual(code, 0)
            self.assertIn("All 1 markdown files passed linting.", out)

    def test_check_violations_returns_one(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            (Path(tmp_dir) / "dirty.md").write_bytes(b"# Dirty Document\n\n### Skipped H3\n")
            code, out, err = run_main(["check", tmp_dir])
            self.assertEqual(code, 1)
            self.assertIn("MD001", out)
            self.assertIn(f"{format_severity_indicator('WARN')} Found 1 lint issue across 1 files.", err)

    def test_fix_action_modifies_files_and_returns_zero(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            p = Path(tmp_dir) / "dirty.md"
            p.write_bytes(b"# Title\n\n* Asterisk bullet \n")
            code, out, _ = run_main(["fix", tmp_dir])
            self.assertEqual((code, p.read_bytes()), (0, b"# Title\n\n- Asterisk bullet\n"))
            self.assertIn("Auto-fixed formatting issues in 1 file.", out)

    def test_fix_option_on_check_applies_fixes(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            p = Path(tmp_dir) / "dirty.md"
            p.write_bytes(b"# Title\n\n* Asterisk bullet \n")
            code, _, _ = run_main(["check", "--fix", tmp_dir])
            self.assertEqual((code, p.read_bytes()), (0, b"# Title\n\n- Asterisk bullet\n"))

    def test_offline_flag_in_cli(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            (Path(tmp_dir) / "doc.md").write_bytes(b"# Title\n\nSee [Fake](https://invalid-host-test.org/404).\n")
            self.assertEqual(run_main(["check", "--offline", tmp_dir])[0], 0)

    def test_timeout_flag_in_cli(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            (Path(tmp_dir) / "clean.md").write_bytes(b"# Title\n\n- Bullet item\n")
            self.assertEqual(run_main(["check", "--timeout", "2.5", tmp_dir])[0], 0)

    def test_exclude_and_rules_options_in_cli(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            (Path(tmp_dir) / "skipped.md").write_bytes(b"# Title\n\n### Skipped H3\n")
            (Path(tmp_dir) / "tabs.md").write_bytes(b"# Title\n\n### Skipped H3\n")
            code, out, _ = run_main(["check", "--exclude", "skipped.md", "--rules", "md010", tmp_dir])
            self.assertEqual(code, 0)
            self.assertIn("All 1 markdown files passed linting.", out)

    def test_nonexistent_explicit_path_exits_two(self) -> None:
        code, _, err = run_main(["check", "nonexistent-path-for-test.md"])
        self.assertEqual(code, 2)
        self.assertIn(f"{ERROR_INDICATOR} Path does not exist: nonexistent-path-for-test.md", err)

    def test_unreadable_file_reports_standard_error_and_exits_one(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            (Path(tmp_dir) / "doc.md").write_bytes(b"# Title\n")
            with patch.object(Path, "read_bytes", side_effect=OSError("access denied")):
                code, _, err = run_main(["check", tmp_dir])
        self.assertEqual(code, 1)
        self.assertIn(f"{ERROR_INDICATOR} Failed to read", err)
        self.assertIn("access denied", err)

    def test_verbose_short_flag_in_cli(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            (Path(tmp_dir) / "clean.md").write_bytes(b"# Title\n\n- Bullet item\n")
            code, out, _ = run_main(["check", "-v", tmp_dir])
            self.assertEqual(code, 0)
            self.assertIn("OK: ", out)

    def test_check_resolves_md019_against_linted_project_directory(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            proj_root = Path(tmp_dir).resolve()
            (proj_root / ".git").mkdir()
            (proj_root / "src").mkdir(parents=True)
            (proj_root / "src" / "custom_module.py").write_text("# module", encoding="utf-8")
            (proj_root / "README.md").write_text(
                "# Readme\n\nSee `src/custom_module.py` for API. Do not use `scripts/generate-agent-digest.py`.\n",
                encoding="utf-8",
            )
            code, out, _ = run_main(["check", "--rules", "MD019", "--offline", str(proj_root)])
            self.assertEqual(code, 1)
            self.assertIn("src/custom_module.py", out)
            self.assertNotIn("scripts/generate-agent-digest.py", out)

    def test_log_file_and_log_level_in_cli(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            (Path(tmp_dir) / "clean.md").write_bytes(b"# Title\n\n- Bullet item\n")
            log_path = Path(tmp_dir) / "lint.log"
            code, _, _ = run_main(["check", "--log-file", str(log_path), "--log-level", "INFO", tmp_dir])
            self.assertEqual(code, 0)
            content = log_path.read_text(encoding="utf-8")
            self.assertRegex(content, r"^\[\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}\] \*\*\[INFO\]\*\*  Starting lint-markdown v")
            self.assertIn("All 1 markdown files passed linting.", content)
            self.assertIn("Finished lint-markdown check in", content)

    def test_lint_violations_recorded_in_log_file(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            dirty = Path(tmp_dir) / "dirty.md"
            dirty.write_bytes(b"# Dirty Document\n\n### Skipped H3\n")
            log_path = Path(tmp_dir) / "lint.log"
            code, out, _ = run_main(["check", "--log-file", str(log_path), "--offline", str(dirty)])
            self.assertEqual(code, 1)
            self.assertIn("MD001", out)
            content = log_path.read_text(encoding="utf-8")
            self.assertRegex(content, r"\[\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}\] .*MD001")

    def test_startup_and_completion_banners_on_console_without_log_file(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            (Path(tmp_dir) / "clean.md").write_bytes(b"# Title\n\n- Bullet item\n")
            code, out, _ = run_main(["check", tmp_dir])
        self.assertEqual(code, 0)
        self.assertTrue(out.startswith(f"Starting lint-markdown v{get_full_version()} with configuration:\n"), out)
        for token in ("- Command: check\n", "- Log file: none\n", f"- Working directory: {Path.cwd()}\n"):
            self.assertIn(token, out)
        self.assertRegex(out, r"Finished lint-markdown check in \d+\.\ds with status: succeeded\n$")

    def test_failed_check_logs_error_completion_summary(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            (Path(tmp_dir) / "dirty.md").write_bytes(b"# Dirty Document\n\n### Skipped H3\n")
            code, _, err = run_main(["check", tmp_dir])
        self.assertEqual(code, 1)
        self.assertRegex(err, r"\*\*\[ERROR\]\*\* Finished lint-markdown check in \d+\.\ds with status: failed")

    def test_debug_flag_logs_to_console_without_log_file(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            (Path(tmp_dir) / "clean.md").write_bytes(b"# Title\n\n- Bullet item\n")
            code, out, _ = run_main(["check", "--debug", "--offline", tmp_dir])
        self.assertEqual(code, 0)
        self.assertIn("- Log level: DEBUG\n", out)
        self.assertIn(f"{format_severity_indicator('DEBUG')} Linting 1 markdown file", out)

    def test_log_level_threshold_filters_console_without_log_file(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            (Path(tmp_dir) / "clean.md").write_bytes(b"# Title\n\n- Bullet item\n")
            code, out, err = run_main(["check", "--log-level", "ERROR", tmp_dir])
        self.assertEqual((code, out, err), (0, "", ""))

    def test_invalid_log_level_exits_two_with_standard_error_indicator(self) -> None:
        code, out, err = run_main(["check", "--log-level", "INVALID"])
        self.assertEqual((code, out), (2, ""))
        self.assertTrue(err.startswith(f"{ERROR_INDICATOR} "), err)
        self.assertIn("--log-level", err)
        self.assertNotIn("error:", err)

    def test_invalid_timeout_and_unknown_option_exit_two_with_standard_error_indicator(self) -> None:
        for argv, expected in ((["check", "--timeout", "abc"], "--timeout"), (["check", "--bogus"], "--bogus")):
            code, out, err = run_main(argv)
            self.assertEqual((code, out), (2, ""), argv)
            self.assertTrue(err.startswith(f"{ERROR_INDICATOR} "), err)
            self.assertIn(expected, err)
            self.assertIn("Usage: lint-markdown", err)


class TestHarnessIntegration(unittest.TestCase):
    def test_cli_is_built_on_the_tool_harness(self) -> None:
        harness = lint_markdown.build_harness()
        self.assertIsInstance(harness, ToolHarness)
        self.assertEqual(harness.name, "lint-markdown")

    def test_package_root_does_not_load_cli_tool_module(self) -> None:
        cmd = [sys.executable, "-c", "import sys, support_python; assert 'support_python.tools.lint_markdown' not in sys.modules"]
        result = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", timeout=30)
        self.assertEqual(result.returncode, 0, result.stderr)


class TestEndToEnd(unittest.TestCase):
    def _run_script(self, *args: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [sys.executable, str(_MODULE_PATH), *args],
            cwd=SRC_DIR.parent,
            env={**os.environ, "PYTHONPATH": str(SRC_DIR)},
            capture_output=True,
            text=True,
            encoding="utf-8",
            timeout=60,
        )

    def test_script_entry_point_bare_invocation_shows_help(self) -> None:
        result = self._run_script()
        self.assertEqual((result.returncode, result.stderr), (0, ""), result.stderr)
        self.assertTrue(result.stdout.startswith("lint-markdown v"), result.stdout)
        self.assertIn("Actions:", result.stdout)
        self.assertIn("Exit codes:", result.stdout)

    def test_script_entry_point_checks_readme_offline(self) -> None:
        result = self._run_script("check", "--offline", "LICENSE.md")
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("All 1 markdown files passed linting.", result.stdout)
        self.assertIn("Finished lint-markdown check in", result.stdout)

    def test_lint_markdown_cli_check_and_fix_actions(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            clean = Path(tmp_dir) / "clean.md"
            clean.write_bytes(b"# Clean Document\n\n- Item 1\n- Item 2\n")
            code, out, err = run_main(["check", "--offline", str(clean)])
            self.assertEqual(code, 0, err)
            self.assertIn("All 1 markdown files passed linting.", out)

            dirty = Path(tmp_dir) / "dirty.md"
            dirty.write_bytes(b"# Title\n\n* Asterisk bullet \n")
            code_fix, _, err_fix = run_main(["fix", "--offline", str(dirty)])
            self.assertEqual((code_fix, dirty.read_bytes()), (0, b"# Title\n\n- Asterisk bullet\n"), err_fix)


if __name__ == "__main__":
    unittest.main()
