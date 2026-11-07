"""Cross-platform OS process hierarchy inspection, liveness checks, and safe termination."""

from __future__ import annotations

from datetime import datetime
import json
import os
from pathlib import Path
import signal
import subprocess
import sys
from typing import Any, Sequence

from .logging import CliLogger


def windows_parent_map() -> dict[int, int]:
    """Map every running process ID to its parent ID using the Win32 process snapshot.

    Uses the standard library ``ctypes`` interface to ``CreateToolhelp32Snapshot``
    so callers do not require third-party packages or external shell processes.

    Returns:
        Dictionary mapping each running process ID to its parent process ID.

    Raises:
        OSError: If the Win32 snapshot API is unavailable or fails.
    """
    import ctypes
    from ctypes import wintypes

    class ProcessEntry(ctypes.Structure):
        """Win32 PROCESSENTRY32W structure for toolhelp process enumeration."""

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
    kernel32.Process32FirstW.restype = wintypes.BOOL
    kernel32.Process32NextW.argtypes = [wintypes.HANDLE, ctypes.POINTER(ProcessEntry)]
    kernel32.Process32NextW.restype = wintypes.BOOL
    kernel32.CloseHandle.argtypes = [wintypes.HANDLE]
    kernel32.CloseHandle.restype = wintypes.BOOL

    snapshot = kernel32.CreateToolhelp32Snapshot(0x2, 0)  # TH32CS_SNAPPROCESS
    invalid_handle = wintypes.HANDLE(-1).value
    if not snapshot or snapshot == invalid_handle:
        raise ctypes.WinError(ctypes.get_last_error())

    parents: dict[int, int] = {}
    try:
        entry = ProcessEntry()
        entry.dwSize = ctypes.sizeof(ProcessEntry)
        more = kernel32.Process32FirstW(snapshot, ctypes.byref(entry))
        while more:
            parents[int(entry.th32ProcessID)] = int(entry.th32ParentProcessID)
            more = kernel32.Process32NextW(snapshot, ctypes.byref(entry))
    finally:
        kernel32.CloseHandle(snapshot)
    return parents


def _powershell_parent_map() -> dict[int, int]:
    """Query Win32_Process via PowerShell as a fallback when toolhelp snapshot fails."""
    result = subprocess.run(
        [
            "powershell.exe",
            "-NoProfile",
            "-NonInteractive",
            "-Command",
            "Get-CimInstance Win32_Process | Select-Object ProcessId,ParentProcessId | ConvertTo-Json -Compress",
        ],
        capture_output=True,
        text=True,
        check=True,
        timeout=15,
    )
    rows = json.loads(result.stdout)
    if isinstance(rows, dict):
        rows = [rows]
    return {int(row["ProcessId"]): int(row["ParentProcessId"]) for row in rows}


def get_process_hierarchy(start_pid: int) -> set[int]:
    """Return ``start_pid`` and all of its ancestor process IDs, failing closed if inspection fails.

    Queries the OS process table using only the Python standard library:
    Win32 ``CreateToolhelp32Snapshot`` (with PowerShell CIM fallback) on Windows,
    and ``ps -A -o pid=,ppid=`` (with ``/proc/<pid>/stat`` fallback) on POSIX.

    Args:
        start_pid: The starting process ID from which to walk up the parent tree.

    Returns:
        Set of process IDs containing ``start_pid`` and every resolved ancestor PID.

    Raises:
        OSError: If ``start_pid`` is non-positive or its ancestors cannot be inspected.
    """
    if start_pid <= 0:
        raise OSError(f"Cannot resolve ancestors of non-positive PID {start_pid}")

    if sys.platform == "win32":
        parents: dict[int, int] = {}
        try:
            parents = windows_parent_map()
        except Exception:
            parents = {}
        if start_pid not in parents:
            try:
                parents = _powershell_parent_map()
            except Exception as exc:
                raise OSError(f"Cannot resolve ancestors of PID {start_pid}") from exc
    else:
        try:
            result = subprocess.run(
                ["ps", "-A", "-o", "pid=,ppid="],
                capture_output=True,
                text=True,
                check=True,
                timeout=5,
            )
            parents = {int(pid): int(parent) for pid, parent in (line.split() for line in result.stdout.splitlines())}
        except FileNotFoundError:
            parents = {}
            current = start_pid
            while current > 0 and current not in parents:
                try:
                    stat = Path(f"/proc/{current}/stat").read_text(encoding="utf-8")
                    # Process names can contain spaces and closing parentheses.
                    parent = int(stat.rsplit(")", 1)[1].split()[1])
                except (OSError, IndexError, ValueError) as exc:
                    if current == start_pid:
                        raise OSError(f"Cannot resolve ancestors of PID {start_pid}") from exc
                    break
                parents[current] = parent
                current = parent
        except Exception as exc:
            raise OSError(f"Cannot resolve ancestors of PID {start_pid}") from exc

    protected: set[int] = set()
    current = start_pid
    while current > 0 and current not in protected:
        protected.add(current)
        if current not in parents:
            if current == start_pid:
                raise OSError(f"Cannot resolve ancestors of PID {current}")
            break  # An exited ancestor remains protected, but has no live parents.
        current = parents[current]
    if start_pid == os.getpid():
        protected.add(os.getppid())
    return protected


def get_process_start_time(pid: int) -> datetime | None:
    """Retrieve the creation time of ``pid`` as a naive local ``datetime``.

    Args:
        pid: The OS process identifier.

    Returns:
        Process start time as a naive local ``datetime``, or ``None`` if the process
        does not exist or the query fails.
    """
    if pid <= 0:
        return None
    if sys.platform == "win32":
        try:
            import ctypes
            from ctypes import wintypes

            class FILETIME(ctypes.Structure):
                """Windows FILETIME 64-bit timestamp structure."""

                _fields_ = [("dwLowDateTime", wintypes.DWORD), ("dwHighDateTime", wintypes.DWORD)]

            process_query_limited_information = 0x1000
            handle = ctypes.windll.kernel32.OpenProcess(process_query_limited_information, False, pid)
            if not handle:
                return None
            try:
                ct, et, kt, ut = FILETIME(), FILETIME(), FILETIME(), FILETIME()
                success = ctypes.windll.kernel32.GetProcessTimes(
                    handle,
                    ctypes.byref(ct),
                    ctypes.byref(et),
                    ctypes.byref(kt),
                    ctypes.byref(ut),
                )
                if not success:
                    return None
                ticks = (ct.dwHighDateTime << 32) + ct.dwLowDateTime
                unix_ts = (ticks - 116444736000000000) / 10000000.0
                return datetime.fromtimestamp(unix_ts)
            finally:
                ctypes.windll.kernel32.CloseHandle(handle)
        except Exception:
            return None

    try:
        proc_stat = Path(f"/proc/{pid}/stat")
        if proc_stat.is_file():
            btime = 0
            try:
                for line in Path("/proc/stat").read_text(encoding="utf-8", errors="replace").splitlines():
                    if line.startswith("btime "):
                        btime = int(line.split()[1])
                        break
            except Exception:
                pass
            raw_stat = proc_stat.read_text(encoding="utf-8", errors="replace")
            after_comm = raw_stat.rsplit(")", 1)[1].split()
            if len(after_comm) > 19 and btime > 0:
                clk_tck = os.sysconf(os.sysconf_names["SC_CLK_TCK"]) if hasattr(os, "sysconf") else 100
                starttime_jiffies = int(after_comm[19])
                start_ts = btime + (starttime_jiffies / clk_tck)
                return datetime.fromtimestamp(start_ts)
        res = subprocess.run(
            ["ps", "-p", str(pid), "-o", "lstart="],
            capture_output=True,
            text=True,
            timeout=2,
        )
        if res.returncode == 0 and res.stdout.strip():
            return datetime.strptime(res.stdout.strip(), "%a %b %d %H:%M:%S %Y")
    except Exception:
        pass
    return None


def _to_naive_local(dt: datetime) -> datetime:
    """Convert a datetime to a naive local datetime for start-time comparison."""
    if dt.tzinfo is not None:
        return dt.astimezone().replace(tzinfo=None)
    return dt


def is_process_alive(
    pid: int,
    expected_start: datetime | None = None,
    slack_seconds: float = 2.0,
) -> bool:
    """Check whether ``pid`` is currently running and optionally matches ``expected_start``.

    Args:
        pid: The OS process identifier.
        expected_start: Optional expected creation time to guard against PID reuse.
        slack_seconds: Maximum allowed difference in seconds between actual and expected start times.

    Returns:
        ``True`` if the process is alive (and within ``slack_seconds`` of ``expected_start``
        when provided), ``False`` otherwise.
    """
    if pid <= 0:
        return False

    if sys.platform == "win32":
        try:
            import ctypes
            from ctypes import wintypes

            process_query_limited_information = 0x1000
            handle = ctypes.windll.kernel32.OpenProcess(process_query_limited_information, False, pid)
            if not handle:
                return False
            try:
                exit_code = wintypes.DWORD()
                if ctypes.windll.kernel32.GetExitCodeProcess(handle, ctypes.byref(exit_code)):
                    if exit_code.value != 259:  # STILL_ACTIVE = 259
                        return False
            finally:
                ctypes.windll.kernel32.CloseHandle(handle)
        except Exception:
            return False
    else:
        try:
            os.kill(pid, 0)
        except OSError:
            return False

    if expected_start is not None:
        actual_start = get_process_start_time(pid)
        if actual_start is not None:
            exp = _to_naive_local(expected_start)
            act = _to_naive_local(actual_start)
            if abs((act - exp).total_seconds()) > slack_seconds:
                return False

    return True


def terminate_process(pid: int, force: bool = False) -> None:
    """Send a termination signal to a single positive PID without ancestor protection.

    Callers must verify that ``pid`` is not the current process or an ancestor
    before invoking this helper (or use :func:`safe_kill` instead).

    Args:
        pid: Positive process identifier to terminate.
        force: If ``True``, use ``taskkill /F`` on Windows or ``SIGKILL`` on POSIX.

    Raises:
        ValueError: If ``pid <= 0``.
        subprocess.CalledProcessError: If ``taskkill`` fails on Windows.
        OSError: If ``os.kill`` fails on POSIX.
    """
    if pid <= 0:
        raise ValueError("Process IDs must be positive")
    if sys.platform == "win32":
        cmd = ["taskkill", "/PID", str(pid)] + (["/F"] if force else [])
        subprocess.run(cmd, check=True, capture_output=True, timeout=15)
    else:
        sig = getattr(signal, "SIGKILL", 9) if force else signal.SIGTERM
        os.kill(pid, sig)


def terminate_process_tree(pid: int) -> bool:
    """Terminate a process and its child subprocess tree.

    Uses ``taskkill /F /T /PID`` on Windows and forceful termination via
    :func:`terminate_process` on POSIX platforms.

    Args:
        pid: The root process identifier to terminate.

    Returns:
        ``True`` if termination succeeded, ``False`` for non-positive PIDs or errors.
    """
    if pid <= 0:
        return False
    try:
        if sys.platform == "win32":
            res = subprocess.run(
                ["taskkill", "/F", "/T", "/PID", str(pid)],
                capture_output=True,
                text=True,
                timeout=5,
            )
            return res.returncode == 0
        terminate_process(pid, force=True)
        return True
    except Exception:
        return False


def _emit_log(logger: Any, level: str, message: str) -> None:
    """Dispatch a log message to a CliLogger, ToolLogger, or standard logging.Logger."""
    if logger is None:
        return
    clean = level.upper()
    if clean == "DEBUG":
        if hasattr(logger, "debug_msg") and callable(logger.debug_msg):
            logger.debug_msg(message)
        elif hasattr(logger, "debug") and callable(logger.debug):
            logger.debug(message)
        elif hasattr(logger, "log") and callable(logger.log):
            logger.log(message, level="DEBUG")
    elif clean in ("WARN", "WARNING"):
        if hasattr(logger, "warn") and callable(logger.warn):
            logger.warn(message)
        elif hasattr(logger, "warning") and callable(logger.warning):
            logger.warning(message)
        elif hasattr(logger, "log") and callable(logger.log):
            logger.log(message, level="WARN")
    elif clean == "ERROR":
        if hasattr(logger, "error") and callable(logger.error):
            logger.error(message)
        elif hasattr(logger, "log") and callable(logger.log):
            logger.log(message, level="ERROR")
    else:
        if hasattr(logger, "info") and callable(logger.info):
            logger.info(message)
        elif hasattr(logger, "log") and callable(logger.log):
            logger.log(message, level="INFO")


def safe_kill(
    pids: Sequence[int],
    logger: Any = None,
    force: bool = False,
) -> bool:
    """Terminate a sequence of process IDs while protecting the current process and its ancestors.

    Args:
        pids: Sequence of process IDs to terminate.
        logger: Optional logger instance (:class:`~support_python.logging.CliLogger`,
            ``ToolLogger``, or standard ``logging.Logger``). Defaults to a new :class:`CliLogger`.
        force: If ``True``, forcefully terminate targets (``SIGKILL`` or ``taskkill /F``).

    Returns:
        ``True`` if all target processes were terminated or safely skipped (protected or
        already absent), ``False`` if ancestor resolution or any target termination failed.
    """
    active_logger = logger if logger is not None else CliLogger()
    try:
        protected_pids = get_process_hierarchy(os.getpid())
    except Exception as exc:
        _emit_log(active_logger, "ERROR", f"Cannot inspect protected process hierarchy: {exc}")
        return False

    _emit_log(active_logger, "DEBUG", f"Protected process hierarchy: {sorted(protected_pids)}")
    all_succeeded = True

    for pid in pids:
        if pid in protected_pids:
            _emit_log(
                active_logger,
                "WARN",
                f"Skipping protected PID {pid} (current script or ancestor process).",
            )
            continue

        try:
            terminate_process(pid, force=force)
            _emit_log(active_logger, "INFO", f"Killed PID {pid}")
        except ProcessLookupError:
            _emit_log(active_logger, "WARN", f"PID {pid} not found.")
        except subprocess.CalledProcessError as exc:
            detail = exc.stderr or exc.stdout or ""
            if isinstance(detail, bytes):
                detail = detail.decode(errors="replace")
            detail_str = str(detail).strip()
            suffix = f": {detail_str}" if detail_str else "."
            _emit_log(active_logger, "ERROR", f"Failed to kill PID {pid}{suffix}")
            all_succeeded = False
        except PermissionError:
            _emit_log(active_logger, "ERROR", f"Permission denied to kill PID {pid}.")
            all_succeeded = False
        except Exception as exc:
            _emit_log(active_logger, "ERROR", f"Error killing PID {pid}: {exc}")
            all_succeeded = False

    return all_succeeded


__all__ = [
    "get_process_hierarchy",
    "get_process_start_time",
    "is_process_alive",
    "safe_kill",
    "terminate_process",
    "terminate_process_tree",
    "windows_parent_map",
]
