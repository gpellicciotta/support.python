#!/usr/bin/env python3
"""Reusable command-line interface and logging harness for repository tools.

Provides standard action-oriented subcommand architecture, default help display on bare
invocation, unified help formatting with version headers, standard operational logging options,
and lifecycle banners (startup configuration and completion summary) per CLI and logging guidelines.
"""

from __future__ import annotations

import argparse
from dataclasses import dataclass
from pathlib import Path
import sys
import time
from typing import Any, Callable, NoReturn, Sequence

from _tool_common import (
    COPYRIGHT,
    PROJECT_VERSION,
    ToolLogger,
    get_full_version,
)

ActionHandler = Callable[..., int]
ParserConfigurator = Callable[[argparse.ArgumentParser], None]

DEFAULT_EXIT_CODES: dict[int, str] = {
    0: "success",
    1: "operational or runtime execution error",
    2: "invalid arguments or syntax errors",
}


@dataclass
class Action:
    """A named action/subcommand supported by the tool."""

    name: str
    description: str
    handler: ActionHandler | None = None
    detail: str = ""
    usage_suffix: str = "[options]"
    configure_parser: ParserConfigurator | None = None
    allow_unknown_args: bool = False


class ToolHarness:
    """Standardized CLI and logging harness enforcing the dev-guidelines conventions."""

    def __init__(
        self,
        name: str,
        description: str,
        version: str = PROJECT_VERSION,
        copyright: str = COPYRIGHT,
        default_log_file: Path | str | None = None,
        default_log_level: str = "INFO",
        exit_codes: dict[int, str] | None = None,
        examples: list[str] | None = None,
        detailed_help: str | None = None,
        fallback_action: str | None = None,
    ) -> None:
        self.name = name
        self.description = description
        self.version = version
        self.copyright = copyright
        self.default_log_file = Path(default_log_file).resolve() if default_log_file else None
        self.default_log_level = default_log_level
        self.exit_codes = dict(DEFAULT_EXIT_CODES)
        if exit_codes:
            self.exit_codes.update(exit_codes)
        self.examples = list(examples or [])
        self.detailed_help = detailed_help
        self.fallback_action = fallback_action
        self._actions: dict[str, Action] = {}
        self._global_args: list[tuple[tuple[Any, ...], dict[str, Any]]] = []

    def add_action(
        self,
        name: str,
        description: str,
        handler: ActionHandler | None = None,
        detail: str = "",
        usage_suffix: str = "[options]",
        configure_parser: ParserConfigurator | None = None,
        allow_unknown_args: bool = False,
    ) -> Action:
        """Register a subcommand action."""
        action = Action(
            name=name,
            description=description,
            handler=handler,
            detail=detail,
            usage_suffix=usage_suffix,
            configure_parser=configure_parser,
            allow_unknown_args=allow_unknown_args,
        )
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
        return f"{self.name} v{get_full_version(self.version)} - {self.copyright}"

    def format_help(self, verbose: bool = False) -> str:
        """Return standardized help screen per CLI guidelines."""
        lines = [
            self.format_version(),
            "",
            self.description,
            "",
            "Usage:",
        ]

        if self._actions:
            for action in self._actions.values():
                suffix = f" {action.usage_suffix}" if action.usage_suffix else ""
                lines.append(f"  {self.name} {action.name}{suffix}")
        else:
            lines.append(f"  {self.name} [options]")

        lines.extend(
            [
                f"  {self.name} version",
                f"  {self.name} help [--verbose]",
                "",
                "Actions:",
            ]
        )

        max_act_len = max([len(name) for name in self._actions] + [7])
        act_col = max(max_act_len + 2, 23)
        for name, action in self._actions.items():
            lines.append(f"  {name:<{act_col}}{action.description}")
        lines.append(f"  {'version':<{act_col}}show version information and exit")
        lines.append(f"  {'help':<{act_col}}show help message and exit (use --verbose for details)")

        lines.extend(
            [
                "",
                "Options:",
                "  -h, --help             show help message and exit",
                "  --version              show version information and exit",
                "  -v, --verbose          enable verbose output logging",
                "  --debug                enable debug output logging",
                "  --log-file PATH        append operational logs to specified file",
                f"  --log-level LEVEL      logging severity threshold (DEBUG, INFO, WARN, ERROR; default: {self.default_log_level})",
            ]
        )

        for g_args, g_kwargs in self._global_args:
            opts = ", ".join(arg for arg in g_args if isinstance(arg, str) and arg.startswith("-"))
            if g_kwargs.get("metavar"):
                opts = f"{opts} {g_kwargs['metavar']}"
            help_msg = g_kwargs.get("help", "")
            lines.append(f"  {opts:<23}{help_msg}")

        lines.extend(
            [
                "",
                "Exit codes:",
            ]
        )
        for code in sorted(self.exit_codes):
            desc = self.exit_codes[code]
            lines.append(f"  {code:<4}{desc}")

        if not verbose:
            return "\n".join(lines) + "\n"

        # Verbose additions
        lines.append("\nDetailed Action Descriptions:")
        for name, action in self._actions.items():
            detail_text = action.detail or action.description
            lines.append(f"  {name}")
            for d_line in detail_text.splitlines():
                lines.append(f"      {d_line}")

        if self.detailed_help:
            lines.append(f"\n{self.detailed_help.strip()}")

        if self.examples:
            lines.append("\nExamples:")
            for ex in self.examples:
                lines.append(f"  {ex}")

        return "\n".join(lines) + "\n"

    def format_action_help(self, action_name: str, verbose: bool = False) -> str:
        """Return standardized help screen for a specific subcommand."""
        action = self._actions[action_name]
        suffix = f" {action.usage_suffix}" if action.usage_suffix else ""
        lines = [
            self.format_version(),
            "",
        ]

        detail_text = action.detail or action.description
        if detail_text:
            lines.append(f"Detailed Action Description: {action_name}")
            for d_line in detail_text.splitlines():
                lines.append(f"  {d_line}")

        relevant_examples = [ex for ex in self.examples if action_name in ex.split()]
        if not relevant_examples:
            relevant_examples = [ex for ex in self.examples if action_name in ex]
        if relevant_examples:
            lines.append("")
            lines.append("Examples:")
            for ex in relevant_examples:
                lines.append(f"  {ex}")

        lines.extend(
            [
                "",
                "Usage:",
                f"  {self.name} {action_name}{suffix}",
                "",
                "Options:",
                "  -h, --help             show help message and exit",
                "  --version              show version information and exit",
                "  -v, --verbose          enable verbose output logging",
                "  --debug                enable debug output logging",
                "  --log-file PATH        append operational logs to specified file",
                f"  --log-level LEVEL      logging severity threshold (DEBUG, INFO, WARN, ERROR; default: {self.default_log_level})",
            ]
        )

        parser = self._build_parser(action_name)
        standard_dest = {"help", "version", "verbose", "debug", "log_file", "log_level"}
        for action_obj in parser._actions:
            if action_obj.dest not in standard_dest:
                opts = ", ".join(action_obj.option_strings)
                if opts:
                    lines.append(f"  {opts:<23}{action_obj.help or ''}")

        lines.extend(
            [
                "",
                "Exit codes:",
            ]
        )
        for code in sorted(self.exit_codes):
            desc = self.exit_codes[code]
            lines.append(f"  {code:<4}{desc}")

        return "\n".join(lines) + "\n"

    def _extract_early_logger(self, args: Sequence[str]) -> ToolLogger:
        """Construct a ToolLogger from raw args before full argument parsing completes."""
        log_file: Path | None = self.default_log_file
        log_level: str | None = None
        debug: bool = False
        verbose: bool = False

        i = 0
        n = len(args)
        while i < n:
            arg = args[i]
            if arg == "--":
                break
            if arg == "--log-file":
                if i + 1 < n:
                    log_file = Path(args[i + 1])
                    i += 2
                    continue
            elif arg.startswith("--log-file="):
                val = arg.split("=", 1)[1]
                log_file = Path(val) if val else None
            elif arg == "--log-level":
                if i + 1 < n:
                    log_level = args[i + 1].upper()
                    i += 2
                    continue
            elif arg.startswith("--log-level="):
                log_level = arg.split("=", 1)[1].upper()
            elif arg == "--debug":
                debug = True
            elif arg in ("-v", "--verbose"):
                verbose = True
            i += 1

        return ToolLogger(
            log_file=log_file,
            log_level=log_level,
            debug=debug,
            verbose=verbose,
        )

    def _build_parser(self, action_name: str | None = None) -> argparse.ArgumentParser:
        prog = f"{self.name} {action_name}" if action_name else self.name
        parser = argparse.ArgumentParser(prog=prog, description=self.description, add_help=False)
        parser.add_argument("-h", "--help", action="store_true")
        parser.add_argument("--version", action="store_true")
        parser.add_argument("-v", "--verbose", action="store_true")
        parser.add_argument("--debug", action="store_true")
        parser.add_argument("--log-file", type=str, default=str(self.default_log_file) if self.default_log_file else None)
        parser.add_argument(
            "--log-level",
            type=str.upper,
            choices=["DEBUG", "INFO", "WARN", "ERROR"],
            default=None,
        )
        for g_args, g_kwargs in self._global_args:
            parser.add_argument(*g_args, **g_kwargs)

        if action_name and action_name in self._actions:
            configurator = self._actions[action_name].configure_parser
            if configurator:
                configurator(parser)

        return parser

    def create_logger(self, args: argparse.Namespace) -> ToolLogger:
        """Construct standard ToolLogger configured from parsed arguments."""
        log_path = Path(args.log_file).resolve() if args.log_file else self.default_log_file
        return ToolLogger(
            log_file=log_path,
            log_level=args.log_level,
            debug=getattr(args, "debug", False),
            verbose=getattr(args, "verbose", False),
        )

    def log_startup(
        self,
        logger: ToolLogger,
        action: str,
        extra: dict[str, Any] | None = None,
    ) -> None:
        """Emit single multi-line startup message per logging guidelines."""
        lines = [
            f"Starting {self.name} v{get_full_version(self.version)} with configuration:",
            f"- Command: {action}",
            f"- Log file: {logger.log_file or 'none'}",
            f"- Log level: {logger.effective_level}",
            f"- Verbose: {str(logger.verbose).lower()}",
        ]
        if extra:
            for key, val in extra.items():
                lines.append(f"- {key}: {val}")
        logger.info("\n".join(lines))

    def log_completion(
        self,
        logger: ToolLogger,
        action: str,
        exit_code: int,
        started_at: float,
    ) -> None:
        """Emit completion summary upon exit per logging guidelines."""
        duration = time.monotonic() - started_at
        status = "succeeded" if exit_code == 0 else "failed"
        lvl = "INFO" if exit_code == 0 else "ERROR"
        logger.log(
            f"Finished {self.name} {action} in {duration:.1f}s with status: {status}",
            level=lvl,
        )

    def run(
        self,
        argv: Sequence[str] | None = None,
        extra_startup: dict[str, Any] | None = None,
    ) -> int:
        """Execute the requested command line, handling standard actions and logging."""
        raw_args = list(sys.argv[1:] if argv is None else argv)

        # Default action when zero arguments are passed: show help text
        if not raw_args:
            print(self.format_help(verbose=False), end="")
            return 0

        first = raw_args[0]
        rest = raw_args[1:]

        # Handle top-level help and version subcommands / options
        if first in ("version", "--version"):
            print(self.format_version())
            return 0

        if first in ("help", "-h", "--help"):
            is_verbose = any(arg in ("-v", "--verbose") for arg in rest)
            target_actions = [arg for arg in rest if not arg.startswith("-")]
            if target_actions and target_actions[0] in self._actions:
                print(self.format_action_help(target_actions[0], verbose=is_verbose), end="")
                return 0
            print(self.format_help(verbose=is_verbose), end="")
            return 0

        action_name = first
        action_args = rest

        if action_name not in self._actions:
            if self.fallback_action and self.fallback_action in self._actions and not first.startswith("-"):
                action_name = self.fallback_action
                action_args = raw_args
            else:
                early_logger = self._extract_early_logger(raw_args)
                usage = f"Usage: {self.name} {{help|version|{'|'.join(self._actions.keys())}}} [options]"
                early_logger.error(f"Unknown subcommand: '{first}'\n{usage}")
                early_logger.close()
                return 2

        action = self._actions[action_name]
        parser = self._build_parser(action_name)

        if getattr(parser, "error", None) is not None:
            orig_error = parser.error
            qual = getattr(orig_error, "__qualname__", "")
            if getattr(orig_error, "_is_harness_handler", False) or qual.startswith("ArgumentParser."):

                def report_error(message: str) -> NoReturn:
                    early_logger = self._extract_early_logger(raw_args)
                    suffix = f" {action.usage_suffix}" if action.usage_suffix else " [options]"
                    action_usage = f"Usage: {self.name} {action_name}{suffix}" if action_name else f"Usage: {self.name} [options]"
                    early_logger.error(f"{message}\n{action_usage}")
                    early_logger.close()
                    sys.exit(2)

                report_error._is_harness_handler = True  # type: ignore[attr-defined]
                parser.error = report_error  # type: ignore[method-assign]

        try:
            if action.allow_unknown_args:
                args, passthrough = parser.parse_known_args(action_args)
            else:
                args = parser.parse_args(action_args)
                passthrough = []
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
            import inspect

            sig = inspect.signature(action.handler)
            param_count = len(sig.parameters)
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
