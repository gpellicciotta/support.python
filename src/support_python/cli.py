"""Shared, reusable argparse CLI helper and application entry point.

Implements the standard version/help/exit-code template from the CLI guideline
(action-oriented commands, `-h`/`--help`, `-v`/`--version`, `--verbose`/`--debug`,
a `{prog} v{version} - Copyright (c) {author}` header, and exit-codes listing).
"""

from __future__ import annotations

import argparse
import sys
from typing import Optional, Sequence, Tuple

from .version import get_package_version, get_project_version

#: Default copyright author name string used in CLI banners.
APP_AUTHOR: str = "Giovanni Pellicciotta"

#: Standard CLI exit codes mapped to short human-readable descriptions.
STANDARD_EXIT_CODES: Sequence[Tuple[int, str]] = [
    (0, "Success"),
    (1, "Error"),
]

#: Application executable name for the demo CLI.
PROG: str = "support-python"

#: Application short description string for the demo CLI.
DESCRIPTION: str = "Python support CLI - reference implementation of the shared CLI version/help helper"

#: Supported action subcommands for the demo CLI.
ACTIONS: list[str] = ["greet", "version", "help"]


def build_action_parser(
    prog: str,
    description: str,
    actions: Sequence[str],
    default_action: Optional[str] = None,
) -> argparse.ArgumentParser:
    """Build an action-oriented parser with custom help, version, and logging flags.

    Configures an :class:`argparse.ArgumentParser` with an action positional argument and standard
    switches: ``-h``/``--help``, ``-v``/``--version``, ``--verbose``, and ``--debug``.

    Args:
        prog: Program name displayed in help and usage banners.
        description: Description text describing program functionality.
        actions: Sequence of supported action command names.
        default_action: Optional default action when none is provided on the command line.

    Returns:
        Configured :class:`argparse.ArgumentParser` instance.
    """
    parser = argparse.ArgumentParser(prog=prog, description=description, add_help=False)
    parser.add_argument("action", nargs="?", default=default_action, choices=list(actions), help="Action to perform")
    parser.add_argument("-h", "--help", action="store_true", help="Show this help message and exit")
    parser.add_argument("-v", "--version", action="store_true", help="Show version information and exit")
    parser.add_argument("--verbose", action="store_true", help="Provide more detailed operational progress on stdout/stderr")
    parser.add_argument("--debug", action="store_true", help="Allow debug-level log messages to be written out to the log file")
    return parser


def format_version(prog: str, version: Optional[str] = None, author: str = APP_AUTHOR) -> str:
    """Format single-line version string according to developer guidelines.

    Outputs formatted text: ``{prog} v{version} - Copyright (c) {author}``.

    Args:
        prog: Program or utility executable name.
        version: Optional version string. If omitted, resolved via :func:`~support_python.version.get_project_version`.
        author: Copyright holder name. Defaults to :const:`APP_AUTHOR`.

    Returns:
        Formatted single-line version string.
    """
    if version is None:
        version = get_project_version()
    return f"{prog} v{version} - Copyright (c) {author}"


def print_version(prog: str, version: Optional[str] = None, author: str = APP_AUTHOR) -> None:
    """Print the formatted version string to standard output.

    Args:
        prog: Program or utility executable name.
        version: Optional version string.
        author: Copyright holder name. Defaults to :const:`APP_AUTHOR`.
    """
    print(format_version(prog, version, author))


def print_help(
    prog: str,
    version: Optional[str],
    description: str,
    parser: argparse.ArgumentParser,
    exit_codes: Sequence[Tuple[int, str]] = STANDARD_EXIT_CODES,
    author: str = APP_AUTHOR,
) -> None:
    """Print the standard help template to standard output.

    Includes version banner header, description, argparse usage text, and exit-codes table.

    Args:
        prog: Program name string.
        version: Optional version string.
        description: Functional description text.
        parser: Configured :class:`argparse.ArgumentParser` whose usage and flags to print.
        exit_codes: Sequence of ``(code, description)`` tuples. Defaults to :const:`STANDARD_EXIT_CODES`.
        author: Copyright author name. Defaults to :const:`APP_AUTHOR`.
    """
    print_version(prog, version, author)
    print()
    print(description)
    print()
    parser.print_help()
    print("\nExit codes:")
    for code, meaning in exit_codes:
        print(f"  {code}  {meaning}")


def format_support_message(name: str) -> str:
    """Format support greeting message for demo CLI greeting.

    Args:
        name: Name string to greet.

    Returns:
        Formatted greeting string.
    """
    normalized = name.strip() or "there"
    return f"Hello {normalized}, from support.python!"


def _build_demo_parser() -> argparse.ArgumentParser:
    parser = build_action_parser(PROG, DESCRIPTION, ACTIONS, default_action="greet")
    parser.add_argument("name", nargs="?", default="there", help="Name to greet (used by the 'greet' action)")
    return parser


def main(argv: Optional[Sequence[str]] = None) -> int:
    """Execute the reference demonstration CLI application.

    Args:
        argv: Optional sequence of command-line argument strings. Defaults to ``sys.argv[1:]``.

    Returns:
        Exit code integer (0 for success).
    """
    parser = _build_demo_parser()
    args = parser.parse_args(argv)

    version = get_package_version("support-python")
    if version.startswith("0.0.0"):
        version = get_project_version()

    if args.help or args.action == "help":
        print_help(PROG, version, DESCRIPTION, parser)
        return 0
    if args.version or args.action == "version":
        print_version(PROG, version)
        return 0

    print(format_support_message(args.name))
    return 0


__all__ = [
    "ACTIONS",
    "APP_AUTHOR",
    "DESCRIPTION",
    "PROG",
    "STANDARD_EXIT_CODES",
    "build_action_parser",
    "format_support_message",
    "format_version",
    "main",
    "print_help",
    "print_version",
]

if __name__ == "__main__":
    sys.exit(main())
