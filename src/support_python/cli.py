"""Shared, reusable argparse CLI helper and application entry point.

Implements the standard version/help/exit-code template from the CLI guideline
(action-oriented commands, `-h`/`--help`, `-v`/`--version`, `--verbose`/`--debug`,
a `{prog} v{version} - Copyright (c) {author}` header, and exit-codes listing).
"""

from __future__ import annotations

import argparse
from dataclasses import dataclass
from functools import lru_cache
import inspect
from pathlib import Path
import subprocess
import sys
import time
from typing import Any, Callable, NoReturn, Optional, Sequence, Tuple, Union

from .logging import CliLogger
from .version import get_package_version, get_project_version

#: Default copyright author name string used in CLI banners.
APP_AUTHOR: str = "Giovanni Pellicciotta"

#: Default full copyright notice string used in CLI banners.
COPYRIGHT: str = f"Copyright (c) {APP_AUTHOR}"

#: Default project version string resolved from package metadata or pyproject.toml.
PROJECT_VERSION: str = get_project_version()

#: Standard CLI exit codes mapped to short human-readable descriptions.
STANDARD_EXIT_CODES: Sequence[Tuple[int, str]] = [
    (0, "Success"),
    (1, "Error"),
]

#: Default harness exit codes mapping per CLI guidelines.
DEFAULT_EXIT_CODES: dict[int, str] = {
    0: "success",
    1: "operational or runtime execution error",
    2: "invalid arguments or syntax errors",
}

#: Application executable name for the demo CLI.
PROG: str = "support-python"

#: Application short description string for the demo CLI.
DESCRIPTION: str = "Python support CLI - reference implementation of the shared CLI version/help helper"

#: Supported action subcommands for the demo CLI.
ACTIONS: list[str] = ["greet", "backup", "version", "help"]

#: Type alias for an action handler callable returning an integer exit code.
ActionHandler = Callable[..., int]

#: Type alias for an argparse configurator callable.
ParserConfigurator = Callable[[argparse.ArgumentParser], None]


def _infer_caller_dir() -> Path:
    """Resolve the directory of the calling module or ``__main__.__file__``, falling back to this module's directory."""
    frame = inspect.currentframe()
    try:
        cur = frame.f_back if frame is not None else None
        this_file = Path(__file__).resolve()
        while cur is not None:
            mod_file = cur.f_globals.get("__file__")
            if isinstance(mod_file, str) and mod_file and Path(mod_file).resolve() != this_file:
                return Path(mod_file).resolve().parent
            cur = cur.f_back
    finally:
        del frame
    main_file = getattr(sys.modules.get("__main__"), "__file__", None)
    return Path(main_file).resolve().parent if isinstance(main_file, str) and main_file else Path(__file__).resolve().parent


@lru_cache(maxsize=16)
def resolve_build_metadata(cwd: Optional[Union[str, Path]] = None) -> str:
    """Resolve the short commit hash of the checkout as SemVer build metadata, or ``"unknown"``."""
    work_dir = Path(cwd).resolve() if cwd is not None else Path(__file__).resolve().parent
    try:
        res = subprocess.run(["git", "rev-parse", "--short", "HEAD"], cwd=work_dir, capture_output=True, text=True, timeout=5)
        if res.returncode == 0 and res.stdout.strip():
            return res.stdout.strip()
    except Exception:
        pass
    return "unknown"


def get_full_version(tool_version: Optional[str] = None, cwd: Optional[Union[str, Path]] = None) -> str:
    """Return ``tool_version`` decorated with build metadata (short commit hash), e.g. ``1.0.14-pre+af31b0d``."""
    base_version = tool_version if tool_version is not None else get_project_version(cwd)
    if "+" in base_version:
        return base_version
    metadata = resolve_build_metadata(cwd) if cwd is not None else resolve_build_metadata()
    return base_version if metadata == "unknown" else f"{base_version}+{metadata}"


@dataclass
class Action:
    """A named action or subcommand supported by :class:`ToolHarness`."""

    name: str
    description: str
    handler: Optional[ActionHandler] = None
    detail: str = ""
    usage_suffix: str = "[options]"
    configure_parser: Optional[ParserConfigurator] = None
    allow_unknown_args: bool = False


class ToolHarness:
    """Standardized CLI and logging harness enforcing the dev-guidelines CLI and logging conventions."""

    def __init__(
        self,
        name: str,
        description: str,
        version: Optional[str] = None,
        copyright: str = COPYRIGHT,
        default_log_file: Optional[Union[Path, str]] = None,
        default_log_level: str = "INFO",
        exit_codes: Optional[dict[int, str]] = None,
        examples: Optional[list[str]] = None,
        detailed_help: Optional[str] = None,
        fallback_action: Optional[str] = None,
        repo_dir: Optional[Union[Path, str]] = None,
    ) -> None:
        """Initialize the CLI action harness."""
        self.name, self.description, self.copyright = name, description, copyright
        self.repo_dir: Path = Path(repo_dir).resolve() if repo_dir is not None else _infer_caller_dir()
        self.version = version if version is not None else get_project_version(self.repo_dir)
        self.default_log_file = Path(default_log_file).resolve() if default_log_file else None
        self.default_log_level = default_log_level
        self.exit_codes: dict[int, str] = {**DEFAULT_EXIT_CODES, **(exit_codes or {})}
        self.examples: list[str] = list(examples or [])
        self.detailed_help, self.fallback_action = detailed_help, fallback_action
        self._actions: dict[str, Action] = {}
        self._global_args: list[tuple[tuple[Any, ...], dict[str, Any]]] = []

    def add_action(
        self,
        name: str,
        description: str,
        handler: Optional[ActionHandler] = None,
        detail: str = "",
        usage_suffix: str = "[options]",
        configure_parser: Optional[ParserConfigurator] = None,
        allow_unknown_args: bool = False,
    ) -> Action:
        """Register a subcommand action on this harness."""
        action = Action(name, description, handler, detail, usage_suffix, configure_parser, allow_unknown_args)
        self._actions[name] = action
        return action

    def add_global_argument(self, *args: Any, **kwargs: Any) -> None:
        """Add a custom argument that will be available on all actions."""
        self._global_args.append((args, kwargs))

    def set_examples(self, examples: list[str]) -> None:
        """Set example command lines shown in verbose help."""
        self.examples = list(examples)

    def set_exit_codes(self, exit_codes: dict[int, str]) -> None:
        """Set or update recognized exit codes."""
        self.exit_codes.update(exit_codes)

    def format_version(self) -> str:
        """Return single-line formatted version banner per CLI guidelines."""
        return f"{self.name} v{get_full_version(self.version, cwd=self.repo_dir)} - {self.copyright}"

    def _standard_option_lines(self) -> list[str]:
        return [
            "",
            "Options:",
            "  -h, --help             show help message and exit",
            "  --version              show version information and exit",
            "  -v, --verbose          enable verbose output logging",
            "  --debug                enable debug output logging",
            "  --log-file PATH        append operational logs to specified file",
            f"  --log-level LEVEL      logging severity threshold (DEBUG, INFO, WARN, ERROR; default: {self.default_log_level})",
        ]

    def format_help(self, verbose: bool = False) -> str:
        """Return standardized help screen per CLI guidelines."""
        lines = [self.format_version(), "", self.description, "", "Usage:"]
        if self._actions:
            for action in self._actions.values():
                lines.append(f"  {self.name} {action.name}{f' {action.usage_suffix}' if action.usage_suffix else ''}")
        else:
            lines.append(f"  {self.name} [options]")

        lines.extend([f"  {self.name} version", f"  {self.name} help [--verbose]", "", "Actions:"])
        act_col = max(max([len(name) for name in self._actions] + [7]) + 2, 23)
        for name, action in self._actions.items():
            lines.append(f"  {name:<{act_col}}{action.description}")
        lines.append(f"  {'version':<{act_col}}show version information and exit")
        lines.append(f"  {'help':<{act_col}}show help message and exit (use --verbose for details)")
        lines.extend(self._standard_option_lines())

        for g_args, g_kwargs in self._global_args:
            opts = ", ".join(arg for arg in g_args if isinstance(arg, str) and arg.startswith("-"))
            opts = f"{opts} {g_kwargs['metavar']}" if g_kwargs.get("metavar") else opts
            lines.append(f"  {opts:<23}{g_kwargs.get('help', '')}")

        lines.extend(["", "Exit codes:", *(f"  {code:<4}{self.exit_codes[code]}" for code in sorted(self.exit_codes))])
        if not verbose:
            return "\n".join(lines) + "\n"

        lines.append("\nDetailed Action Descriptions:")
        for name, action in self._actions.items():
            lines.extend([f"  {name}", *(f"      {d_line}" for d_line in (action.detail or action.description).splitlines())])
        if self.detailed_help:
            lines.append(f"\n{self.detailed_help.strip()}")
        if self.examples:
            lines.extend(["\nExamples:", *(f"  {ex}" for ex in self.examples)])
        return "\n".join(lines) + "\n"

    def format_action_help(self, action_name: str, verbose: bool = False) -> str:
        """Return standardized help screen for a specific subcommand."""
        action = self._actions[action_name]
        suffix = f" {action.usage_suffix}" if action.usage_suffix else ""
        lines = [self.format_version(), ""]
        detail_text = action.detail or action.description
        if detail_text:
            lines.extend([f"Detailed Action Description: {action_name}", *(f"  {d}" for d in detail_text.splitlines())])

        relevant = [ex for ex in self.examples if action_name in ex.split()] or [ex for ex in self.examples if action_name in ex]
        if relevant:
            lines.extend(["", "Examples:", *(f"  {ex}" for ex in relevant)])

        lines.extend(["", "Usage:", f"  {self.name} {action_name}{suffix}", *self._standard_option_lines()])
        standard_dest = {"help", "version", "verbose", "debug", "log_file", "log_level"}
        for action_obj in self._build_parser(action_name)._actions:
            if action_obj.dest not in standard_dest and action_obj.option_strings:
                lines.append(f"  {', '.join(action_obj.option_strings):<23}{action_obj.help or ''}")

        lines.extend(["", "Exit codes:", *(f"  {code:<4}{self.exit_codes[code]}" for code in sorted(self.exit_codes))])
        return "\n".join(lines) + "\n"

    def _extract_early_logger(self, args: Sequence[str]) -> CliLogger:
        """Construct a :class:`CliLogger` from raw args before full argument parsing completes."""
        log_file: Optional[Path] = self.default_log_file
        log_level: Optional[str] = None
        debug, verbose = False, False
        i, n = 0, len(args)
        while i < n:
            arg = args[i]
            if arg == "--":
                break
            if arg == "--log-file" and i + 1 < n:
                log_file, i = Path(args[i + 1]), i + 2
                continue
            if arg.startswith("--log-file="):
                val = arg.split("=", 1)[1]
                log_file = Path(val) if val else None
            elif arg == "--log-level" and i + 1 < n:
                log_level, i = args[i + 1].upper(), i + 2
                continue
            elif arg.startswith("--log-level="):
                log_level = arg.split("=", 1)[1].upper()
            elif arg == "--debug":
                debug = True
            elif arg in ("-v", "--verbose"):
                verbose = True
            i += 1
        return CliLogger(
            log_file=log_file,
            log_level=log_level or (None if debug else self.default_log_level),
            debug=debug,
            verbose=verbose,
        )

    def _build_parser(self, action_name: Optional[str] = None) -> argparse.ArgumentParser:
        prog = f"{self.name} {action_name}" if action_name else self.name
        parser = argparse.ArgumentParser(prog=prog, description=self.description, add_help=False)
        for flag in (("-h", "--help"), ("--version",), ("-v", "--verbose"), ("--debug",)):
            parser.add_argument(*flag, action="store_true")
        parser.add_argument("--log-file", type=str, default=str(self.default_log_file) if self.default_log_file else None)
        parser.add_argument("--log-level", type=str.upper, choices=["DEBUG", "INFO", "WARN", "ERROR"], default=None)
        for g_args, g_kwargs in self._global_args:
            parser.add_argument(*g_args, **g_kwargs)
        if action_name and action_name in self._actions and self._actions[action_name].configure_parser:
            self._actions[action_name].configure_parser(parser)  # type: ignore[misc]
        return parser

    def create_logger(self, args: argparse.Namespace) -> CliLogger:
        """Construct standard :class:`CliLogger` configured from parsed arguments."""
        log_path = Path(args.log_file).resolve() if getattr(args, "log_file", None) else self.default_log_file
        debug_flag = getattr(args, "debug", False)
        explicit_level = getattr(args, "log_level", None)
        effective_init_level = explicit_level if explicit_level is not None else (None if debug_flag else self.default_log_level)
        return CliLogger(
            log_file=log_path, log_level=effective_init_level, debug=debug_flag, verbose=getattr(args, "verbose", False)
        )

    def log_startup(self, logger: CliLogger, action: str, extra: Optional[dict[str, Any]] = None) -> None:
        """Emit single multi-line startup message per logging guidelines."""
        lines = [
            f"Starting {self.name} v{get_full_version(self.version, cwd=self.repo_dir)} with configuration:",
            f"- Command: {action}",
            f"- Log file: {logger.log_file or 'none'}",
            f"- Log level: {logger.effective_level}",
            f"- Verbose: {str(logger.verbose).lower()}",
            *(f"- {key}: {val}" for key, val in (extra or {}).items()),
        ]
        logger.info("\n".join(lines))

    def log_completion(self, logger: CliLogger, action: str, exit_code: int, started_at: float) -> None:
        """Emit completion summary upon exit per logging guidelines."""
        duration = time.monotonic() - started_at
        msg = f"Finished {self.name} {action} in {duration:.1f}s with status: {'succeeded' if exit_code == 0 else 'failed'}"
        logger.info(msg) if exit_code == 0 else logger.error(msg)

    def run(self, argv: Optional[Sequence[str]] = None, extra_startup: Optional[dict[str, Any]] = None) -> int:
        """Execute the requested command line, handling standard actions and logging."""
        raw_args = list(sys.argv[1:] if argv is None else argv)
        if not raw_args:
            print(self.format_help(verbose=False), end="")
            return 0

        first, rest = raw_args[0], raw_args[1:]
        if first in ("version", "--version"):
            print(self.format_version())
            return 0
        if first in ("help", "-h", "--help"):
            is_verbose = any(arg in ("-v", "--verbose") for arg in rest)
            targets = [arg for arg in rest if not arg.startswith("-")]
            out = (
                self.format_action_help(targets[0], verbose=is_verbose)
                if targets and targets[0] in self._actions
                else self.format_help(verbose=is_verbose)
            )
            print(out, end="")
            return 0

        action_name, action_args = first, rest
        if action_name not in self._actions:
            if self.fallback_action and self.fallback_action in self._actions and not first.startswith("-"):
                action_name, action_args = self.fallback_action, raw_args
            else:
                early_logger = self._extract_early_logger(raw_args)
                early_logger.error(
                    f"Unknown subcommand: '{first}'\nUsage: {self.name} {{help|version|{'|'.join(self._actions.keys())}}} [options]"
                )
                early_logger.close()
                return 2

        action = self._actions[action_name]
        parser = self._build_parser(action_name)
        if getattr(parser, "error", None) is not None:
            orig_error = parser.error
            if getattr(orig_error, "_is_harness_handler", False) or getattr(orig_error, "__qualname__", "").startswith(
                "ArgumentParser."
            ):

                def report_error(message: str) -> NoReturn:
                    early_logger = self._extract_early_logger(raw_args)
                    suffix = f" {action.usage_suffix}" if action.usage_suffix else " [options]"
                    early_logger.error(f"{message}\nUsage: {self.name} {action_name}{suffix}")
                    early_logger.close()
                    sys.exit(2)

                report_error._is_harness_handler = True  # type: ignore[attr-defined]
                parser.error = report_error  # type: ignore[method-assign]

        try:
            args, passthrough = (
                parser.parse_known_args(action_args) if action.allow_unknown_args else (parser.parse_args(action_args), [])
            )
        except SystemExit as exc:
            return exc.code if isinstance(exc.code, int) else 2

        if getattr(args, "version", False):
            print(self.format_version())
            return 0
        if getattr(args, "help", False):
            print(self.format_action_help(action_name, verbose=getattr(args, "verbose", False)), end="")
            return 0
        if action.handler is None:
            return 0

        logger = self.create_logger(args)
        started = time.monotonic()
        try:
            self.log_startup(logger, action_name, extra=extra_startup)
            param_count = len(inspect.signature(action.handler).parameters)
            if param_count >= 3 and action.allow_unknown_args:
                exit_code = action.handler(args, logger, passthrough)
            elif param_count >= 2:
                exit_code = action.handler(args, logger)
            else:
                exit_code = action.handler(args)
            self.log_completion(logger, action_name, exit_code, started)
            return exit_code
        except Exception as exc:
            logger.error(f"Execution error during {action_name}: {exc}")
            self.log_completion(logger, action_name, 1, started)
            return 1
        finally:
            logger.close()


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
    raw_args = list(sys.argv[1:] if argv is None else argv)
    if raw_args and raw_args[0] == "backup":
        from .backup import main as backup_main

        return backup_main(raw_args[1:])

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
    "COPYRIGHT",
    "Action",
    "ActionHandler",
    "DEFAULT_EXIT_CODES",
    "DESCRIPTION",
    "PROG",
    "PROJECT_VERSION",
    "ParserConfigurator",
    "STANDARD_EXIT_CODES",
    "ToolHarness",
    "build_action_parser",
    "format_support_message",
    "format_version",
    "get_full_version",
    "main",
    "print_help",
    "print_version",
    "resolve_build_metadata",
]

if __name__ == "__main__":
    sys.exit(main())
