"""Shared, reusable action-oriented CLI harness and build-metadata version helpers.

Implements the standard version/help/exit-code template from the CLI guideline
(action-oriented commands, `-h`/`--help`, `--version`, `-v`/`--verbose`, `--debug`,
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
from .terminal import configure_utf8_output
from .version import get_package_version, get_project_version

#: Default copyright author name string used in CLI banners.
APP_AUTHOR: str = "Giovanni Pellicciotta"

#: Default full copyright notice string used in CLI banners.
COPYRIGHT: str = f"Copyright (c) {APP_AUTHOR}"

#: Default project version string resolved from package metadata or pyproject.toml.
PROJECT_VERSION: str = get_project_version()
if PROJECT_VERSION == "0.0.0+unknown":
    PROJECT_VERSION = get_project_version(Path(__file__).resolve().parent)
if PROJECT_VERSION == "0.0.0+unknown":
    PROJECT_VERSION = get_package_version("support-python")

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

    @staticmethod
    def add_format_option(parser: argparse.ArgumentParser, *, default: str = "text") -> None:
        """Add the standard ``--format {text,json}`` option; ``json`` switches the action's logger to JSON output mode."""
        parser.add_argument(
            "--format", choices=["text", "json"], default=default, help=f"output format (text or json; default: {default})"
        )

    def format_version(self) -> str:
        """Return single-line formatted version banner per CLI guidelines."""
        return f"{self.name} v{get_full_version(self.version, cwd=self.repo_dir)} - {self.copyright}"

    def _standard_option_rows(self) -> list[tuple[str, str]]:
        return [
            ("-h, --help", "show help message and exit"),
            ("--version", "show version information and exit"),
            ("-v, --verbose", "enable verbose output logging"),
            ("--debug", "enable debug output logging (implies --verbose)"),
            ("--log-file PATH", "append operational logs to specified file"),
            ("--log-level LEVEL", f"logging severity threshold (DEBUG, INFO, WARN, ERROR; default: {self.default_log_level})"),
        ]

    @staticmethod
    def _format_option_lines(rows: list[tuple[str, str]]) -> list[str]:
        """Render an ``Options:`` block whose help column clears the longest label by at least two spaces."""
        col = max(max(len(label) for label, _ in rows) + 2, 23)
        return ["", "Options:", *(f"  {label:<{col}}{text}".rstrip() for label, text in rows)]

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
        rows = self._standard_option_rows()
        for g_args, g_kwargs in self._global_args:
            opts = ", ".join(arg for arg in g_args if isinstance(arg, str) and arg.startswith("-"))
            opts = f"{opts} {g_kwargs['metavar']}" if g_kwargs.get("metavar") else opts
            rows.append((opts, g_kwargs.get("help", "")))
        lines.extend(self._format_option_lines(rows))

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

        lines.extend(["", "Usage:", f"  {self.name} {action_name}{suffix}"])
        standard_dest = {"help", "version", "verbose", "debug", "log_file", "log_level"}
        rows = self._standard_option_rows()
        for action_obj in self._build_parser(action_name)._actions:
            if action_obj.dest not in standard_dest and action_obj.option_strings:
                rows.append((", ".join(action_obj.option_strings), action_obj.help or ""))
        lines.extend(self._format_option_lines(rows))

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

    def _reorder_leading_options(self, args: list[str]) -> list[str]:
        """Put the action first when a fallback harness's command line starts with an option.

        The first non-option token after the leading options selects the action when it names one
        (``--verbose list``); otherwise the whole command line goes to the fallback action (``--url x``).
        Option arities come from the fallback action's parser, then from the other actions' parsers.
        An option with an optional or variable number of values never takes an action name as its value.
        Leading options move after the target of ``help`` and ``version``, which ignore them.
        """
        if not self.fallback_action or self.fallback_action not in self._actions:
            return args
        if not args[0].startswith("-") or args[0] in ("-h", "--help", "--version"):
            return args
        names = {*self._actions, "version", "help"}
        options: dict[str, argparse.Action] = {}
        for action_name in (self.fallback_action, *self._actions):
            for flag, option in self._build_parser(action_name)._option_string_actions.items():
                options.setdefault(flag, option)
        i = 0
        while i < len(args) and args[i].startswith("-") and args[i] != "--":
            option = self._lookup_option(options, args[i])
            i += 1
            nargs = option.nargs if option is not None else 0
            if nargs is None:
                nargs = 1
            if isinstance(nargs, int):
                i += nargs
            elif nargs == argparse.REMAINDER:
                i = len(args)
            else:
                while i < len(args) and not args[i].startswith("-") and args[i] not in names:
                    i += 1
                    if nargs == "?":
                        break
        if i < len(args) and args[i] in names:
            if args[i] in ("help", "version"):
                return [args[i], *args[i + 1 :], *args[:i]]
            return [args[i], *args[:i], *args[i + 1 :]]
        return [self.fallback_action, *args]

    @staticmethod
    def _lookup_option(options: dict[str, argparse.Action], token: str) -> Optional[argparse.Action]:
        """Resolve ``token`` as argparse would: exact flags, unique long prefixes, and bundled short flags."""
        if "=" in token:
            return None
        if token in options:
            return options[token]
        if token.startswith("--"):
            matches = {option for flag, option in options.items() if flag.startswith(token)}
            return matches.pop() if len(matches) == 1 else None
        if len(token) > 2:
            for position in range(1, len(token)):
                option = options.get(f"-{token[position]}")
                if option is None:
                    return None
                if option.nargs != 0:
                    return option if position == len(token) - 1 else None
        return None

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
        """Construct standard :class:`CliLogger` configured from parsed arguments.

        The logger runs in JSON output mode when the action's ``--format`` option is ``json``.
        """
        log_path = Path(args.log_file).resolve() if getattr(args, "log_file", None) else self.default_log_file
        debug_flag = getattr(args, "debug", False)
        explicit_level = getattr(args, "log_level", None)
        effective_init_level = explicit_level if explicit_level is not None else (None if debug_flag else self.default_log_level)
        logger = CliLogger(
            log_file=log_path, log_level=effective_init_level, debug=debug_flag, verbose=getattr(args, "verbose", False)
        )
        logger.json_output = getattr(args, "format", None) == "json"
        return logger

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
        logger.info("\n".join(lines), to_stdout=logger.verbose)

    def log_completion(self, logger: CliLogger, action: str, exit_code: int, started_at: float) -> None:
        """Emit completion summary upon exit; success reaches stdout only with ``--verbose``, failure goes to stderr."""
        duration = time.monotonic() - started_at
        msg = f"Finished {self.name} {action} in {duration:.1f}s with status: {'succeeded' if exit_code == 0 else 'failed'}"
        logger.info(msg, to_stdout=logger.verbose) if exit_code == 0 else logger.error(msg)

    def run(self, argv: Optional[Sequence[str]] = None, extra_startup: Optional[dict[str, Any]] = None) -> int:
        """Execute the requested command line, handling standard actions and logging."""
        configure_utf8_output()
        raw_args = list(sys.argv[1:] if argv is None else argv)
        if not raw_args:
            print(self.format_help(verbose=False), end="")
            return 0

        raw_args = self._reorder_leading_options(raw_args)
        first, rest = raw_args[0], raw_args[1:]
        if first in ("version", "--version"):
            print(self.format_version())
            return 0
        if first in ("help", "-h", "--help"):
            is_verbose = any(arg in ("-v", "--verbose", "--debug") for arg in rest)
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
        if getattr(args, "debug", False):
            args.verbose = True  # --debug implies --verbose for every handler reading args.verbose

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


__all__ = [
    "APP_AUTHOR",
    "COPYRIGHT",
    "Action",
    "ActionHandler",
    "DEFAULT_EXIT_CODES",
    "PROJECT_VERSION",
    "ParserConfigurator",
    "STANDARD_EXIT_CODES",
    "ToolHarness",
    "get_full_version",
    "resolve_build_metadata",
]
