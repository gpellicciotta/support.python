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
import urllib.parse
import uuid

__all__ = [
    "FileLock",
    "Lock",
    "LockTimeoutError",
    "MySQLLock",
    "NullLock",
    "RedisLock",
    "create_lock",
]

DEFAULT_LOCK_TIMEOUT = 10.0
DEFAULT_LOCK_TTL = 30.0
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


def _reentrancy_tokens() -> dict:
    """Return the per-thread lock token map for distributed locks, creating it on first use."""
    tokens = getattr(_LOCAL_LOCK_COUNTS, "tokens", None)
    if tokens is None:
        tokens = {}
        _LOCAL_LOCK_COUNTS.tokens = tokens
    return tokens


def _reentrancy_connections() -> dict:
    """Return the per-thread connection map for MySQL advisory locks, creating it on first use."""
    connections = getattr(_LOCAL_LOCK_COUNTS, "connections", None)
    if connections is None:
        connections = {}
        _LOCAL_LOCK_COUNTS.connections = connections
    return connections


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


class RedisLock(Lock):
    """Distributed Redis-backed lock using atomic SET NX PX and Lua script token release.

    Lock Resource:
        Key name in Redis, such as ``app:tasks``.
        Value in Redis: Unique UUIDv4 token generated per acquisition attempt.

    Redis Wire Commands Dispatched:
        1. Acquire:
           ``SET <key> <uuid_token> NX PX <ttl_ms>``
           - ``NX``: atomically sets the key only if it does not already exist.
           - ``PX <ttl_ms>``: attaches an automatic expiration lease (default 30,000ms = 30s).
           - Retries with random jitter every ``poll_interval`` until acquired or ``timeout`` expires.

        2. Release:
           Evaluates an atomic Lua script:
           .. code-block:: lua

               if redis.call("get", KEYS[1]) == ARGV[1] then
                   return redis.call("del", KEYS[1])
               else
                   return 0
               end

    Crash & Deadlock Semantics:
        If a client process crashes or dies, Redis automatically expires the key when the TTL lease runs out.
    """

    _LUA_RELEASE_SCRIPT = """
    if redis.call("get", KEYS[1]) == ARGV[1] then
        return redis.call("del", KEYS[1])
    else
        return 0
    end
    """

    def __init__(
        self,
        key: str,
        redis_url: str = "redis://localhost:6379/0",
        timeout: float = DEFAULT_LOCK_TIMEOUT,
        ttl: float = DEFAULT_LOCK_TTL,
        poll_interval: float = DEFAULT_POLL_INTERVAL,
        max_jitter: float = DEFAULT_MAX_JITTER,
    ) -> None:
        self.key = key
        self.redis_url = redis_url
        self.timeout = timeout
        self.ttl = ttl
        self.poll_interval = poll_interval
        self.max_jitter = max_jitter
        self._token: Optional[str] = None
        self._depth = 0
        self._client: Any = None

    @property
    def is_locked(self) -> bool:
        """Check whether the Redis lock is currently held by this instance."""
        return self._depth > 0

    def _get_client(self) -> Any:
        if self._client is None:
            try:
                import redis
            except ImportError as err:
                raise ImportError(
                    "Redis locking backend requires the 'redis' extra. Install it via 'pip install support-python[redis]'."
                ) from err
            self._client = redis.from_url(self.redis_url)
        return self._client

    def acquire(self, timeout: Optional[float] = None) -> bool:
        """Acquire the distributed Redis lock within the optional timeout.

        Args:
            timeout: Maximum time in seconds to wait for the lock.

        Returns:
            True if the lock was successfully acquired.

        Raises:
            LockTimeoutError: If the lock cannot be acquired before timeout.
        """
        effective_timeout = self.timeout if timeout is None else timeout

        counts = _reentrancy_counts()
        reentrancy_key = f"redis:{self.redis_url}:{self.key}"
        current_depth = counts.get(reentrancy_key, 0)
        if current_depth > 0:
            counts[reentrancy_key] = current_depth + 1
            self._depth += 1
            return True

        client = self._get_client()
        token = str(uuid.uuid4())
        ttl_ms = max(1, int(self.ttl * 1000))
        start_time = time.monotonic()

        while True:
            try:
                acquired = client.set(self.key, token, nx=True, px=ttl_ms)
                if acquired:
                    self._token = token
                    self._depth = 1
                    counts[reentrancy_key] = 1
                    _reentrancy_tokens()[reentrancy_key] = token
                    return True
            except Exception as exc:
                elapsed = time.monotonic() - start_time
                if elapsed >= effective_timeout:
                    raise LockTimeoutError(
                        f"Failed to acquire Redis lock on '{self.key}' within {effective_timeout:.1f}s: {exc}"
                    ) from exc

            elapsed = time.monotonic() - start_time
            if elapsed >= effective_timeout:
                raise LockTimeoutError(
                    f"Timed out waiting for Redis lock on '{self.key}' after {effective_timeout:.1f}s. "
                    "Another process or node is actively holding the lock."
                )

            sleep_duration = self.poll_interval + random.uniform(0.0, self.max_jitter)
            time.sleep(sleep_duration)

    def release(self) -> None:
        """Release the acquired Redis lock."""
        counts = _reentrancy_counts()
        reentrancy_key = f"redis:{self.redis_url}:{self.key}"
        if counts and reentrancy_key in counts:
            counts[reentrancy_key] -= 1
            self._depth -= 1
            if counts[reentrancy_key] > 0:
                return
            del counts[reentrancy_key]

        tokens = _reentrancy_tokens()
        token = tokens.pop(reentrancy_key, None) or self._token
        client = self._client or (self._get_client() if token else None)
        if token and client:
            try:
                client.eval(self._LUA_RELEASE_SCRIPT, 1, self.key, token)
            except Exception:
                pass
            finally:
                self._token = None
                self._depth = 0


class MySQLLock(Lock):
    """Distributed MySQL advisory lock using GET_LOCK and RELEASE_LOCK.

    Lock Resource:
        Lock Name in MySQL, such as ``app:tasks``.
        Scope: Server-wide across the entire MySQL instance.

    MySQL Wire Commands Dispatched:
        1. Acquire:
           ``SELECT GET_LOCK('...', <timeout_sec>);``
           - Calls MySQL's built-in user-level advisory locking engine.
           - Blocks on the server side for up to ``timeout_sec`` seconds.
           - Returns:
             ``1``: Lock acquired successfully.
             ``0``: Lock attempt timed out on the MySQL server.
             ``NULL``: An unexpected error occurred inside MySQL (e.g. out of memory).

        2. Release:
           ``SELECT RELEASE_LOCK('...');``
           - Releases the named advisory lock associated with the current connection.
           - Returns ``1`` if successfully freed, ``0`` if not held by this session.
           - The database connection and cursor are then closed.

    Crash & Deadlock Semantics:
        Advisory locks in MySQL are bound to the client's TCP database session.
        If a client process terminates, crashes, or loses network connectivity,
        the operating system closes the TCP socket, and the MySQL server
        automatically drops all advisory locks held by that session immediately.
        Zero deadlocks can remain after a client crash.

    Database Permission Fallback:
        Because MySQL advisory locks are server-wide and do not operate on table rows,
        they do not require an active database. If connecting to a specified database
        raises error 1044 (Access denied) or 1049 (Unknown database), MySQLLock
        automatically reconnects with ``database=None`` so advisory locks function cleanly.
    """

    def __init__(
        self,
        key: str,
        mysql_url: str = "mysql://localhost:3306",
        timeout: float = DEFAULT_LOCK_TIMEOUT,
        poll_interval: float = DEFAULT_POLL_INTERVAL,
        max_jitter: float = DEFAULT_MAX_JITTER,
    ) -> None:
        self.key = key
        self.mysql_url = mysql_url
        self.timeout = timeout
        self.poll_interval = poll_interval
        self.max_jitter = max_jitter
        self._depth = 0
        self._conn: Any = None

    @property
    def is_locked(self) -> bool:
        """Check whether the MySQL advisory lock is currently held by this instance."""
        return self._depth > 0

    def _parse_url(self) -> dict[str, Any]:
        url = self.mysql_url
        if url.startswith("jdbc:"):
            url = url[len("jdbc:") :]
        if url.startswith("mysql+pymysql://"):
            url = "mysql://" + url[len("mysql+pymysql://") :]

        parsed = urllib.parse.urlparse(url)
        return {
            "host": parsed.hostname or "127.0.0.1",
            "port": parsed.port or 3306,
            "user": urllib.parse.unquote(parsed.username) if parsed.username else "root",
            "password": urllib.parse.unquote(parsed.password) if parsed.password else "",
            "database": parsed.path.lstrip("/") or None,
        }

    def _connect(self) -> Any:
        try:
            import pymysql
        except ImportError as err:
            raise ImportError(
                "MySQL locking backend requires the 'mysql' extra. Install it via 'pip install support-python[mysql]'."
            ) from err

        params = self._parse_url()
        try:
            return pymysql.connect(
                host=params["host"],
                port=params["port"],
                user=params["user"],
                password=params["password"],
                database=params["database"],
                connect_timeout=max(2, int(self.timeout)),
                autocommit=True,
            )
        except pymysql.OperationalError as exc:
            # If database access is denied or database does not exist, connect without database
            # because MySQL advisory locks (GET_LOCK/RELEASE_LOCK) are server-wide.
            if params["database"] and exc.args and exc.args[0] in (1044, 1049):
                return pymysql.connect(
                    host=params["host"],
                    port=params["port"],
                    user=params["user"],
                    password=params["password"],
                    database=None,
                    connect_timeout=max(2, int(self.timeout)),
                    autocommit=True,
                )
            raise

    def acquire(self, timeout: Optional[float] = None) -> bool:
        """Acquire the distributed MySQL advisory lock within the optional timeout.

        Args:
            timeout: Maximum time in seconds to wait for the lock.

        Returns:
            True if the lock was successfully acquired.

        Raises:
            LockTimeoutError: If the lock cannot be acquired before timeout.
        """
        effective_timeout = self.timeout if timeout is None else timeout

        counts = _reentrancy_counts()
        reentrancy_key = f"mysql:{self.mysql_url}:{self.key}"
        current_depth = counts.get(reentrancy_key, 0)
        if current_depth > 0:
            counts[reentrancy_key] = current_depth + 1
            self._depth += 1
            return True

        self._conn = self._connect()
        try:
            cur = self._conn.cursor()
            timeout_sec = max(0, int(effective_timeout))
            cur.execute("SELECT GET_LOCK(%s, %s)", (self.key, timeout_sec))
            row = cur.fetchone()
            cur.close()

            res = row[0] if row else None
            if res == 1:
                self._depth = 1
                counts[reentrancy_key] = 1
                _reentrancy_connections()[reentrancy_key] = self._conn
                return True
            elif res == 0:
                self._cleanup_conn()
                raise LockTimeoutError(
                    f"Timed out waiting for MySQL advisory lock on '{self.key}' after {effective_timeout:.1f}s. "
                    "Another process or node is actively holding the lock."
                )
            else:
                self._cleanup_conn()
                raise LockTimeoutError(f"Failed to acquire MySQL advisory lock on '{self.key}' (GET_LOCK returned {res}).")
        except Exception:
            self._cleanup_conn()
            raise

    def release(self) -> None:
        """Release the acquired MySQL advisory lock."""
        counts = _reentrancy_counts()
        reentrancy_key = f"mysql:{self.mysql_url}:{self.key}"
        if counts and reentrancy_key in counts:
            counts[reentrancy_key] -= 1
            self._depth -= 1
            if counts[reentrancy_key] > 0:
                return
            del counts[reentrancy_key]

        connections = _reentrancy_connections()
        conn = connections.pop(reentrancy_key, None) or self._conn
        if conn:
            try:
                cur = conn.cursor()
                cur.execute("SELECT RELEASE_LOCK(%s)", (self.key,))
                cur.close()
            except Exception:
                pass
            finally:
                try:
                    conn.close()
                except Exception:
                    pass
                self._conn = None
                self._depth = 0

    def _cleanup_conn(self) -> None:
        if self._conn:
            try:
                self._conn.close()
            except Exception:
                pass
            self._conn = None


def create_lock(
    backend: Optional[str] = None,
    key: Optional[str] = None,
    path: Optional[Union[Path, str]] = None,
    timeout: float = DEFAULT_LOCK_TIMEOUT,
    poll_interval: float = DEFAULT_POLL_INTERVAL,
    max_jitter: float = DEFAULT_MAX_JITTER,
    ttl: float = DEFAULT_LOCK_TTL,
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
        ttl: Expiration lease duration in seconds for distributed backends with automatic leases.

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
        if key is None:
            raise ValueError("Distributed Redis locking backend requires a key.")
        return RedisLock(
            key=key,
            redis_url=value,
            timeout=timeout,
            ttl=ttl,
            poll_interval=poll_interval,
            max_jitter=max_jitter,
        )
    if lower.startswith(("mysql://", "mysql+pymysql://", "jdbc:mysql://")):
        if key is None:
            raise ValueError("Distributed MySQL locking backend requires a key.")
        return MySQLLock(
            key=key,
            mysql_url=value,
            timeout=timeout,
            poll_interval=poll_interval,
            max_jitter=max_jitter,
        )
    raise ValueError(f"Unsupported locking backend scheme: {value}")
