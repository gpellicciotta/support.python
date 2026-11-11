"""Cross-platform OS process hierarchy inspection, liveness checks, and safe termination."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
import json
import os
from pathlib import Path
import signal
import subprocess
import sys
from typing import Any, Sequence

from .logging import CliLogger


@dataclass(frozen=True)
class ProcessInfo:
    """Metadata describing a running operating system process."""

    pid: int
    ppid: int
    name: str = ""
    started: datetime | None = None
    cwd: str | None = None


def windows_process_snapshot() -> dict[int, tuple[int, str]]:
    """Map every running process ID to ``(parent_pid, exe_name)`` using the Win32 snapshot."""
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

    entries: dict[int, tuple[int, str]] = {}
    try:
        entry = ProcessEntry()
        entry.dwSize = ctypes.sizeof(ProcessEntry)
        more = kernel32.Process32FirstW(snapshot, ctypes.byref(entry))
        while more:
            entries[int(entry.th32ProcessID)] = (int(entry.th32ParentProcessID), str(entry.szExeFile))
            more = kernel32.Process32NextW(snapshot, ctypes.byref(entry))
    finally:
        kernel32.CloseHandle(snapshot)
    return entries


def windows_parent_map() -> dict[int, int]:
    """Map every running process ID to its parent ID using the Win32 process snapshot.

    Uses the standard library ``ctypes`` interface to ``CreateToolhelp32Snapshot``
    so callers do not require third-party packages or external shell processes.

    Returns:
        Dictionary mapping each running process ID to its parent process ID.

    Raises:
        OSError: If the Win32 snapshot API is unavailable or fails.
    """
    return {pid: ppid for pid, (ppid, _) in windows_process_snapshot().items()}


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
                timeout=15,
            )
            return res.returncode == 0
        terminate_process(pid, force=True)
        return True
    except Exception:
        return False


def _emit_log(logger: Any, level: str, message: str) -> None:
    """Dispatch a log message to a CliLogger or standard logging.Logger."""
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


def safe_kill_report(
    pids: Sequence[int],
    logger: Any = None,
    force: bool = False,
) -> tuple[bool, list[dict[str, Any]]]:
    """Terminate process IDs like :func:`safe_kill` and report the outcome of each one.

    Returns:
        ``(succeeded, results)`` where ``results`` holds one ``{"pid", "outcome"}`` mapping per PID with outcome
        ``killed``, ``skipped-protected``, ``not-found``, or ``failed`` (failures add a ``detail`` message).
        ``results`` is empty when the protected process hierarchy cannot be inspected.
    """
    active_logger = logger if logger is not None else CliLogger()
    try:
        protected_pids = get_process_hierarchy(os.getpid())
    except Exception as exc:
        _emit_log(active_logger, "ERROR", f"Cannot inspect protected process hierarchy: {exc}")
        return False, []

    _emit_log(active_logger, "DEBUG", f"Protected process hierarchy: {sorted(protected_pids)}")
    all_succeeded = True
    results: list[dict[str, Any]] = []

    def failed(pid: int, message: str) -> None:
        nonlocal all_succeeded
        _emit_log(active_logger, "ERROR", message)
        results.append({"pid": pid, "outcome": "failed", "detail": message})
        all_succeeded = False

    for pid in pids:
        if pid in protected_pids:
            _emit_log(
                active_logger,
                "WARN",
                f"Skipping protected PID {pid} (current script or ancestor process).",
            )
            results.append({"pid": pid, "outcome": "skipped-protected"})
            continue

        try:
            terminate_process(pid, force=force)
            _emit_log(active_logger, "INFO", f"Killed PID {pid}")
            results.append({"pid": pid, "outcome": "killed"})
        except ProcessLookupError:
            _emit_log(active_logger, "WARN", f"PID {pid} not found.")
            results.append({"pid": pid, "outcome": "not-found"})
        except subprocess.CalledProcessError as exc:
            detail = exc.stderr or exc.stdout or ""
            if isinstance(detail, bytes):
                detail = detail.decode(errors="replace")
            detail_str = str(detail).strip()
            suffix = f": {detail_str}" if detail_str else "."
            failed(pid, f"Failed to kill PID {pid}{suffix}")
        except PermissionError:
            failed(pid, f"Permission denied to kill PID {pid}.")
        except Exception as exc:
            failed(pid, f"Error killing PID {pid}: {exc}")

    return all_succeeded, results


def safe_kill(
    pids: Sequence[int],
    logger: Any = None,
    force: bool = False,
) -> bool:
    """Terminate a sequence of process IDs while protecting the current process and its ancestors.

    Args:
        pids: Sequence of process IDs to terminate.
        logger: Optional logger instance (:class:`~support_python.logging.CliLogger`
            or standard ``logging.Logger``). Defaults to a new :class:`CliLogger`.
        force: If ``True``, forcefully terminate targets (``SIGKILL`` or ``taskkill /F``).

    Returns:
        ``True`` if all target processes were terminated or safely skipped (protected or
        already absent), ``False`` if ancestor resolution or any target termination failed.
    """
    return safe_kill_report(pids, logger=logger, force=force)[0]


def _resolve_parent_and_name_map() -> dict[int, tuple[int, str]]:
    """Return a mapping of ``pid -> (ppid, name)`` across running OS processes."""
    if sys.platform == "win32":
        try:
            return windows_process_snapshot()
        except Exception:
            return {pid: (ppid, "") for pid, ppid in _powershell_parent_map().items()}
    entries: dict[int, tuple[int, str]] = {}
    if Path("/proc").is_dir():
        with os.scandir("/proc") as it:
            for item in it:
                if item.name.isdigit():
                    try:
                        raw = Path(item.path, "stat").read_text(encoding="utf-8", errors="replace")
                        entries[int(item.name)] = (int(raw.rsplit(")", 1)[1].split()[1]), raw.split("(", 1)[1].rsplit(")", 1)[0])
                    except Exception:
                        continue
        if entries:
            return entries
    res = subprocess.run(["ps", "-A", "-o", "pid=,ppid=,comm="], capture_output=True, text=True, check=True, timeout=5)
    for line in res.stdout.splitlines():
        parts = line.strip().split(None, 2)
        if len(parts) >= 2:
            entries[int(parts[0])] = (int(parts[1]), parts[2] if len(parts) > 2 else "")
    return entries


def get_process_descendants(start_pid: int, parent_map: dict[int, int] | None = None) -> set[int]:
    """Return ``start_pid`` and all of its descendant process IDs."""
    if start_pid <= 0:
        raise OSError(f"Cannot resolve descendants of non-positive PID {start_pid}")
    parents = parent_map if parent_map is not None else {pid: ppid for pid, (ppid, _) in _resolve_parent_and_name_map().items()}
    children: dict[int, list[int]] = {}
    for pid, ppid in parents.items():
        if pid != ppid:
            children.setdefault(ppid, []).append(pid)
    descendants, queue = {start_pid}, [start_pid]
    while queue:
        for child in children.get(queue.pop(), ()):
            if child not in descendants:
                descendants.add(child)
                queue.append(child)
    return descendants


def get_process_cwd(pid: int) -> Path | None:
    """Resolve the current working directory of ``pid`` using stdlib and ``ctypes``."""
    if pid <= 0:
        return None
    if pid == os.getpid():
        return Path.cwd().resolve()
    if sys.platform == "win32":
        try:
            import ctypes
            from ctypes import wintypes

            class _Pbi(ctypes.Structure):
                _fields_ = [("R1", ctypes.c_void_p), ("Peb", ctypes.c_void_p), ("R2", ctypes.c_void_p * 4)]

            class _Ustr(ctypes.Structure):
                _fields_ = [("Length", wintypes.USHORT), ("MaxLength", wintypes.USHORT), ("Buffer", ctypes.c_void_p)]

            k32, ntdll = ctypes.WinDLL("kernel32", use_last_error=True), ctypes.WinDLL("ntdll")
            k32.OpenProcess.restype = wintypes.HANDLE
            handle = k32.OpenProcess(0x0410, False, pid)
            if not handle:
                return None
            try:
                pbi, rlen, bread = _Pbi(), wintypes.ULONG(), ctypes.c_size_t()
                rpm = k32.ReadProcessMemory
                rpm.argtypes = [wintypes.HANDLE, ctypes.c_void_p, ctypes.c_void_p, ctypes.c_size_t, ctypes.POINTER(ctypes.c_size_t)]
                if (
                    ntdll.NtQueryInformationProcess(handle, 0, ctypes.byref(pbi), ctypes.sizeof(pbi), ctypes.byref(rlen)) != 0
                    or not pbi.Peb
                ):
                    return None
                psize = ctypes.sizeof(ctypes.c_void_p)
                poff, coff = (0x20, 0x38) if psize == 8 else (0x10, 0x24)
                params, us = ctypes.c_void_p(), _Ustr()
                if not rpm(handle, pbi.Peb + poff, ctypes.byref(params), psize, ctypes.byref(bread)) or not params.value:
                    return None
                if (
                    not rpm(handle, params.value + coff, ctypes.byref(us), ctypes.sizeof(us), ctypes.byref(bread))
                    or not us.Length
                    or not us.Buffer
                ):
                    return None
                buf = ctypes.create_unicode_buffer(us.Length // 2)
                if not rpm(handle, us.Buffer, buf, us.Length, ctypes.byref(bread)):
                    return None
                return Path(buf.value.rstrip("\\/") or buf.value).resolve()
            finally:
                k32.CloseHandle(handle)
        except Exception:
            return None
    proc_cwd = Path(f"/proc/{pid}/cwd")
    try:
        if proc_cwd.exists() or proc_cwd.is_symlink():
            return Path(os.readlink(proc_cwd)).resolve()
    except OSError:
        pass
    try:
        res = subprocess.run(["lsof", "-a", "-p", str(pid), "-d", "cwd", "-Fn"], capture_output=True, text=True, timeout=5)
        for line in res.stdout.splitlines():
            if line.startswith("n") and len(line) > 1:
                return Path(line[1:]).resolve()
    except Exception:
        pass
    return None


def get_process_open_files(pid: int) -> set[Path]:
    """Return open file paths held by ``pid`` on POSIX platforms."""
    if pid <= 0 or sys.platform == "win32":
        return set()
    opened: set[Path] = set()
    fd_dir = Path(f"/proc/{pid}/fd")
    if fd_dir.is_dir():
        try:
            for entry in fd_dir.iterdir():
                try:
                    target = os.readlink(entry)
                    if target.startswith("/"):
                        opened.add(Path(target).resolve())
                except OSError:
                    continue
        except OSError:
            pass
        return opened
    try:
        res = subprocess.run(["lsof", "-p", str(pid), "-Fn"], capture_output=True, text=True, timeout=5)
        for line in res.stdout.splitlines():
            if line.startswith("n/"):
                opened.add(Path(line[1:]).resolve())
    except Exception:
        pass
    return opened


def _path_is_within(candidate: Path, target: Path) -> bool:
    """Return ``True`` if ``candidate`` equals ``target`` or lies inside ``target``."""
    try:
        cand_norm, targ_norm = os.path.normcase(str(candidate.resolve())), os.path.normcase(str(target.resolve()))
    except OSError:
        return False
    return cand_norm == targ_norm or cand_norm.startswith(targ_norm.rstrip("\\/") + os.sep)


def find_pids_with_open_path(path: str | Path) -> set[int]:
    """Find all process IDs that have ``path`` (or a file inside ``path``) open."""
    target = Path(path).resolve()
    if sys.platform == "win32":
        import ctypes
        from ctypes import wintypes

        class _RmProcInfo(ctypes.Structure):
            _fields_ = [("Pid", wintypes.DWORD), ("Start", wintypes.DWORD * 2), ("Pad", ctypes.c_byte * 660)]

        files = [str(c.resolve()) for c in target.rglob("*") if c.is_file()][:64] if target.is_dir() else [str(target)]
        pids: set[int] = set()
        if not files:
            return pids
        try:
            rm = ctypes.WinDLL("RstrtMgr", use_last_error=True)
            sess, skey = wintypes.DWORD(), (wintypes.WCHAR * 33)()
            if rm.RmStartSession(ctypes.byref(sess), 0, skey) != 0:
                return pids
            try:
                res_arr = (wintypes.LPCWSTR * len(files))(*files)
                if rm.RmRegisterResources(sess, len(files), res_arr, 0, None, 0, None) == 0:
                    needed, count, reasons = wintypes.UINT(0), wintypes.UINT(0), wintypes.DWORD(0)
                    if (
                        rm.RmGetList(sess, ctypes.byref(needed), ctypes.byref(count), None, ctypes.byref(reasons)) == 234
                        and needed.value > 0
                    ):
                        arr, count = (_RmProcInfo * needed.value)(), wintypes.UINT(needed.value)
                        if rm.RmGetList(sess, ctypes.byref(needed), ctypes.byref(count), arr, ctypes.byref(reasons)) == 0:
                            pids.update(int(arr[i].Pid) for i in range(count.value))
            finally:
                rm.RmEndSession(sess)
            if pids:
                snap = windows_process_snapshot()
                for mpid in list(pids):
                    if (
                        mpid in snap
                        and snap[mpid][0] in snap
                        and snap[mpid][1]
                        and snap[snap[mpid][0]][1].lower() == snap[mpid][1].lower()
                    ):
                        pids.add(snap[mpid][0])
        except Exception:
            pass
        return pids

    proc_root = Path("/proc")
    if proc_root.is_dir():
        try:
            return {
                int(e.name)
                for e in proc_root.iterdir()
                if e.name.isdigit() and any(_path_is_within(f, target) for f in get_process_open_files(int(e.name)))
            }
        except OSError:
            return set()
    try:
        res = subprocess.run(["lsof", "-Fn", "--", str(target)], capture_output=True, text=True, timeout=5)
        return {int(line[1:]) for line in res.stdout.splitlines() if line.startswith("p") and line[1:].isdigit()}
    except Exception:
        return set()


def filter_processes(
    processes_list: Sequence[ProcessInfo],
    *,
    cwd: str | Path | None = None,
    open_path: str | Path | None = None,
    started_before: datetime | None = None,
    started_after: datetime | None = None,
    ancestors_of: int | None = None,
    descendants_of: int | None = None,
    parent_map: dict[int, int] | None = None,
    open_pids: set[int] | None = None,
) -> list[ProcessInfo]:
    """Filter a sequence of :class:`ProcessInfo` records against optional criteria."""
    derived_parents = parent_map if parent_map is not None else {p.pid: p.ppid for p in processes_list}
    allowed_pids: set[int] | None = None
    if ancestors_of is not None:
        if parent_map is not None:
            anc, curr = set(), ancestors_of
            while curr > 0 and curr not in anc:
                anc.add(curr)
                if curr not in derived_parents:
                    break
                curr = derived_parents[curr]
        else:
            anc = get_process_hierarchy(ancestors_of)
        allowed_pids = anc
    if descendants_of is not None:
        desc = get_process_descendants(descendants_of, parent_map=derived_parents)
        allowed_pids = desc if allowed_pids is None else (allowed_pids & desc)
    if open_path is not None:
        matching_open = open_pids if open_pids is not None else find_pids_with_open_path(open_path)
        allowed_pids = matching_open if allowed_pids is None else (allowed_pids & matching_open)

    target_cwd = Path(cwd).resolve() if cwd is not None else None
    before_dt = _to_naive_local(started_before) if started_before is not None else None
    after_dt = _to_naive_local(started_after) if started_after is not None else None
    results: list[ProcessInfo] = []
    for proc in processes_list:
        if allowed_pids is not None and proc.pid not in allowed_pids:
            continue
        if before_dt is not None and (proc.started is None or _to_naive_local(proc.started) > before_dt):
            continue
        if after_dt is not None and (proc.started is None or _to_naive_local(proc.started) < after_dt):
            continue
        if target_cwd is not None:
            proc_cwd = Path(proc.cwd) if proc.cwd else get_process_cwd(proc.pid)
            if proc_cwd is None or not _path_is_within(proc_cwd, target_cwd):
                continue
        results.append(proc)
    return results


def list_processes(
    *,
    cwd: str | Path | None = None,
    open_path: str | Path | None = None,
    started_before: datetime | None = None,
    started_after: datetime | None = None,
    ancestors_of: int | None = None,
    descendants_of: int | None = None,
) -> list[ProcessInfo]:
    """Enumerate running OS processes and apply optional hierarchy, path, and start-time filters."""
    snapshot = _resolve_parent_and_name_map()
    parent_map = {pid: ppid for pid, (ppid, _) in snapshot.items()}
    candidate_pids = set(snapshot.keys())
    if ancestors_of is not None:
        candidate_pids &= get_process_hierarchy(ancestors_of)
    if descendants_of is not None:
        candidate_pids &= get_process_descendants(descendants_of, parent_map=parent_map)
    open_pids = find_pids_with_open_path(open_path) if open_path is not None else None
    if open_pids is not None:
        candidate_pids &= open_pids

    need_cwd = cwd is not None or len(candidate_pids) <= 32
    raw_records: list[ProcessInfo] = []
    for pid in sorted(candidate_pids):
        ppid, name = snapshot[pid]
        resolved_cwd = get_process_cwd(pid) if need_cwd else None
        if cwd is not None and (resolved_cwd is None or not _path_is_within(resolved_cwd, Path(cwd).resolve())):
            continue
        started = get_process_start_time(pid)
        if resolved_cwd is None:
            resolved_cwd = get_process_cwd(pid)
        raw_records.append(
            ProcessInfo(pid=pid, ppid=ppid, name=name, started=started, cwd=str(resolved_cwd) if resolved_cwd else None)
        )
    return filter_processes(
        raw_records,
        cwd=cwd,
        open_path=open_path,
        started_before=started_before,
        started_after=started_after,
        ancestors_of=ancestors_of,
        descendants_of=descendants_of,
        parent_map=parent_map,
        open_pids=open_pids,
    )


__all__ = [
    "ProcessInfo",
    "filter_processes",
    "find_pids_with_open_path",
    "get_process_cwd",
    "get_process_descendants",
    "get_process_hierarchy",
    "get_process_open_files",
    "get_process_start_time",
    "is_process_alive",
    "list_processes",
    "safe_kill",
    "safe_kill_report",
    "terminate_process",
    "terminate_process_tree",
    "windows_parent_map",
    "windows_process_snapshot",
]
