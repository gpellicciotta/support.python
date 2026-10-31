"""Tests for support_python.cli module."""

from __future__ import annotations

from contextlib import redirect_stdout
import io
import unittest
from unittest.mock import patch

from support_python import __version__
from support_python.cli import (
    DESCRIPTION,
    PROG,
    build_action_parser,
    format_support_message,
    format_version,
    main,
    print_help,
    print_version,
)


class CliTests(unittest.TestCase):
    def test_cli_uses_default_name(self) -> None:
        buffer = io.StringIO()
        with patch("sys.argv", ["support-python"]), redirect_stdout(buffer):
            main()
        self.assertEqual(
            buffer.getvalue().strip(),
            "Hello there, from support.python!",
        )

    def test_cli_greet_action_uses_given_name(self) -> None:
        buffer = io.StringIO()
        with patch("sys.argv", ["support-python", "greet", "Alice"]), redirect_stdout(buffer):
            main()
        self.assertEqual(
            buffer.getvalue().strip(),
            "Hello Alice, from support.python!",
        )

    def test_cli_falls_back_for_blank_name(self) -> None:
        buffer = io.StringIO()
        with patch("sys.argv", ["support-python", "greet", "   "]), redirect_stdout(buffer):
            main()
        self.assertEqual(
            buffer.getvalue().strip(),
            "Hello there, from support.python!",
        )

    def test_cli_dash_v_prints_version_and_exits_zero(self) -> None:
        buffer = io.StringIO()
        with patch("sys.argv", ["support-python", "-v"]), redirect_stdout(buffer):
            exit_code = main()
        self.assertEqual(exit_code, 0)
        self.assertEqual(buffer.getvalue().strip(), f"support-python v{__version__} - Copyright (c) Giovanni Pellicciotta")

    def test_cli_version_action_matches_dash_v(self) -> None:
        buffer = io.StringIO()
        with patch("sys.argv", ["support-python", "version"]), redirect_stdout(buffer):
            exit_code = main()
        self.assertEqual(exit_code, 0)
        self.assertEqual(buffer.getvalue().strip(), f"support-python v{__version__} - Copyright (c) Giovanni Pellicciotta")

    def test_cli_dash_h_prints_help_with_exit_codes_and_exits_zero(self) -> None:
        buffer = io.StringIO()
        with patch("sys.argv", ["support-python", "-h"]), redirect_stdout(buffer):
            exit_code = main()
        self.assertEqual(exit_code, 0)
        output = buffer.getvalue()
        self.assertIn(f"support-python v{__version__} - Copyright (c) Giovanni Pellicciotta", output)
        self.assertIn("Exit codes:", output)
        self.assertIn("0  Success", output)
        self.assertIn("1  Error", output)

    def test_cli_help_action_matches_dash_h(self) -> None:
        buffer = io.StringIO()
        with patch("sys.argv", ["support-python", "help"]), redirect_stdout(buffer):
            exit_code = main()
        self.assertEqual(exit_code, 0)
        self.assertIn("Exit codes:", buffer.getvalue())

    def test_format_support_message(self) -> None:
        self.assertEqual(format_support_message("Bob"), "Hello Bob, from support.python!")
        self.assertEqual(format_support_message("   "), "Hello there, from support.python!")


class BuildActionParserTests(unittest.TestCase):
    def test_default_action_used_when_omitted(self) -> None:
        parser = build_action_parser(PROG, DESCRIPTION, ["greet", "version"], default_action="greet")
        args = parser.parse_args([])
        self.assertEqual(args.action, "greet")
        self.assertFalse(args.help)
        self.assertFalse(args.version)
        self.assertFalse(args.verbose)
        self.assertFalse(args.debug)

    def test_rejects_unknown_action(self) -> None:
        parser = build_action_parser(PROG, DESCRIPTION, ["greet", "version"], default_action="greet")
        with self.assertRaises(SystemExit):
            parser.parse_args(["not-an-action"])


class PrintVersionAndHelpTests(unittest.TestCase):
    def test_format_version(self) -> None:
        self.assertEqual(
            format_version("some-tool", "1.2.3", author="Some Author"),
            "some-tool v1.2.3 - Copyright (c) Some Author",
        )

    def test_print_version_uses_standard_template(self) -> None:
        buffer = io.StringIO()
        with redirect_stdout(buffer):
            print_version("some-tool", "1.2.3", author="Some Author")
        self.assertEqual(buffer.getvalue().strip(), "some-tool v1.2.3 - Copyright (c) Some Author")

    def test_print_help_lists_custom_exit_codes(self) -> None:
        parser = build_action_parser("some-tool", "A tool", ["run"], default_action="run")
        buffer = io.StringIO()
        with redirect_stdout(buffer):
            print_help("some-tool", "1.2.3", "A tool", parser, exit_codes=[(0, "OK"), (2, "Bad input")], author="Some Author")
        output = buffer.getvalue()
        self.assertIn("some-tool v1.2.3 - Copyright (c) Some Author", output)
        self.assertIn("0  OK", output)
        self.assertIn("2  Bad input", output)


if __name__ == "__main__":
    unittest.main()
