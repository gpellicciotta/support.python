"""Command-line interface for cross-platform process listing and ancestor-protected termination."""

from __future__ import annotations

import argparse
from datetime import datetime
import sys
from typing import Sequence

from ..cli import ToolHarness
from ..durations import parse_date_or_datetime
from ..logging import CliLogger
from .. import processes
from ..processes import list_processes, safe_kill
from ..tables import render_output

TOOL_NAME = "processes"
DESCRIPTION = "Safely terminate processes by PID and list running processes with hierarchy, path, and time filters."
KILL_DETAIL = (
    "Terminates each listed process ID in turn while protecting the current process and all ancestor processes. "
    "With --dry-run, reports each PID it would kill or skip as protected, and terminates nothing."
)
LIST_DETAIL = "Lists running processes with optional filters for cwd, open paths, start timestamps, and hierarchy trees."
EXAMPLES = [
    "processes kill 1234 5678",
    "processes kill 1234 --force",
    "processes kill 1234 5678 --dry-run",
    "processes list --cwd /path/to/workdir",
    "processes list --open-path /path/to/file.txt --format json",
    "processes list --descendants-of 1234",
]
EXIT_CODES = {
    0: "success (processes listed, killed, or protected PIDs safely skipped)",
    1: "operational failure during process inspection or termination",
    2: "invalid arguments or syntax errors",
}
TOP_LEVEL_TOKENS = {"help", "version", "-h", "--help", "--version"}
VALUE_OPTIONS = {
    "--log-file",
    "--log-level",
    "--cwd",
    "--open-path",
    "--started-before",
    "--started-after",
    "--ancestors-of",
    "--descendants-of",
    "--format",
}


def parse_pid(value: str) -> int:
    """Convert a command-line string to a positive integer process ID."""
    if not value.strip().isdigit() or int(value) <= 0:
        raise argparse.ArgumentTypeError(f"invalid process ID: '{value}'")
    return int(value)


def parse_timestamp(value: str) -> datetime:
    """Parse an ISO-8601 or date/datetime command-line filter string into a naive local datetime."""
    parsed = parse_date_or_datetime(value)
    if parsed is not None:
        return parsed
    try:
        dt = datetime.fromisoformat(value.strip().removesuffix("Z") + ("+00:00" if value.strip().endswith("Z") else ""))
    except ValueError:
        raise argparse.ArgumentTypeError(f"invalid timestamp: '{value}'") from None
    return dt.astimezone().replace(tzinfo=None) if dt.tzinfo is not None else dt


def configure_kill_parser(parser: argparse.ArgumentParser) -> None:
    """Register positional process IDs and termination flags for the ``kill`` subcommand."""
    parser.add_argument("pids", nargs="+", type=parse_pid, metavar="pid", help="One or more process IDs to terminate.")
    parser.add_argument("-f", "--force", action="store_true", help="Force termination (SIGKILL or taskkill /F).")
    parser.add_argument("--dry-run", action="store_true", help="Report the PIDs that would be killed; terminate nothing.")


def configure_list_parser(parser: argparse.ArgumentParser) -> None:
    """Register filter and output flags for the ``list`` subcommand."""
    parser.add_argument("--cwd", type=str, default=None, metavar="PATH", help="Filter processes by working directory.")
    parser.add_argument("--open-path", type=str, default=None, metavar="PATH", help="Filter processes holding an open path.")
    parser.add_argument("--started-before", type=parse_timestamp, default=None, metavar="TIMESTAMP", help="Upper start-time bound.")
    parser.add_argument("--started-after", type=parse_timestamp, default=None, metavar="TIMESTAMP", help="Lower start-time bound.")
    parser.add_argument("--ancestors-of", type=parse_pid, default=None, metavar="PID", help="Filter ancestors of PID.")
    parser.add_argument("--descendants-of", type=parse_pid, default=None, metavar="PID", help="Filter descendants of PID.")
    ToolHarness.add_format_option(parser)


def report_kill_plan(pids: Sequence[int], logger: CliLogger) -> bool:
    """Report whether each PID would be killed or skipped as protected, without terminating anything."""
    try:
        protected_pids = processes.get_process_hierarchy(processes.os.getpid())
    except Exception as exc:
        logger.error(f"Cannot inspect protected process hierarchy: {exc}")
        return False
    for pid in pids:
        if pid in protected_pids:
            logger.warning(f"Would skip protected PID {pid} (current script or ancestor process).")
        else:
            logger.info(f"Would kill PID {pid}")
    return True


def run_kill(args: argparse.Namespace, logger: CliLogger) -> int:
    """Execute the ``kill`` subcommand."""
    if args.dry_run:
        return 0 if report_kill_plan(args.pids, logger) else 1
    return 0 if safe_kill(args.pids, logger=logger, force=args.force) else 1


def run_list(args: argparse.Namespace, logger: CliLogger) -> int:
    """Execute the ``list`` subcommand."""
    matched = list_processes(
        cwd=args.cwd,
        open_path=args.open_path,
        started_before=args.started_before,
        started_after=args.started_after,
        ancestors_of=args.ancestors_of,
        descendants_of=args.descendants_of,
    )
    logger.debug_msg(f"Matched {len(matched)} process(es)")
    render_output(matched, output_format="json" if args.format == "json" else "table")
    return 0


def build_harness() -> ToolHarness:
    """Construct the :class:`ToolHarness` for the ``processes`` CLI."""
    harness = ToolHarness(name=TOOL_NAME, description=DESCRIPTION, exit_codes=EXIT_CODES, examples=EXAMPLES, fallback_action="kill")
    harness.add_action(
        "kill",
        "terminate processes by PID",
        handler=run_kill,
        detail=KILL_DETAIL,
        usage_suffix="{pid}... [options]",
        configure_parser=configure_kill_parser,
    )
    harness.add_action(
        "list",
        "list running processes with optional filters",
        handler=run_list,
        detail=LIST_DETAIL,
        usage_suffix="[options]",
        configure_parser=configure_list_parser,
    )
    return harness


def normalize_argv(argv: Sequence[str]) -> list[str]:
    """Normalize command-line arguments so implicit ``kill`` and action-scoped help/version work consistently."""
    args = list(argv)
    if not args or args[0] in TOP_LEVEL_TOKENS:
        return args
    action = args[0] if args[0] in ("kill", "list") else "kill"
    flags, skip_value = set(), False
    for token in args[1:] if args[0] in ("kill", "list") else args:
        if skip_value:
            skip_value = False
        elif token == "--":
            break
        elif token in VALUE_OPTIONS:
            skip_value = True
        else:
            flags.add(token)
    if "--version" in flags:
        return ["version"]
    if flags & {"-h", "--help"}:
        return ["help", action, "--verbose"] if flags & {"-v", "--verbose"} else ["help", action]
    return ["kill", *args] if args[0] not in ("kill", "list") else args


def main(argv: Sequence[str] | None = None) -> int:
    """Parse command-line arguments and execute the requested ``processes`` subcommand."""
    raw = list(sys.argv[1:] if argv is None else argv)
    return build_harness().run(normalize_argv(raw))


__all__ = [
    "DESCRIPTION",
    "EXAMPLES",
    "EXIT_CODES",
    "TOOL_NAME",
    "build_harness",
    "configure_kill_parser",
    "configure_list_parser",
    "main",
    "normalize_argv",
    "parse_pid",
    "parse_timestamp",
    "report_kill_plan",
    "run_kill",
    "run_list",
]
