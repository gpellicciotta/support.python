import contextlib
import io
import unittest
from datetime import datetime
from pathlib import Path
from tempfile import TemporaryDirectory

from support_python import CliLogger, LogLevel, format_log_message, format_severity_indicator


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
            self.assertIn("Starting mytool v1.0.0", content)
            self.assertIn("Completed execution in", content)
            self.assertIn("done", content)


if __name__ == "__main__":
    unittest.main()
