#!/usr/bin/env python3
"""
Unit tests for scripts/_tool_common.py.
"""

from __future__ import annotations

import sys
import unittest
from pathlib import Path
from unittest import mock

SCRIPTS_DIR = Path(__file__).resolve().parent.parent / "scripts"
sys.path.insert(0, str(SCRIPTS_DIR))
import _tool_common as tool_common  # noqa: E402


class ResolveBuildMetadataTests(unittest.TestCase):
    def setUp(self) -> None:
        tool_common.resolve_build_metadata.cache_clear()

    def tearDown(self) -> None:
        tool_common.resolve_build_metadata.cache_clear()

    def test_returns_short_hash_from_git(self) -> None:
        fake_result = mock.Mock(returncode=0, stdout="af31b0d\n")
        with mock.patch.object(tool_common.subprocess, "run", return_value=fake_result):
            self.assertEqual(tool_common.resolve_build_metadata(), "af31b0d")

    def test_falls_back_when_git_fails(self) -> None:
        fake_result = mock.Mock(returncode=128, stdout="")
        with mock.patch.object(tool_common.subprocess, "run", return_value=fake_result):
            self.assertEqual(tool_common.resolve_build_metadata(), "unknown")

    def test_falls_back_when_git_missing(self) -> None:
        with mock.patch.object(tool_common.subprocess, "run", side_effect=FileNotFoundError):
            self.assertEqual(tool_common.resolve_build_metadata(), "unknown")

    def test_is_cached(self) -> None:
        fake_result = mock.Mock(returncode=0, stdout="af31b0d\n")
        with mock.patch.object(tool_common.subprocess, "run", return_value=fake_result) as run_mock:
            tool_common.resolve_build_metadata()
            tool_common.resolve_build_metadata()
        run_mock.assert_called_once()


class GetFullVersionTests(unittest.TestCase):
    def setUp(self) -> None:
        tool_common.resolve_build_metadata.cache_clear()

    def tearDown(self) -> None:
        tool_common.resolve_build_metadata.cache_clear()

    def test_combines_version_and_hash(self) -> None:
        with mock.patch.object(tool_common, "resolve_build_metadata", return_value="af31b0d"):
            self.assertEqual(tool_common.get_full_version("9.9.9-test"), "9.9.9-test+af31b0d")

    def test_omits_metadata_when_hash_unknown(self) -> None:
        with mock.patch.object(tool_common, "resolve_build_metadata", return_value="unknown"):
            self.assertEqual(tool_common.get_full_version("9.9.9-test"), "9.9.9-test")

    def test_defaults_to_project_version(self) -> None:
        with mock.patch.object(tool_common, "resolve_build_metadata", return_value="unknown"):
            self.assertEqual(tool_common.get_full_version(), tool_common.PROJECT_VERSION)


class LoggingFormattingTests(unittest.TestCase):
    def test_format_severity_indicator_padding(self) -> None:
        self.assertEqual(tool_common.format_severity_indicator("ERROR"), "**[ERROR]**")
        self.assertEqual(tool_common.format_severity_indicator("WARN"), "**[WARN]** ")
        self.assertEqual(tool_common.format_severity_indicator("WARNING"), "**[WARN]** ")
        self.assertEqual(tool_common.format_severity_indicator("INFO"), "**[INFO]** ")
        self.assertEqual(tool_common.format_severity_indicator("DEBUG"), "**[DEBUG]**")
        # Every standard severity indicator must be exactly 11 characters
        for level in ("ERROR", "WARN", "WARNING", "INFO", "DEBUG"):
            self.assertEqual(len(tool_common.format_severity_indicator(level)), 11)

    def test_format_origin(self) -> None:
        self.assertEqual(tool_common.format_origin("worker"), "<worker>")
        self.assertEqual(tool_common.format_origin("<worker>"), "<worker>")
        self.assertEqual(tool_common.format_origin(None), "")

    def test_format_utc_timestamp(self) -> None:
        from datetime import datetime, timezone

        dt = datetime(2026, 10, 9, 10, 48, 13, tzinfo=timezone.utc)
        self.assertEqual(tool_common.format_utc_timestamp(dt), "[2026-10-09 10:48:13]")

    def test_format_log_message_file_mode(self) -> None:
        from datetime import datetime, timezone

        dt = datetime(2026, 10, 9, 10, 48, 13, tzinfo=timezone.utc)
        msg = "Starting devops runner v1.12.8-pre with configuration:\n- Task: T0107"
        formatted = tool_common.format_log_message(msg, level="INFO", timestamp=dt, for_file=True)
        expected = (
            "[2026-10-09 10:48:13] **[INFO]**  Starting devops runner v1.12.8-pre with configuration:\n"
            "                                  - Task: T0107\n"
        )
        self.assertEqual(formatted, expected)

    def test_format_log_message_console_info_drops_tag(self) -> None:
        msg = "Starting devops runner v1.12.8-pre with configuration:\n- Task: T0107"
        formatted = tool_common.format_log_message(msg, level="INFO", for_file=False)
        expected = "Starting devops runner v1.12.8-pre with configuration:\n- Task: T0107\n"
        self.assertEqual(formatted, expected)

    def test_format_log_message_console_warn_with_origin(self) -> None:
        msg = "Configuration file missing optional cache directory\ndefaulting to temporary storage"
        formatted = tool_common.format_log_message(msg, level="WARN", origin="worker", for_file=False)
        expected = (
            "**[WARN]**  <worker> Configuration file missing optional cache directory\n"
            "                     defaulting to temporary storage\n"
        )
        self.assertEqual(formatted, expected)

    def test_format_log_message_console_debug(self) -> None:
        msg = "Cache lookup missed for key 'schema:v2'"
        formatted = tool_common.format_log_message(msg, level="DEBUG", origin="worker", for_file=False)
        expected = "**[DEBUG]** <worker> Cache lookup missed for key 'schema:v2'\n"
        self.assertEqual(formatted, expected)


class ToolLoggerTests(unittest.TestCase):
    def test_threshold_filtering(self) -> None:
        import io

        out = io.StringIO()
        err = io.StringIO()
        with mock.patch("sys.stdout", out), mock.patch("sys.stderr", err):
            logger = tool_common.ToolLogger(log_level="WARN")
            logger.info("should be dropped")
            logger.debug_msg("should be dropped")
            logger.warn("warning message")
            logger.error("error message")

        self.assertEqual(out.getvalue(), "")
        self.assertIn("**[WARN]**  warning message\n", err.getvalue())
        self.assertIn("**[ERROR]** error message\n", err.getvalue())

    def test_debug_routing_to_stdout(self) -> None:
        import io

        out = io.StringIO()
        err = io.StringIO()
        with mock.patch("sys.stdout", out), mock.patch("sys.stderr", err):
            logger = tool_common.ToolLogger(debug=True)
            logger.debug_msg("debugging info")

        self.assertEqual(err.getvalue(), "")
        self.assertIn("**[DEBUG]** debugging info\n", out.getvalue())

    def test_file_logging_with_utc_timestamp(self) -> None:
        import tempfile

        with tempfile.TemporaryDirectory() as tmp_dir:
            log_path = Path(tmp_dir) / "test.log"
            logger = tool_common.ToolLogger(log_file=log_path, log_level="INFO")
            logger.info("hello file")
            logger.close()

            content = log_path.read_text(encoding="utf-8")
            self.assertIn("**[INFO]**  hello file\n", content)
            self.assertRegex(content, r"^\[\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}\] \*\*\[INFO\]\*\*")

    def test_emit_writes_unadorned_to_stdout_and_timestamped_to_file(self) -> None:
        import io
        import tempfile

        with tempfile.TemporaryDirectory() as tmp_dir:
            log_path = Path(tmp_dir) / "emit.log"
            out = io.StringIO()
            with mock.patch("sys.stdout", out):
                logger = tool_common.ToolLogger(log_file=log_path, log_level="INFO")
                logger.emit("tool output row 1")
                logger.emit("tool output row 2")
                logger.close()

            self.assertEqual(out.getvalue(), "tool output row 1\ntool output row 2\n")
            content = log_path.read_text(encoding="utf-8")
            lines = content.splitlines()
            self.assertEqual(len(lines), 2)
            self.assertRegex(lines[0], r"^\[\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}\] tool output row 1$")
            self.assertRegex(lines[1], r"^\[\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}\] tool output row 2$")
            self.assertNotIn("**[", content)

    def test_logger_explicit_level_overrides_debug(self) -> None:
        logger = tool_common.ToolLogger(log_level="INFO", debug=True)
        self.assertEqual(logger.effective_level, "INFO")

        logger_debug = tool_common.ToolLogger(debug=True)
        self.assertEqual(logger_debug.effective_level, "DEBUG")

        logger_default = tool_common.ToolLogger()
        self.assertEqual(logger_default.effective_level, "INFO")

    def test_resolve_log_level_overrides_debug(self) -> None:
        self.assertEqual(tool_common.resolve_log_level("ERROR", debug=True), "ERROR")
        self.assertEqual(tool_common.resolve_log_level("INFO", debug=True), "INFO")
        self.assertEqual(tool_common.resolve_log_level(None, debug=True), "DEBUG")
        self.assertEqual(tool_common.resolve_log_level(None, debug=False), "INFO")


class ToolHarnessTests(unittest.TestCase):
    def setUp(self) -> None:
        self.harness = tool_common.ToolHarness(
            name="sample-tool",
            description="Sample tool for harness testing.",
            version="1.2.3",
            copyright="Copyright (c) Test",
        )
        self.harness.add_action(
            name="run-job",
            description="Execute the sample job.",
            detail="Runs the sample job with given configuration.",
            handler=lambda args, logger: 0,
        )

    def test_bare_invocation_shows_help_and_exits_zero(self) -> None:
        import io

        out = io.StringIO()
        err = io.StringIO()
        with mock.patch("sys.stdout", out), mock.patch("sys.stderr", err):
            code = self.harness.run([])
        self.assertEqual(code, 0)
        self.assertEqual(err.getvalue(), "")
        stdout = out.getvalue()
        expected_version = f"sample-tool v{tool_common.get_full_version('1.2.3')} - Copyright (c) Test"
        self.assertIn(expected_version, stdout)
        self.assertIn("Sample tool for harness testing.", stdout)
        self.assertIn("Actions:", stdout)
        self.assertIn("run-job", stdout)
        self.assertIn("Options:", stdout)
        self.assertIn("-h, --help", stdout)
        self.assertIn("--version", stdout)
        self.assertIn("Exit codes:", stdout)
        self.assertIn("0   success", stdout)

    def test_help_subcommand_and_flags_exit_zero(self) -> None:
        expected_version = f"sample-tool v{tool_common.get_full_version('1.2.3')} - Copyright (c) Test"
        for argv in (["help"], ["--help"], ["-h"]):
            import io

            out = io.StringIO()
            with mock.patch("sys.stdout", out):
                code = self.harness.run(argv)
            self.assertEqual(code, 0)
            self.assertIn(expected_version, out.getvalue())

    def test_help_verbose_shows_detailed_documentation(self) -> None:
        self.harness.set_examples(["sample-tool run-job --dry-run"])
        import io

        out = io.StringIO()
        with mock.patch("sys.stdout", out):
            code = self.harness.run(["help", "--verbose"])
        self.assertEqual(code, 0)
        stdout = out.getvalue()
        self.assertIn("Detailed Action Descriptions:", stdout)
        self.assertIn("Runs the sample job with given configuration.", stdout)
        self.assertIn("Examples:", stdout)
        self.assertIn("sample-tool run-job --dry-run", stdout)

    def test_action_specific_help_flag(self) -> None:
        import io

        out = io.StringIO()
        with mock.patch("sys.stdout", out):
            code = self.harness.run(["run-job", "--help"])
        self.assertEqual(code, 0)
        stdout = out.getvalue()
        self.assertIn("Detailed Action Description: run-job\n  Runs the sample job with given configuration.", stdout)
        self.assertIn("Usage:\n  sample-tool run-job", stdout)
        self.assertNotIn("Actions:", stdout)

    def test_action_specific_help_section_order(self) -> None:
        import io

        self.harness.set_examples(["sample-tool run-job --dry-run"])
        out = io.StringIO()
        with mock.patch("sys.stdout", out):
            code = self.harness.run(["run-job", "--help"])
        self.assertEqual(code, 0)
        stdout = out.getvalue()
        desc_pos = stdout.find("Detailed Action Description: run-job")
        ex_pos = stdout.find("Examples:\n  sample-tool run-job --dry-run")
        usage_pos = stdout.find("Usage:\n  sample-tool run-job")
        opts_pos = stdout.find("Options:\n")
        exit_pos = stdout.find("Exit codes:\n")
        self.assertNotEqual(desc_pos, -1)
        self.assertNotEqual(ex_pos, -1)
        self.assertNotEqual(usage_pos, -1)
        self.assertNotEqual(opts_pos, -1)
        self.assertNotEqual(exit_pos, -1)
        self.assertTrue(desc_pos < ex_pos < usage_pos < opts_pos < exit_pos)

    def test_help_subcommand_with_action_argument(self) -> None:
        import io

        out = io.StringIO()
        with mock.patch("sys.stdout", out):
            code = self.harness.run(["help", "run-job"])
        self.assertEqual(code, 0)
        stdout = out.getvalue()
        self.assertIn("Usage:\n  sample-tool run-job", stdout)
        self.assertNotIn("Actions:", stdout)

    def test_version_subcommand_and_flag_exit_zero(self) -> None:
        expected_version = f"sample-tool v{tool_common.get_full_version('1.2.3')} - Copyright (c) Test"
        for argv in (["version"], ["--version"]):
            import io

            out = io.StringIO()
            with mock.patch("sys.stdout", out):
                code = self.harness.run(argv)
            self.assertEqual(code, 0)
            self.assertEqual(out.getvalue().strip(), expected_version)

    def test_action_dispatch_and_logging_lifecycle(self) -> None:
        executed = []

        def sample_handler(args, logger):
            executed.append(True)
            logger.info("Inside action handler")
            return 0

        harness = tool_common.ToolHarness(
            name="sample-tool",
            description="Sample tool.",
            version="1.0.0",
            copyright="Copyright (c) Test",
        )
        harness.add_action("do-work", "Perform work", handler=sample_handler)

        import io

        out = io.StringIO()
        err = io.StringIO()
        with mock.patch("sys.stdout", out), mock.patch("sys.stderr", err):
            code = harness.run(["do-work"])

        self.assertEqual(code, 0)
        self.assertTrue(executed)
        stdout = out.getvalue()
        self.assertRegex(stdout, r"Starting sample-tool v1\.0\.0\S* with configuration:")
        self.assertIn("- Command: do-work", stdout)
        self.assertIn("Inside action handler", stdout)
        self.assertIn("Finished sample-tool do-work in", stdout)
        self.assertIn("status: succeeded", stdout)

    def test_action_failure_logs_completion_error_and_returns_code(self) -> None:
        def failing_handler(args, logger):
            logger.error("Something went wrong")
            return 1

        harness = tool_common.ToolHarness(
            name="sample-tool",
            description="Sample tool.",
            version="1.0.0",
            copyright="Copyright (c) Test",
        )
        harness.add_action("fail-job", "Fails", handler=failing_handler)

        import io

        out = io.StringIO()
        err = io.StringIO()
        with mock.patch("sys.stdout", out), mock.patch("sys.stderr", err):
            code = harness.run(["fail-job"])

        self.assertEqual(code, 1)
        self.assertIn("**[ERROR]** Something went wrong", err.getvalue())
        self.assertIn("status: failed", err.getvalue())

    def test_unknown_subcommand_prints_error_and_exits_two(self) -> None:
        import io

        err = io.StringIO()
        with mock.patch("sys.stderr", err):
            code = self.harness.run(["unknown-cmd"])
        self.assertEqual(code, 2)
        self.assertIn("**[ERROR]** Unknown subcommand: 'unknown-cmd'", err.getvalue())

    def test_custom_exit_codes_included_in_help(self) -> None:
        self.harness.set_exit_codes({130: "interrupted by user"})
        help_text = self.harness.format_help()
        self.assertIn("130 interrupted by user", help_text)

    def test_fallback_action_dispatches_when_no_subcommand_matched(self) -> None:
        target_received = []

        def kill_handler(args, logger):
            target_received.extend(args.pids)
            return 0

        harness = tool_common.ToolHarness(
            name="kill-tool",
            description="Process killer.",
            fallback_action="kill",
        )
        act = harness.add_action("kill", "Kill process", handler=kill_handler)
        act.configure_parser = lambda p: p.add_argument("pids", nargs="+")

        import io

        with mock.patch("sys.stdout", io.StringIO()):
            code = harness.run(["1234", "5678"])
        self.assertEqual(code, 0)
        self.assertEqual(target_received, ["1234", "5678"])

    def test_passthrough_unknown_args_when_allowed(self) -> None:
        passed_extra = []

        def test_runner(args, logger, passthrough):
            passed_extra.extend(passthrough)
            return 0

        harness = tool_common.ToolHarness(name="runner", description="Test runner.")
        harness.add_action("test", "Run tests", handler=test_runner, allow_unknown_args=True)

        import io

        with mock.patch("sys.stdout", io.StringIO()):
            code = harness.run(["test", "-k", "digest", "--", "-v", "-x"])
        self.assertEqual(code, 0)
        self.assertIn("-k", passed_extra)
        self.assertIn("digest", passed_extra)
        self.assertIn("-v", passed_extra)
        self.assertIn("-x", passed_extra)

    def test_extra_startup_configuration_logged(self) -> None:
        harness = tool_common.ToolHarness(name="sample-tool", description="Sample tool.")
        harness.add_action("job", "Sample job", handler=lambda args, logger: 0)

        import io

        out = io.StringIO()
        with mock.patch("sys.stdout", out):
            code = harness.run(["job"], extra_startup={"Target": "production", "Workers": 4})
        self.assertEqual(code, 0)
        stdout = out.getvalue()
        self.assertIn("- Target: production", stdout)
        self.assertIn("- Workers: 4", stdout)

    def test_global_argument_support(self) -> None:
        harness = tool_common.ToolHarness(name="sample-tool", description="Sample tool.")
        harness.add_global_argument("--config", type=str, help="configuration file path")
        recorded_cfg = []
        harness.add_action("check", "Check status", handler=lambda args, logger: recorded_cfg.append(args.config) or 0)

        import io

        with mock.patch("sys.stdout", io.StringIO()):
            code = harness.run(["check", "--config", "conf.json"])
        self.assertEqual(code, 0)
        self.assertEqual(recorded_cfg, ["conf.json"])

    def test_global_argument_help_shows_metavar(self) -> None:
        harness = tool_common.ToolHarness(name="sample-tool", description="Sample tool.")
        harness.add_global_argument("--timeout", type=int, metavar="SECONDS", help="per-run timeout")
        harness.add_global_argument("--force", action="store_true", help="skip confirmation")
        help_text = harness.format_help()
        self.assertRegex(help_text, r"(?m)^  --timeout SECONDS\s+per-run timeout$")
        self.assertRegex(help_text, r"(?m)^  --force\s+skip confirmation$")

    def test_unknown_subcommand_logged_to_file(self) -> None:
        import io
        import tempfile

        with tempfile.TemporaryDirectory() as tmp_dir:
            log_path = Path(tmp_dir) / "err.log"
            err = io.StringIO()
            with mock.patch("sys.stderr", err):
                code = self.harness.run(["bogus-action", "--log-file", str(log_path)])
            self.assertEqual(code, 2)
            self.assertIn("**[ERROR]** Unknown subcommand: 'bogus-action'", err.getvalue())
            self.assertTrue(log_path.exists())
            log_content = log_path.read_text(encoding="utf-8")
            self.assertIn("**[ERROR]** Unknown subcommand: 'bogus-action'", log_content)

    def test_argument_parsing_error_logged_to_file(self) -> None:
        import io
        import tempfile

        with tempfile.TemporaryDirectory() as tmp_dir:
            log_path = Path(tmp_dir) / "err.log"
            err = io.StringIO()
            with mock.patch("sys.stderr", err):
                code = self.harness.run(["run-job", "--invalid-flag", "--log-file", str(log_path)])
            self.assertEqual(code, 2)
            self.assertIn("**[ERROR]**", err.getvalue())
            self.assertTrue(log_path.exists())
            log_content = log_path.read_text(encoding="utf-8")
            self.assertIn("**[ERROR]**", log_content)


if __name__ == "__main__":
    unittest.main()
