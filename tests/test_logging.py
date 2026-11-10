import contextlib
import io
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Optional
from unittest import mock

from support_python import CliLogger, LogLevel, format_log_message, format_severity_indicator


class _UtcPlusTwoClock(datetime):
    """A clock frozen at 21:00 UTC on a machine whose local time zone is UTC+2."""

    @classmethod
    def now(cls, tz: Optional[timezone] = None) -> datetime:  # type: ignore[override]
        utc_now = datetime(2026, 9, 3, 21, 0, 0, tzinfo=timezone.utc)
        if tz is None:
            return datetime(2026, 9, 3, 23, 0, 0)
        return utc_now.astimezone(tz)


class LogLevelTests(unittest.TestCase):
    def test_to_string_known_levels(self) -> None:
        self.assertEqual(LogLevel.to_string(LogLevel.ERROR), "ERROR")
        self.assertEqual(LogLevel.to_string(LogLevel.WARNING), "WARNING")
        self.assertEqual(LogLevel.to_string(LogLevel.INFO), "INFO")
        self.assertEqual(LogLevel.to_string(LogLevel.DEBUG), "DEBUG")
        self.assertEqual(LogLevel.to_string(LogLevel.NONE), "NONE")
        self.assertEqual(LogLevel.to_string(LogLevel.ALL), "ALL")

    def test_to_string_unknown_level_falls_back_to_number(self) -> None:
        self.assertEqual(LogLevel.to_string(750), "750")

    def test_parse_known_names_case_insensitive(self) -> None:
        self.assertEqual(LogLevel.parse("error"), LogLevel.ERROR)
        self.assertEqual(LogLevel.parse("Warning"), LogLevel.WARNING)
        self.assertEqual(LogLevel.parse("  DEBUG  "), LogLevel.DEBUG)

    def test_parse_numeric_string(self) -> None:
        self.assertEqual(LogLevel.parse("750"), 750)

    def test_parse_invalid_raises(self) -> None:
        with self.assertRaises(ValueError):
            LogLevel.parse("not-a-level")

    def test_error_outranks_warning_outranks_info_outranks_debug(self) -> None:
        self.assertGreater(LogLevel.ERROR, LogLevel.WARNING)
        self.assertGreater(LogLevel.WARNING, LogLevel.INFO)
        self.assertGreater(LogLevel.INFO, LogLevel.DEBUG)
        self.assertLess(LogLevel.DEBUG, LogLevel.NONE)
        self.assertGreater(LogLevel.DEBUG, LogLevel.ALL)


class FormatSeverityIndicatorTests(unittest.TestCase):
    def test_pads_known_levels_to_eleven_chars(self) -> None:
        self.assertEqual(format_severity_indicator("WARN"), "**[WARN]** ")
        self.assertEqual(format_severity_indicator("INFO"), "**[INFO]** ")
        self.assertEqual(format_severity_indicator("ERROR"), "**[ERROR]**")
        self.assertEqual(format_severity_indicator("DEBUG"), "**[DEBUG]**")
        for tag in ("**[WARN]** ", "**[INFO]** ", "**[ERROR]**", "**[DEBUG]**"):
            self.assertEqual(len(tag), 11)

    def test_none_or_blank_returns_empty(self) -> None:
        self.assertEqual(format_severity_indicator(None), "")
        self.assertEqual(format_severity_indicator(""), "")


class FormatLogMessageTests(unittest.TestCase):
    def test_file_mode_includes_timestamp_level_and_origin(self) -> None:
        # general-guidelines.md's Logging section prescribes two spaces between the
        # (already space-padded) severity tag and <origin>.
        ts = datetime(2026, 9, 3, 21, 0, 0)
        result = format_log_message("Started", level="INFO", origin="cli", timestamp=ts, for_file=True)
        self.assertEqual(result, "[2026-09-03 21:00:00] **[INFO]**  <cli> Started\n")

    def test_file_mode_converts_aware_timestamp_to_utc(self) -> None:
        ts = datetime(2026, 9, 3, 23, 0, 0, tzinfo=timezone(timedelta(hours=2)))
        result = format_log_message("Started", level="INFO", timestamp=ts, for_file=True)
        self.assertEqual(result, "[2026-09-03 21:00:00] **[INFO]**  Started\n")

    def test_file_mode_defaults_to_current_utc_time(self) -> None:
        with mock.patch("support_python.logging.datetime", _UtcPlusTwoClock):
            result = format_log_message("Started", level="INFO", for_file=True)
        self.assertEqual(result, "[2026-09-03 21:00:00] **[INFO]**  Started\n")

    def test_stdout_mode_strips_timestamp_and_info_tag(self) -> None:
        result = format_log_message("Started", level="INFO", origin="cli", for_file=False)
        self.assertEqual(result, "<cli> Started\n")

    def test_stdout_mode_keeps_warn_and_error_tags(self) -> None:
        result = format_log_message("Oops", level="ERROR", for_file=False)
        self.assertEqual(result, "**[ERROR]** Oops\n")

    def test_multiline_message_is_vertically_aligned(self) -> None:
        result = format_log_message("First\nSecond", level="ERROR", for_file=False)
        lines = result.splitlines()
        self.assertEqual(lines[0], "**[ERROR]** First")
        self.assertEqual(lines[1], " " * len("**[ERROR]** ") + "Second")

    def test_multiline_message_preserves_blank_lines(self) -> None:
        result = format_log_message("First\n\nThird", level="ERROR", for_file=False)
        lines = result.splitlines()
        self.assertEqual(lines, ["**[ERROR]** First", "", " " * len("**[ERROR]** ") + "Third"])

    def test_empty_message_and_no_level_or_origin_returns_empty(self) -> None:
        self.assertEqual(format_log_message(""), "")


class CliLoggerTests(unittest.TestCase):
    def test_info_writes_to_stdout(self) -> None:
        with TemporaryDirectory() as tmp:
            logger = CliLogger(log_path=Path(tmp) / "run.log", origin="test")
            out = io.StringIO()
            with contextlib.redirect_stdout(out):
                logger.info("hello")
            self.assertIn("hello", out.getvalue())

    def test_progress_only_reaches_stdout_when_verbose(self) -> None:
        with TemporaryDirectory() as tmp:
            quiet_logger = CliLogger(log_path=Path(tmp) / "quiet.log", verbose=False)
            out = io.StringIO()
            with contextlib.redirect_stdout(out):
                quiet_logger.progress("step 1")
            self.assertEqual(out.getvalue(), "")

            verbose_logger = CliLogger(log_path=Path(tmp) / "verbose.log", verbose=True)
            out = io.StringIO()
            with contextlib.redirect_stdout(out):
                verbose_logger.progress("step 1")
            self.assertIn("step 1", out.getvalue())

    def test_debug_only_written_when_debug_enabled(self) -> None:
        with TemporaryDirectory() as tmp:
            log_path = Path(tmp) / "run.log"
            logger = CliLogger(log_path=log_path, debug=False)
            logger.debug("hidden")
            self.assertFalse(log_path.exists())

            log_path2 = Path(tmp) / "run2.log"
            debug_logger = CliLogger(log_path=log_path2, debug=True)
            debug_logger.debug("shown")
            self.assertIn("shown", log_path2.read_text(encoding="utf-8"))

    def test_warning_and_warn_alias_write_to_stderr(self) -> None:
        with TemporaryDirectory() as tmp:
            logger = CliLogger(log_path=Path(tmp) / "run.log")
            err = io.StringIO()
            with contextlib.redirect_stderr(err):
                logger.warning("careful")
            self.assertIn("careful", err.getvalue())
            self.assertIs(CliLogger.warn, CliLogger.warning)

    def test_error_writes_to_stderr_not_stdout(self) -> None:
        with TemporaryDirectory() as tmp:
            logger = CliLogger(log_path=Path(tmp) / "run.log")
            out, err = io.StringIO(), io.StringIO()
            with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
                logger.error("boom")
            self.assertEqual(out.getvalue(), "")
            self.assertIn("boom", err.getvalue())

    def test_log_start_and_log_end_write_to_file(self) -> None:
        with TemporaryDirectory() as tmp:
            log_path = Path(tmp) / "run.log"
            logger = CliLogger(log_path=log_path, origin="tool")
            logger.log_start("mytool", "1.0.0", ["mytool", "--flag"], {"key": "value"})
            logger.log_end("done")
            content = log_path.read_text(encoding="utf-8")
            self.assertRegex(
                content, r"Starting mytool v1\.0\.0 with configuration:\n\s+- Full command line given : mytool --flag\n"
            )
            self.assertIn("Completed execution in", content)
            self.assertIn("done", content)


class ResolveAndNormalizeLogLevelTests(unittest.TestCase):
    def test_resolve_log_level_precedence(self) -> None:
        from support_python.logging import normalize_log_level, resolve_log_level

        self.assertEqual(resolve_log_level("WARN", debug=True, default="INFO"), "WARN")
        self.assertEqual(resolve_log_level("  error ", debug=False, default="INFO"), "ERROR")
        self.assertEqual(resolve_log_level(None, debug=True, default="INFO"), "DEBUG")
        self.assertEqual(resolve_log_level(None, debug=False, default="INFO"), "INFO")
        self.assertEqual(resolve_log_level(None, debug=False, default="warn"), "WARN")
        self.assertEqual(normalize_log_level("warn"), "WARNING")
        self.assertEqual(normalize_log_level("  debug "), "DEBUG")
        self.assertIsNone(normalize_log_level("invalid-level"))
        self.assertIsNone(normalize_log_level(None))

    def test_log_level_parse_warn_and_eleven_char_padding(self) -> None:
        self.assertEqual(LogLevel.parse("warn"), LogLevel.WARNING)
        self.assertEqual(LogLevel.parse("WARN"), LogLevel.WARNING)
        tag = format_severity_indicator("TRACE")
        self.assertEqual(len(tag), 11)
        self.assertTrue(tag.startswith("**[TRACE]**"))


class UnifiedTeeAndToolLoggerTests(unittest.TestCase):
    def test_log_file_timestamps_use_utc(self) -> None:
        with TemporaryDirectory() as tmp:
            log_file = Path(tmp) / "utc.log"
            logger = CliLogger(log_file=log_file, log_level="INFO")
            with mock.patch("support_python.logging.datetime", _UtcPlusTwoClock), contextlib.redirect_stdout(io.StringIO()):
                logger.info("Starting work")
            logger.close()
            self.assertEqual(log_file.read_text(encoding="utf-8"), "[2026-09-03 21:00:00] **[INFO]**  Starting work\n")

    def test_logger_tees_to_file_and_console_with_matching_content(self) -> None:
        from support_python.logging import format_invocation_start, init_cli_logger, log_message

        with TemporaryDirectory() as tmp:
            log_file = Path(tmp) / "tee.log"
            logger = CliLogger(log_file=log_file, log_level="INFO", verbose=True, origin="app")
            out, err = io.StringIO(), io.StringIO()
            with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
                logger.info("Starting work")
                logger.warn("Careful now")
                logger.emit("raw-machine-output")
                logger.write("written line\n")
                logger.log_invocation("my-cli", "1.2.0", "sync", {"dry_run": True})
                logger.debug_msg("filtered debug")
            logger.close()

            stdout_text, stderr_text, file_text = out.getvalue(), err.getvalue(), log_file.read_text(encoding="utf-8")
            self.assertIn("<app> Starting work\n", stdout_text)
            self.assertIn("raw-machine-output\n", stdout_text)
            self.assertIn("<app> written line\n", stdout_text)
            self.assertNotIn("filtered debug", stdout_text)
            self.assertIn("**[WARN]**  <app> Careful now\n", stderr_text)
            for expected in (
                "**[INFO]**  <app> Starting work",
                "**[WARN]**  <app> Careful now",
                "raw-machine-output",
                "**[INFO]**  <app> written line",
                "Starting my-cli v1.2.0 (action: sync, dry_run: True)",
            ):
                self.assertIn(expected, file_text)
            self.assertNotIn("filtered debug", file_text)
            self.assertEqual(
                format_invocation_start("plan", "1.0.0", "list", {"all": True, "empty": ""}),
                "Starting plan v1.0.0 (action: list, all: True)",
            )
            single_log = Path(tmp) / "single.log"
            with contextlib.redirect_stdout(io.StringIO()):
                log_message("one-shot", level="INFO", log_file=single_log, origin="oneshot")
            self.assertIn("<oneshot> one-shot", single_log.read_text(encoding="utf-8"))
            self.assertIsNone(init_cli_logger(None))
            initialized = init_cli_logger(single_log, log_level="DEBUG")
            self.assertIsNotNone(initialized)
            assert initialized is not None
            initialized.close()

    def test_backward_compatible_defaults(self) -> None:
        self.assertEqual(format_log_message("dbg", level="DEBUG", for_file=False), "dbg\n")
        res_dbg = format_log_message("dbg", level="DEBUG", for_file=False, retain_debug_on_console=True)
        self.assertEqual(res_dbg, "**[DEBUG]** dbg\n")
        with TemporaryDirectory() as tmp:
            log_path = Path(tmp) / "compat.log"
            logger = CliLogger(log_path=log_path, log_level="DEBUG")
            out, err = io.StringIO(), io.StringIO()
            with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
                logger.log("bare-line")
                logger.log("warn-on-stdout", level="WARN")
                logger.debug("file-only-debug")
                logger.debug_msg("console-and-file-debug")
            logger.close()
            self.assertEqual(err.getvalue(), "")
            self.assertEqual(out.getvalue(), "bare-line\n**[WARN]**  warn-on-stdout\n**[DEBUG]** console-and-file-debug\n")
            file_lines = log_path.read_text(encoding="utf-8").splitlines()
            self.assertEqual(len(file_lines), 4)
            self.assertTrue(file_lines[0].endswith("] bare-line"))
            self.assertIn("**[DEBUG]** file-only-debug", file_lines[2])
            self.assertIn("**[DEBUG]** console-and-file-debug", file_lines[3])

    def test_tool_logger_and_tee_logger_aliases_are_removed(self) -> None:
        import support_python
        import support_python.logging as logging_mod

        for prefix in ("Tool", "Tee"):
            alias = f"{prefix}Logger"
            self.assertFalse(hasattr(logging_mod, alias), f"support_python.logging still exposes {alias}")
            self.assertNotIn(alias, logging_mod.__all__)
            self.assertFalse(hasattr(support_python, alias), f"support_python still exposes {alias}")
            self.assertNotIn(alias, support_python.__all__)


class CliLoggerJsonOutputTests(unittest.TestCase):
    def _capture(self, logger: CliLogger, action) -> tuple[str, str]:
        out, err = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            action(logger)
        return out.getvalue(), err.getvalue()

    def test_json_output_defaults_off(self) -> None:
        self.assertFalse(CliLogger().json_output)

    def test_json_output_redirects_console_messages_to_stderr(self) -> None:
        logger = CliLogger(debug=True)
        logger.json_output = True

        def log_all(lg: CliLogger) -> None:
            lg.info("info line")
            lg.progress("progress line")
            lg.warn("warn line")
            lg.error("error line")
            lg.debug_msg("debug line")
            lg.log("levelless line")
            lg.log_start("demo", "1.0", ["demo"], {})
            lg.log_end()

        out, err = self._capture(logger, log_all)
        self.assertEqual(out, "")
        for expected in (
            "info line",
            "progress line",
            "**[WARN]**  warn line",
            "**[ERROR]** error line",
            "**[DEBUG]** debug line",
            "levelless line",
            "Starting demo v1.0",
            "Completed execution in",
        ):
            self.assertIn(expected, err)

    def test_json_output_keeps_verbosity_rules(self) -> None:
        logger = CliLogger(verbose=False)
        logger.json_output = True
        out, err = self._capture(logger, lambda lg: (lg.progress("quiet progress"), lg.info("banner", to_stdout=False)))
        self.assertEqual((out, err), ("", ""))

    def test_json_output_keeps_file_logging(self) -> None:
        with TemporaryDirectory() as tmp:
            log_path = Path(tmp) / "run.log"
            logger = CliLogger(log_path=log_path)
            logger.json_output = True
            self._capture(logger, lambda lg: lg.info("to file"))
            self.assertIn("**[INFO]**  to file", log_path.read_text(encoding="utf-8"))

    def test_emit_json_writes_one_document_to_stdout(self) -> None:
        for json_output in (False, True):
            with self.subTest(json_output=json_output):
                logger = CliLogger()
                logger.json_output = json_output
                out, err = self._capture(logger, lambda lg: lg.emit_json({"b": [1, 2], "a": "x"}))
                self.assertEqual(out, '{"b": [1, 2], "a": "x"}\n')
                self.assertEqual(err, "")

    def test_emit_json_honors_indent(self) -> None:
        out, _ = self._capture(CliLogger(), lambda lg: lg.emit_json([{"name": "x"}], indent=2))
        self.assertEqual(out, '[\n  {\n    "name": "x"\n  }\n]\n')

    def test_emit_keeps_stdout_in_json_mode(self) -> None:
        logger = CliLogger()
        logger.json_output = True
        out, err = self._capture(logger, lambda lg: lg.emit('{"ok": true}'))
        self.assertEqual((out, err), ('{"ok": true}\n', ""))


if __name__ == "__main__":
    unittest.main()
