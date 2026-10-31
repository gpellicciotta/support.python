#!/usr/bin/env python3
# Copyright (c) Giovanni Pellicciotta
"""Cross-platform process termination script.

Safely terminates running processes by PID while explicitly protecting the
current script and all of its ancestor processes (such as runner shells,
parent agents, and orchestrators) from accidental termination.
"""

from __future__ import annotations

import argparse
import os

from pathlib import Path
import platform
import signal
import subprocess
import sys
from typing import Sequence

# Reconfigure stdout/stderr to UTF-8 on Windows
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

LIB_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(LIB_DIR))
try:
    from _tool_common import ToolHarness, ToolLogger  # noqa: E402
except ImportError as exc:
    LIB_IMPORT_ERROR: ImportError | None = exc
    ToolHarness = object  # type: ignore[assignment,misc]
    ToolLogger = object  # type: ignore[assignment,misc]
else:
    LIB_IMPORT_ERROR = None


TOOL_NAME = "kill-processes"
DESCRIPTION = "Safely terminates processes by PID while protecting the script and its ancestor processes."

KILL_DETAIL = """Terminates each listed process ID in turn while protecting the current script,
its parent process, and all ancestor processes from accidental termination.
On POSIX systems, sends SIGTERM by default and SIGKILL when --force is passed.
On Windows systems, executes 'taskkill /PID {pid}' and appends '/F' when --force is passed.
The action name may be omitted: 'kill-processes {pid}...' runs 'kill'."""

EXAMPLES = [
    "kill-processes 1234 5678",
    "kill-processes kill 1234 --force",
    "kill-processes 1234 --log-file .plan/logs/process.log --log-level INFO",
]

EXIT_CODES = {
    0: "success (processes killed or protected PIDs safely skipped)",
    1: "operational failure during process termination",
    2: "invalid arguments or syntax errors",
}


def format_fallback_indicator(level: str) -> str:
    """Return a severity indicator padded to 11 characters without depending on the shared script modules."""
    return f"{'**[' + level.strip().upper() + ']**':<11}"


def parse_pid(value: str) -> int:
    """Convert a command-line value to a process ID, rejecting non-positive or non-numeric values."""
    try:
        pid = int(value)
    except ValueError:
        raise argparse.ArgumentTypeError(f"invalid process ID: '{value}'") from None
    if pid <= 0:
        raise argparse.ArgumentTypeError(f"invalid process ID: '{value}'")
    return pid


def windows_parent_map() -> dict[int, int]:
    """Map every running process ID to its parent ID using the Win32 process snapshot (standard library only)."""
    import ctypes
    from ctypes import wintypes

    class ProcessEntry(ctypes.Structure):
        _fields_ = [
            ("dwSize", wintypes.DWORD),
            ("cntUsage", wintypes.DWORD),
            ("th32ProcessID", wintypes.DWORD),
            ("th32DefaultHeapID", ctypes.c_size_t),
            ("th32ModuleID", wintypes.DWORD),
            ("cntThreads", wintypes.DWORD),
            ("th32ParentProcessID", wintypes.DWORD),
            ("pcPriClassBase", ctypes.c_long),
            ("dwFlags", wintypes.DWORD),
            ("szExeFile", ctypes.c_wchar * 260),
        ]

    kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
    kernel32.CreateToolhelp32Snapshot.restype = wintypes.HANDLE
    kernel32.CreateToolhelp32Snapshot.argtypes = [wintypes.DWORD, wintypes.DWORD]
    kernel32.Process32FirstW.argtypes = [wintypes.HANDLE, ctypes.POINTER(ProcessEntry)]
    kernel32.Process32NextW.argtypes = [wintypes.HANDLE, ctypes.POINTER(ProcessEntry)]
    kernel32.CloseHandle.argtypes = [wintypes.HANDLE]
    snapshot = kernel32.CreateToolhelp32Snapshot(0x2, 0)  # TH32CS_SNAPPROCESS
    parents: dict[int, int] = {}
    try:
        entry = ProcessEntry()
        entry.dwSize = ctypes.sizeof(ProcessEntry)
        more = kernel32.Process32FirstW(snapshot, ctypes.byref(entry))
        while more:
            parents[entry.th32ProcessID] = entry.th32ParentProcessID
            more = kernel32.Process32NextW(snapshot, ctypes.byref(entry))
    finally:
        kernel32.CloseHandle(snapshot)
    return parents


def get_process_hierarchy(start_pid: int) -> set[int]:
    """Retrieve the full hierarchy of parent process IDs up to the system root.

    Args:
        start_pid: The starting process ID from which to build the hierarchy.

    Returns:
        A set containing start_pid and all its ancestor PIDs. If resolution fails,
        returns at least start_pid and any detectable immediate parent.
    """
    parents = {start_pid}

    try:
        import psutil

        proc = psutil.Process(start_pid)
        for parent in proc.parents():
            parents.add(parent.pid)
        return parents
    except ImportError:
        pass
    except Exception:
        pass

    try:
        if start_pid == os.getpid():
            parents.add(os.getppid())
    except Exception:
        pass

    if platform.system() == "Windows":
        try:
            parent_map = windows_parent_map()
            curr = start_pid
            seen = {curr}
            while parent_map.get(curr, 0) > 0 and parent_map[curr] not in seen:
                curr = parent_map[curr]
                seen.add(curr)
                parents.add(curr)
        except Exception:
            pass
    else:
        curr = start_pid
        while curr > 1:
            try:
                with open(f"/proc/{curr}/stat", "r", encoding="utf-8") as f:
                    ppid = int(f.read().split()[3])
                    if ppid in parents or ppid <= 0:
                        break
                    parents.add(ppid)
                    curr = ppid
            except Exception:
                break

    return parents


def safe_kill(pids: Sequence[int], logger: ToolLogger, force: bool = False) -> bool:
    """Terminate a list of process IDs safely, protecting parent and ancestor processes.

    Args:
        pids: A sequence of process IDs to terminate.
        logger: The process-wide logger receiving all progress and diagnostic messages.
        force: If True, forcefully terminate processes (SIGKILL on POSIX, taskkill /F on Windows).

    Returns:
        True if all target processes were successfully terminated or safely skipped,
        False if any unskipped process failed to terminate.
    """
    protected_pids = get_process_hierarchy(os.getpid())
    logger.debug_msg(f"Protected process hierarchy: {sorted(protected_pids)}")

    detail_level = "INFO" if logger.verbose else "DEBUG"
    system = platform.system()
    all_succeeded = True

    for pid in pids:
        if pid in protected_pids:
            logger.warn(f"Skipping protected PID {pid} (current script or ancestor process).")
            continue

        try:
            if system == "Windows":
                cmd = ["taskkill", "/PID", str(pid)]
                if force:
                    cmd.append("/F")
                logger.log(f"Executing: {' '.join(cmd)}", level=detail_level)
                subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            else:
                sig = signal.SIGKILL if force else signal.SIGTERM
                logger.log(f"Sending signal {sig} to PID {pid}", level=detail_level)
                os.kill(pid, sig)
            logger.info(f"Killed PID {pid}")
        except ProcessLookupError:
            logger.warn(f"PID {pid} not found.")
        except subprocess.CalledProcessError:
            logger.error(f"Failed to kill PID {pid}.")
            all_succeeded = False
        except PermissionError:
            logger.error(f"Permission denied to kill PID {pid}.")
            all_succeeded = False
        except Exception as e:
            logger.error(f"Error killing PID {pid}: {e}")
            all_succeeded = False

    return all_succeeded


def configure_kill_parser(parser: argparse.ArgumentParser) -> None:
    """Add the positional process ID arguments of the kill action."""
    parser.add_argument("pids", nargs="+", type=parse_pid, metavar="pid", help="One or more process IDs to terminate.")


def run_kill(args: argparse.Namespace, logger: ToolLogger) -> int:
    """Handle the kill action, returning 0 when all targets were killed or skipped and 1 otherwise."""
    return 0 if safe_kill(args.pids, logger, force=args.force) else 1


def build_harness() -> ToolHarness:
    """Construct the CLI harness declaring the kill action and its options."""
    harness = ToolHarness(
        name=TOOL_NAME,
        description=DESCRIPTION,
        exit_codes=EXIT_CODES,
        examples=EXAMPLES,
        fallback_action="kill",
    )
    harness.add_action(
        "kill",
        "terminate processes by PID (default action)",
        handler=run_kill,
        detail=KILL_DETAIL,
        usage_suffix="{pid}... [options]",
        configure_parser=configure_kill_parser,
    )
    harness.add_global_argument("-f", "--force", action="store_true", help="force termination (SIGKILL or taskkill /F)")
    return harness


TOP_LEVEL_TOKENS = {"help", "version", "-h", "--help", "--version"}
VALUE_OPTIONS = {"--log-file", "--log-level"}


def normalize_argv(argv: Sequence[str]) -> list[str]:
    """Rewrite argv so the harness accepts every supported argument arrangement.

    Help and version flags anywhere in a kill invocation map to action-scoped help or version
    actions, so they never require PIDs. A leading option without an action selects the implicit
    kill action, so 'kill-processes --debug {pid}' works like 'kill-processes {pid} --debug'.
    """
    args = list(argv)
    if not args or args[0] in TOP_LEVEL_TOKENS:
        return args

    flags: set[str] = set()
    skip_value = False
    for token in args[1:] if args[0] == "kill" else args:
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
        return ["help", "kill", "--verbose"] if flags & {"-v", "--verbose"} else ["help", "kill"]
    if args[0].startswith("-"):
        return ["kill", *args]
    return args


def main(argv: Sequence[str] | None = None) -> int:
    """Parse command-line arguments and execute the requested action."""
    if LIB_IMPORT_ERROR is not None:
        print(
            f"{format_fallback_indicator('ERROR')} Cannot load the script harness ({LIB_DIR}): {LIB_IMPORT_ERROR}",
            file=sys.stderr,
        )
        return 1
    return build_harness().run(normalize_argv(sys.argv[1:] if argv is None else argv))


if __name__ == "__main__":
    sys.exit(main())
