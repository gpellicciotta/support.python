"""Tests for locking backends, re-entrancy, contention, and timeout handling."""

from __future__ import annotations

import os
from pathlib import Path
import subprocess
import sys
import threading
import time

import pytest

from support_python.locking import (
    FileLock,
    LockTimeoutError,
    NullLock,
    create_lock,
)


def test_file_lock_basic(tmp_path: Path) -> None:
    lock = FileLock(tmp_path / "a.lock", timeout=2.0)
    assert not lock.is_locked
    with lock:
        assert lock.is_locked
    assert not lock.is_locked


def test_file_lock_reentrancy(tmp_path: Path) -> None:
    lock_file = tmp_path / "a.lock"
    lock1 = FileLock(lock_file, timeout=2.0)
    lock2 = FileLock(lock_file, timeout=2.0)
    with lock1:
        with lock2:
            assert lock2.is_locked
        assert lock1.is_locked
    assert not lock1.is_locked


def test_file_lock_timeout_across_threads(tmp_path: Path) -> None:
    lock_file = tmp_path / "a.lock"
    holder_ready = threading.Event()
    release_holder = threading.Event()

    def holder() -> None:
        with FileLock(lock_file, timeout=5.0):
            holder_ready.set()
            release_holder.wait(timeout=2.0)

    thread = threading.Thread(target=holder)
    thread.start()
    assert holder_ready.wait(timeout=2.0)
    try:
        with pytest.raises(LockTimeoutError) as exc_info:
            FileLock(lock_file, timeout=0.1, poll_interval=0.02).acquire()
        assert "Timed out waiting for lock" in str(exc_info.value)
    finally:
        release_holder.set()
        thread.join(timeout=2.0)


@pytest.mark.parametrize("stack_available", [True, False])
def test_file_lock_timeout_identifies_nested_holder(tmp_path: Path, monkeypatch, stack_available: bool) -> None:
    lock_file = tmp_path / "a.lock"
    holder_ready = threading.Event()
    release_holder = threading.Event()

    def hold_nested_lock() -> None:
        with FileLock(lock_file):
            with FileLock(lock_file):
                pass
            holder_ready.set()
            release_holder.wait(timeout=5)

    holder = threading.Thread(target=hold_nested_lock, name="test-lock-holder")
    if not stack_available:

        def unavailable_frames():
            raise RuntimeError("Frame inspection disabled")

        monkeypatch.setattr(sys, "_current_frames", unavailable_frames)
    holder.start()
    try:
        assert holder_ready.wait(timeout=2)
        with pytest.raises(LockTimeoutError) as error:
            FileLock(lock_file, timeout=0.05, poll_interval=0.01, max_jitter=0).acquire()
        message = str(error.value)
        assert f"PID {os.getpid()}" in message
        assert "test-lock-holder" in message
        assert str(holder.ident) in message
        assert "held for" in message
        assert ("hold_nested_lock" if stack_available else "Holder stack: unavailable") in message
    finally:
        release_holder.set()
        holder.join(timeout=5)
    assert not holder.is_alive()

    from support_python.locking import _FILE_LOCK_OWNERS

    assert str(lock_file.resolve()) not in _FILE_LOCK_OWNERS
    with FileLock(lock_file, timeout=0):
        pass
    assert str(lock_file.resolve()) not in _FILE_LOCK_OWNERS


def test_file_lock_holder_details_without_local_owner(monkeypatch) -> None:
    from support_python.locking import _FILE_LOCK_OWNERS, _file_lock_holder_details

    assert "Another process may" in _file_lock_holder_details("missing-lock")
    monkeypatch.setitem(_FILE_LOCK_OWNERS, "inherited-lock", (-1, threading.get_ident(), "parent-holder", time.monotonic()))
    assert "parent-holder" not in _file_lock_holder_details("inherited-lock")


def test_null_lock() -> None:
    lock = NullLock()
    assert not lock.is_locked
    with lock:
        assert lock.is_locked
    assert not lock.is_locked


def test_create_lock_resolution(tmp_path: Path) -> None:
    path = tmp_path / "a.lock"
    assert isinstance(create_lock("null"), NullLock)
    assert isinstance(create_lock("NONE"), NullLock)
    for backend in ("file", "local", "", None):
        lock = create_lock(backend, path=path)
        assert isinstance(lock, FileLock)
        assert lock.lock_path == path.resolve()
    lock = create_lock("file", path=path, timeout=3.5, poll_interval=0.2, max_jitter=0.0)
    assert (lock.timeout, lock.poll_interval, lock.max_jitter) == (3.5, 0.2, 0.0)


def test_create_lock_errors(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="Unsupported locking backend"):
        create_lock("postgres://localhost/db", path=tmp_path / "a.lock")
    with pytest.raises(ValueError, match="requires a lock file path"):
        create_lock("file")


_CONTENDER = """
import sys, time
from support_python.locking import FileLock
path, marker, name = sys.argv[1:4]
for _ in range(5):
    with FileLock(path, timeout=30.0):
        with open(marker, "a") as handle:
            handle.write(f"enter {name}\\n")
            handle.flush()
        time.sleep(0.05)
        with open(marker, "a") as handle:
            handle.write(f"exit {name}\\n")
"""


def test_file_lock_serializes_subprocesses(tmp_path: Path) -> None:
    """Two processes contend for one lock; enter and exit markers never interleave."""
    lock_file = tmp_path / "a.lock"
    marker = tmp_path / "markers.txt"
    src = str(Path(__file__).resolve().parents[1] / "src")
    env = {**os.environ, "PYTHONPATH": src}
    procs = [
        subprocess.Popen([sys.executable, "-c", _CONTENDER, str(lock_file), str(marker), name], env=env) for name in ("a", "b")
    ]
    for proc in procs:
        assert proc.wait(timeout=60) == 0
    lines = marker.read_text(encoding="utf-8").splitlines()
    assert len(lines) == 20
    for index in range(0, len(lines), 2):
        enter, leave = lines[index], lines[index + 1]
        assert enter.startswith("enter ")
        assert leave == "exit " + enter.split(" ", 1)[1]


@pytest.mark.parametrize("backend", ["mysql://h/db", "mysql+pymysql://h", "jdbc:mysql://h"])
def test_create_lock_distributed_not_available_yet(backend: str) -> None:
    with pytest.raises(NotImplementedError):
        create_lock(backend, key="k")
