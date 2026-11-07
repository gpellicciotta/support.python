"""Pluggable locking backends for synchronizing mutations across threads and processes.

Provides:
- :class:`Lock`: abstract base class with a context manager protocol.
- :class:`FileLock`: re-entrant OS file descriptor lock (msvcrt on Windows, fcntl elsewhere).
- :class:`NullLock`: no-op lock for tests or disabled locking.
- :func:`create_lock`: backend factory mapping a backend string to a lock instance.
- :class:`LockTimeoutError`: raised when a lock cannot be acquired within its timeout.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
import os
from pathlib import Path
import random
import sys
import threading
import time
import traceback
from types import TracebackType
from typing import Any, Optional, Union

__all__ = [
    "FileLock",
    "Lock",
    "LockTimeoutError",
    "NullLock",
    "create_lock",
]

DEFAULT_LOCK_TIMEOUT = 10.0
DEFAULT_POLL_INTERVAL = 0.05
DEFAULT_MAX_JITTER = 0.05


class LockTimeoutError(TimeoutError):
    """Raised when a lock cannot be acquired within the configured timeout."""


class Lock(ABC):
    """Abstract base class for all lock implementations."""

    @abstractmethod
    def acquire(self, timeout: Optional[float] = None) -> bool:
        """Acquire lock within optional timeout. Return True on success."""
        ...

    @abstractmethod
    def release(self) -> None:
        """Release the acquired lock."""
        ...

    @property
    @abstractmethod
    def is_locked(self) -> bool:
        """Check whether the lock is currently held by this instance."""
        ...

    def __enter__(self) -> "Lock":
        self.acquire()
        return self

    def __exit__(
        self,
        exc_type: Optional[type],
        exc_val: Optional[BaseException],
        exc_tb: Optional[TracebackType],
    ) -> None:
        self.release()


# Thread-local storage for re-entrant lock counting across the same thread
_LOCAL_LOCK_COUNTS = threading.local()
# Best-effort process-local diagnostics, separate from OS lock ownership.
# Immutable values avoid retaining holder frames or Thread objects after release.
_FILE_LOCK_OWNERS: dict = {}


def _file_lock_holder_details(key: str) -> str:
    """Describe an observed local holder without claiming ownership in other processes."""
    owner = _FILE_LOCK_OWNERS.get(key)
    if owner is None or owner[0] != os.getpid():
        return "Another process may be actively holding the lock or is unresponsive."
    pid, ident, name, acquired_at = owner
    held_for = max(0.0, time.monotonic() - acquired_at)
    stack = "unavailable"
    try:
        frame = sys._current_frames().get(ident)
        if frame is not None:
            try:
                stack = " -> ".join(
                    f"{Path(entry.filename).name}:{entry.lineno} in {entry.name}"
                    for entry in traceback.extract_stack(frame, limit=8)
                )
            finally:
                del frame
    except Exception:
        # Diagnostics must not replace the acquisition timeout with an audit/stack error.
        pass
    return f"Observed local holder: PID {pid}, thread {name!r} ({ident}), held for {held_for:.1f}s. Holder stack: {stack}"


def _reentrancy_counts() -> dict:
    """Return the per-thread re-entrancy counter map, creating it on first use."""
    counts = getattr(_LOCAL_LOCK_COUNTS, "counts", None)
    if counts is None:
        counts = {}
        _LOCAL_LOCK_COUNTS.counts = counts
    return counts


class FileLock(Lock):
    """Cross-platform local OS file descriptor lock (msvcrt on Windows, fcntl on Unix).

    Lock Resource:
        The lock file path given at construction (for example ``<project_dir>/.app.lock``).

    OS-Level Calls & Commands:
        - Windows (sys.platform == 'win32'):
            Acquire: ``msvcrt.locking(fd, msvcrt.LK_NBLCK, 1)``
                     Attempts to place an exclusive, non-blocking lock on byte 0 of the file.
                     If held by another process, raises OSError/PermissionError and retries
                     with jitter until ``timeout`` expires.
            Release: ``msvcrt.locking(fd, msvcrt.LK_UNLCK, 1)``
                     Unlocks byte 0 and closes the file descriptor.
        - Unix / Linux / macOS:
            Acquire: ``fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)``
                     Places an exclusive (LOCK_EX), non-blocking (LOCK_NB) kernel lock.
            Release: ``fcntl.flock(fd, fcntl.LOCK_UN)``
                     Unlocks the file descriptor and closes the file.

    Crash & Termination Semantics:
        File descriptor locks are managed directly by the operating system kernel.
        If a process crashes, is killed (e.g. SIGKILL), or terminates abnormally,
        the OS automatically closes all open file descriptors and frees the lock.
        No stale lock files or orphaned deadlocks remain.
    """

    def __init__(
        self,
        lock_path: Union[Path, str],
        timeout: float = DEFAULT_LOCK_TIMEOUT,
        poll_interval: float = DEFAULT_POLL_INTERVAL,
        max_jitter: float = DEFAULT_MAX_JITTER,
    ) -> None:
        self.lock_path = Path(lock_path).resolve()
        self.timeout = timeout
        self.poll_interval = poll_interval
        self.max_jitter = max_jitter
        self._file: Any = None
        self._depth = 0

    @property
    def is_locked(self) -> bool:
        """Check whether the lock is currently held by this instance."""
        return self._depth > 0

    def acquire(self, timeout: Optional[float] = None) -> bool:
        """Acquire the file lock within the optional timeout.

        Args:
            timeout: Maximum time in seconds to wait for the lock.

        Returns:
            True if the lock was successfully acquired.

        Raises:
            LockTimeoutError: If the lock cannot be acquired before timeout.
        """
        effective_timeout = self.timeout if timeout is None else timeout

        # Thread-local re-entrancy: allow the same thread to re-enter nested lock scopes
        counts = _reentrancy_counts()

        key = str(self.lock_path)
        current_depth = counts.get(key, 0)
        if current_depth > 0:
            counts[key] = current_depth + 1
            self._depth += 1
            return True

        self.lock_path.parent.mkdir(parents=True, exist_ok=True)
        # Open file descriptor for reading and writing in append mode
        self._file = open(self.lock_path, "a+b")
        fd = self._file.fileno()

        start_time = time.monotonic()
        while True:
            try:
                if sys.platform == "win32":
                    import msvcrt

                    # Seek to byte 0 and lock byte 1 in non-blocking mode
                    self._file.seek(0)
                    msvcrt.locking(fd, msvcrt.LK_NBLCK, 1)
                else:
                    import fcntl

                    # Request exclusive non-blocking kernel lock
                    fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)

                counts[key] = 1
                self._depth = 1
                _FILE_LOCK_OWNERS[key] = (os.getpid(), threading.get_ident(), threading.current_thread().name, time.monotonic())
                return True
            except (BlockingIOError, OSError, PermissionError):
                elapsed = time.monotonic() - start_time
                if elapsed >= effective_timeout:
                    self._cleanup_file()
                    raise LockTimeoutError(
                        f"Timed out waiting for lock on {self.lock_path} after {effective_timeout:.1f}s. "
                        + _file_lock_holder_details(key)
                    )
                sleep_duration = self.poll_interval + random.uniform(0.0, self.max_jitter)
                time.sleep(sleep_duration)

    def release(self) -> None:
        """Release the acquired file lock."""
        counts = getattr(_LOCAL_LOCK_COUNTS, "counts", None)
        key = str(self.lock_path)
        if counts and key in counts:
            counts[key] -= 1
            self._depth -= 1
            if counts[key] > 0:
                # Still held by an outer re-entrant scope
                return
            del counts[key]

        if self._file:
            _FILE_LOCK_OWNERS.pop(key, None)
            try:
                fd = self._file.fileno()
                if sys.platform == "win32":
                    import msvcrt

                    self._file.seek(0)
                    msvcrt.locking(fd, msvcrt.LK_UNLCK, 1)
                else:
                    import fcntl

                    fcntl.flock(fd, fcntl.LOCK_UN)
            except OSError:
                pass
            finally:
                self._cleanup_file()

    def _cleanup_file(self) -> None:
        if self._file:
            try:
                self._file.close()
            except OSError:
                pass
            self._file = None


class NullLock(Lock):
    """No-op lock implementation for tests or environments with disabled locking."""

    def __init__(self) -> None:
        self._locked = False

    @property
    def is_locked(self) -> bool:
        """Check whether the lock is currently held."""
        return self._locked

    def acquire(self, timeout: Optional[float] = None) -> bool:
        """Acquire the null lock. Always succeeds immediately."""
        self._locked = True
        return True

    def release(self) -> None:
        """Release the null lock."""
        self._locked = False


def create_lock(
    backend: Optional[str] = None,
    key: Optional[str] = None,
    path: Optional[Union[Path, str]] = None,
    timeout: float = DEFAULT_LOCK_TIMEOUT,
    poll_interval: float = DEFAULT_POLL_INTERVAL,
    max_jitter: float = DEFAULT_MAX_JITTER,
) -> Lock:
    """Create the appropriate :class:`Lock` for a backend string.

    Args:
        backend: Backend selector, case-insensitive. ``null``/``none`` returns :class:`NullLock`;
            ``file``/``local`` or empty/None returns :class:`FileLock`; URL schemes select distributed locks.
        key: Resource name for distributed backends.
        path: Lock file path; required for the file backend.
        timeout: Maximum seconds to wait when acquiring.
        poll_interval: Seconds between acquisition retries.
        max_jitter: Maximum random seconds added to each retry delay.

    Raises:
        ValueError: If the scheme is unsupported or a required argument is missing.
    """
    value = (backend or "").strip()
    lower = value.lower()
    if lower in ("null", "none"):
        return NullLock()
    if lower in ("", "file", "local"):
        if path is None:
            raise ValueError("The file lock backend requires a lock file path.")
        return FileLock(path, timeout=timeout, poll_interval=poll_interval, max_jitter=max_jitter)
    if lower.startswith(("redis://", "rediss://")):
        raise NotImplementedError("The Redis lock backend is not available yet.")
    if lower.startswith(("mysql://", "mysql+pymysql://", "jdbc:mysql://")):
        raise NotImplementedError("The MySQL lock backend is not available yet.")
    raise ValueError(f"Unsupported locking backend scheme: {value}")
