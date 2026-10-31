#!/usr/bin/env python3
"""
Unit tests for scripts/kill-processes.py.
"""

from __future__ import annotations

import contextlib
import importlib.util
import io
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

SCRIPTS_DIR = Path(__file__).resolve().parent.parent / "scripts"
sys.path.insert(0, str(SCRIPTS_DIR))

_MODULE_PATH = SCRIPTS_DIR / "kill-processes.py"
_spec = importlib.util.spec_from_file_location("kill_processes", _MODULE_PATH)
kill_processes = importlib.util.module_from_spec(_spec)
sys.modules[_spec.name] = kill_processes
_spec.loader.exec_module(kill_processes)

import _tool_common as tool_common  # noqa: E402


def run_main(argv: list[str]) -> tuple[int, str, str]:
    """Run kill_processes.main capturing exit code, stdout, and stderr."""
    out, err = io.StringIO(), io.StringIO()
    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
        code = kill_processes.main(argv)
    return code, out.getvalue(), err.getvalue()


def protected_pids() -> list[str]:
    """Return PIDs that kill-processes always skips: this process and its parent."""
    return [str(os.getpid()), str(os.getppid())]


class TestKillProcessesCli(unittest.TestCase):
    def test_bare_invocation_shows_help(self) -> None:
        code, out, err = run_main([])
        self.assertEqual(code, 0)
        self.assertIn("Usage:", out)
        self.assertTrue(out.startswith("kill-processes v"))
        self.assertEqual(err, "")

    def test_cli_help_and_version(self) -> None:
        self.assertEqual(run_main(["help"])[0], 0)
        self.assertEqual(run_main(["version"])[0], 0)
        self.assertEqual(run_main(["--help"])[0], 0)
        self.assertEqual(run_main(["--version"])[0], 0)
        # -v is reassigned to --verbose, so a lone -v is not a valid action
        self.assertEqual(run_main(["-v"])[0], 2)

    def test_cli_help_verbose(self) -> None:
        code, short_help, _ = run_main(["help"])
        self.assertEqual(code, 0)
        code, verbose_help, _ = run_main(["help", "--verbose"])
        self.assertEqual(code, 0)
        self.assertNotIn("Detailed Action Descriptions:", short_help)
        self.assertIn("Detailed Action Descriptions:", verbose_help)
        self.assertIn("Examples:", verbose_help)
        self.assertIn("-f, --force", short_help)
        self.assertEqual(run_main(["--help", "--verbose"])[0], 0)

    def test_cli_invalid_pid(self) -> None:
        code, out, err = run_main(["invalid_pid"])
        self.assertEqual(code, 2)
        self.assertNotIn("Starting kill-processes", out)
        self.assertIn("invalid_pid", err)
        self.assertEqual(run_main(["kill", "invalid_pid"])[0], 2)

    def test_cli_rejects_non_positive_pids(self) -> None:
        # PID 0 and negative PIDs address process groups on POSIX, so they are syntax errors
        self.assertEqual(run_main(["0"])[0], 2)
        self.assertEqual(run_main(["kill", "-1"])[0], 2)

    def test_kill_action_requires_pids(self) -> None:
        self.assertEqual(run_main(["kill"])[0], 2)
        code, out, err = run_main(["--debug"])
        self.assertEqual(code, 2)
        self.assertIn("required", err)
        self.assertNotIn("Starting kill-processes", out)

    def test_action_scoped_help_and_version(self) -> None:
        code, out, _ = run_main(["kill", "--help"])
        self.assertEqual(code, 0)
        self.assertIn("Detailed Action Description: kill", out)
        self.assertIn("Usage:\n  kill-processes kill {pid}... [options]", out)
        self.assertNotIn("Actions:", out)
        code, out, _ = run_main(["kill", "-h", "--verbose"])
        self.assertEqual(code, 0)
        self.assertIn("Detailed Action Description: kill", out)
        self.assertNotIn("Actions:", out)
        code, out, _ = run_main(["kill", "--version"])
        self.assertEqual(code, 0)
        self.assertTrue(out.startswith("kill-processes v"))

    def test_action_specific_help_shows_only_target_action(self) -> None:
        code, out, err = run_main(["kill", "--help"])
        self.assertEqual(code, 0)
        self.assertEqual(err, "")
        self.assertIn("Detailed Action Description: kill", out)
        self.assertIn("Usage:\n  kill-processes kill {pid}... [options]", out)
        self.assertNotIn("Actions:", out)

    def test_help_subcommand_with_action_argument(self) -> None:
        code, out, err = run_main(["help", "kill"])
        self.assertEqual(code, 0)
        self.assertEqual(err, "")
        self.assertIn("Detailed Action Description: kill", out)
        self.assertIn("Usage:\n  kill-processes kill {pid}... [options]", out)
        self.assertNotIn("Actions:", out)

    def test_argument_error_routes_through_tool_logger(self) -> None:
        with mock.patch.object(tool_common.ToolLogger, "error") as mock_logger_error:
            code, _, _ = run_main(["kill"])
            self.assertEqual(code, 2)
            mock_logger_error.assert_called_once()
            self.assertIn("the following arguments are required: pid", mock_logger_error.call_args[0][0])

    def test_invalid_pid_error_routes_through_tool_logger(self) -> None:
        with mock.patch.object(tool_common.ToolLogger, "error") as mock_logger_error:
            code, _, _ = run_main(["invalid_pid"])
            self.assertEqual(code, 2)
            mock_logger_error.assert_called_once()
            self.assertIn("invalid process ID: 'invalid_pid'", mock_logger_error.call_args[0][0])

    def test_argument_error_logs_to_log_file(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            log_path = Path(tmpdir) / "error.log"
            code, _, err = run_main(["kill", "--log-file", str(log_path)])
            self.assertEqual(code, 2)
            self.assertIn("the following arguments are required: pid", err)
            self.assertTrue(log_path.exists())
            content = log_path.read_text(encoding="utf-8")
            self.assertIn("the following arguments are required: pid", content)
            self.assertRegex(content, r"\[\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}\] \*\*\[ERROR\]\*\* ")

    def test_invalid_pid_logs_to_log_file(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            log_path = Path(tmpdir) / "error.log"
            code, _, err = run_main(["invalid_pid", "--log-file", str(log_path)])
            self.assertEqual(code, 2)
            self.assertIn("invalid process ID: 'invalid_pid'", err)
            self.assertTrue(log_path.exists())
            content = log_path.read_text(encoding="utf-8")
            self.assertIn("invalid process ID: 'invalid_pid'", content)
            self.assertRegex(content, r"\[\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}\] \*\*\[ERROR\]\*\* ")

    def test_normalize_argv_arrangements(self) -> None:
        normalize = kill_processes.normalize_argv
        self.assertEqual(normalize([]), [])
        self.assertEqual(normalize(["1234", "--debug"]), ["1234", "--debug"])
        self.assertEqual(normalize(["--debug", "1234"]), ["kill", "--debug", "1234"])
        self.assertEqual(normalize(["kill", "--help"]), ["help", "kill"])
        self.assertEqual(normalize(["1234", "-h", "-v"]), ["help", "kill", "--verbose"])
        self.assertEqual(normalize(["kill", "1234", "--version"]), ["version"])
        # Option values and tokens after '--' are not treated as informational flags
        self.assertEqual(normalize(["--log-file", "--help", "1234"]), ["kill", "--log-file", "--help", "1234"])
        self.assertEqual(normalize(["kill", "--", "--help"]), ["kill", "--", "--help"])

    def test_leading_options_with_implicit_kill(self) -> None:
        pid = str(os.getpid())
        code, out, _ = run_main(["--debug", pid])
        self.assertEqual(code, 0)
        self.assertIn("**[DEBUG]** Protected process hierarchy:", out)
        self.assertEqual(run_main(["--force", pid])[0], 0)
        self.assertEqual(run_main(["-v", "--log-level", "INFO", pid])[0], 0)
        self.assertEqual(run_main(["--debug", "0"])[0], 2)

    def test_protects_current_process(self) -> None:
        code, _, err = run_main([str(os.getpid())])
        self.assertEqual(code, 0)
        self.assertIn("**[WARN]**  Skipping protected PID", err)
        self.assertEqual(run_main(["kill", str(os.getpid()), "--force"])[0], 0)


class TestKillProcessesHierarchy(unittest.TestCase):
    @unittest.skipUnless(sys.platform == "win32", "Windows process snapshot")
    def test_windows_hierarchy_includes_grandparent_without_psutil(self) -> None:
        parent_map = kill_processes.windows_parent_map()
        parent = parent_map[os.getpid()]
        grandparent = parent_map[parent]
        with mock.patch.dict(sys.modules, {"psutil": None}):
            hierarchy = kill_processes.get_process_hierarchy(os.getpid())
        self.assertTrue({os.getpid(), parent, grandparent} <= hierarchy)


class TestKillProcessesLogging(unittest.TestCase):
    def test_uses_single_persistent_logger(self) -> None:
        original_init = tool_common.ToolLogger.__init__
        instances: list[object] = []

        def counting_init(self: object, *args: object, **kwargs: object) -> None:
            instances.append(self)
            original_init(self, *args, **kwargs)

        with mock.patch.object(tool_common.ToolLogger, "__init__", counting_init):
            code, _, _ = run_main(protected_pids() + ["--debug"])
        self.assertEqual(code, 0)
        self.assertEqual(len(instances), 1)

    def test_lifecycle_banners_in_log_file(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            log_path = Path(tmpdir) / "process.log"
            code, out, _ = run_main([str(os.getpid()), "--log-file", str(log_path)])
            self.assertEqual(code, 0)
            content = log_path.read_text(encoding="utf-8")
        self.assertRegex(content, r"^\[\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}\] \*\*\[INFO\]\*\*  Starting kill-processes v")
        self.assertIn("with configuration:", content)
        self.assertIn("- Command: kill", content)
        self.assertIn(f"- Log file: {log_path.resolve()}", content)
        self.assertRegex(content, r"Finished kill-processes kill in \d+\.\ds with status: succeeded")
        self.assertIn("Starting kill-processes v", out)
        self.assertIn("with status: succeeded", out)

    def test_debug_logs_protected_hierarchy(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            log_path = Path(tmpdir) / "process.log"
            code, out, _ = run_main([str(os.getpid()), "--log-file", str(log_path), "--debug"])
            self.assertEqual(code, 0)
            content = log_path.read_text(encoding="utf-8")
        self.assertIn("**[DEBUG]** Protected process hierarchy:", content)
        self.assertIn("**[DEBUG]** Protected process hierarchy:", out)

    def test_log_level_overrides_debug_flag(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            log_path = Path(tmpdir) / "process.log"
            code, _, _ = run_main([str(os.getpid()), "--log-file", str(log_path), "--log-level", "INFO", "--debug"])
            self.assertEqual(code, 0)
            content = log_path.read_text(encoding="utf-8")
        self.assertIn("Starting kill-processes", content)
        self.assertNotIn("**[DEBUG]**", content)

    def test_fallback_severity_indicator_padding(self) -> None:
        self.assertEqual(kill_processes.format_fallback_indicator("WARN"), "**[WARN]** ")
        self.assertEqual(kill_processes.format_fallback_indicator("ERROR"), "**[ERROR]**")
        self.assertEqual(kill_processes.format_fallback_indicator("info"), "**[INFO]** ")


class TestKillProcessesEndToEnd(unittest.TestCase):
    def run_script(self, script: Path, *args: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [sys.executable, "-I", str(script), *args],
            capture_output=True,
            text=True,
            encoding="utf-8",
            timeout=60,
        )

    def test_version_and_verbose_help(self) -> None:
        result = self.run_script(_MODULE_PATH, "version")
        self.assertEqual(result.returncode, 0)
        self.assertRegex(result.stdout, r"^kill-processes v\S+ - Copyright")
        result = self.run_script(_MODULE_PATH, "help", "--verbose")
        self.assertEqual(result.returncode, 0)
        self.assertIn("Detailed Action Descriptions:", result.stdout)

    def test_bare_invocation_exits_zero(self) -> None:
        result = self.run_script(_MODULE_PATH)
        self.assertEqual(result.returncode, 0)
        self.assertIn("Usage:", result.stdout)
        self.assertEqual(result.stderr, "")

    def test_action_scoped_help_and_version_exit_zero(self) -> None:
        result = self.run_script(_MODULE_PATH, "kill", "--help")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("Usage:", result.stdout)
        result = self.run_script(_MODULE_PATH, "kill", "--version")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertRegex(result.stdout, r"^kill-processes v\S+ - Copyright")

    def test_leading_options_skip_protected_parent(self) -> None:
        # This test process is the parent of the script process, so the script must skip it
        result = self.run_script(_MODULE_PATH, "--debug", "--force", str(os.getpid()))
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("**[DEBUG]** Protected process hierarchy:", result.stdout)
        self.assertIn(f"Skipping protected PID {os.getpid()}", result.stderr)

    def test_missing_lib_reports_padded_error(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            standalone = Path(tmpdir) / "kill-processes.py"
            shutil.copyfile(_MODULE_PATH, standalone)
            result = self.run_script(standalone, "help")
        self.assertEqual(result.returncode, 1)
        self.assertTrue(result.stderr.startswith("**[ERROR]** "), result.stderr)
        self.assertIn("the script harness", result.stderr)


if __name__ == "__main__":
    unittest.main()
