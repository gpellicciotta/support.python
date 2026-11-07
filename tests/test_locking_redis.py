"""Tests for Redis-backed distributed lock implementation, retry, and re-entrancy."""

from __future__ import annotations

import os
from pathlib import Path
import sys
import threading
from unittest.mock import MagicMock, patch

import pytest

from support_python.locking import (
    LockTimeoutError,
    RedisLock,
    create_lock,
)


def _get_test_env(name: str) -> str | None:
    val = os.environ.get(name)
    if val:
        return val
    env_file = Path(".env")
    if env_file.is_file():
        try:
            for line in env_file.read_text(encoding="utf-8").splitlines():
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    k, v = line.split("=", 1)
                    if k.strip() == name:
                        return v.strip()
        except OSError:
            pass
    return None


def test_redis_missing_package_raises_import_error() -> None:
    """Acquiring without the redis package raises an ImportError mentioning the 'redis' extra."""
    with patch.dict(sys.modules, {"redis": None}):
        lock = RedisLock(key="test:missing_pkg", redis_url="redis://localhost:6379/0")
        with pytest.raises(ImportError) as exc_info:
            lock.acquire(timeout=0.1)
        assert "redis" in str(exc_info.value).lower()
        assert "extra" in str(exc_info.value).lower()


def test_redis_lock_mock_lifecycle() -> None:
    """Test RedisLock acquire, holds token, and evaluates release script."""
    mock_client = MagicMock()
    mock_client.set.return_value = True
    mock_client.eval.return_value = 1
    mock_redis = MagicMock()
    mock_redis.from_url.return_value = mock_client

    with patch.dict(sys.modules, {"redis": mock_redis}):
        lock = RedisLock(key="test:unit", redis_url="redis://localhost:6379/0", timeout=1.0, ttl=15.0)
        assert not lock.is_locked

        with lock:
            assert lock.is_locked
            assert lock._token is not None
            mock_client.set.assert_called_once()
            args, kwargs = mock_client.set.call_args
            assert args[0] == "test:unit"
            assert kwargs.get("nx") is True
            assert kwargs.get("px") == 15000

        assert not lock.is_locked
        mock_client.eval.assert_called_once()
        eval_args = mock_client.eval.call_args[0]
        assert eval_args[1] == 1
        assert eval_args[2] == "test:unit"


def test_redis_lock_mock_timeout() -> None:
    """Test RedisLock raises LockTimeoutError when key cannot be acquired within timeout."""
    mock_client = MagicMock()
    mock_client.set.return_value = None  # NX failed
    mock_redis = MagicMock()
    mock_redis.from_url.return_value = mock_client

    with patch.dict(sys.modules, {"redis": mock_redis}):
        lock = RedisLock(key="test:timeout", redis_url="redis://localhost:6379/0", timeout=0.05, poll_interval=0.01)
        with pytest.raises(LockTimeoutError) as exc_info:
            with lock:
                pass
        assert "Timed out waiting for Redis lock" in str(exc_info.value)


def test_redis_lock_mock_reentrancy() -> None:
    """Test RedisLock supports re-entrant acquisition on the same thread without multi-acquires."""
    mock_client = MagicMock()
    mock_client.set.return_value = True
    mock_client.eval.return_value = 1
    mock_redis = MagicMock()
    mock_redis.from_url.return_value = mock_client

    with patch.dict(sys.modules, {"redis": mock_redis}):
        lock1 = RedisLock(key="test:reentrant", redis_url="redis://localhost:6379/0", timeout=1.0)
        lock2 = RedisLock(key="test:reentrant", redis_url="redis://localhost:6379/0", timeout=1.0)

        with lock1:
            assert lock1.is_locked
            assert mock_client.set.call_count == 1
            with lock2:
                assert lock2.is_locked
                assert mock_client.set.call_count == 1  # Not called again
            assert lock1.is_locked

        assert not lock1.is_locked
        assert mock_client.eval.call_count == 1  # Evaluated once on outer release


def test_redis_lock_mock_reentrancy_cross_instance_non_nested_release() -> None:
    """Test re-entrant RedisLock release across instances regardless of release order."""
    mock_client = MagicMock()
    mock_client.set.return_value = True
    mock_client.eval.return_value = 1
    mock_redis = MagicMock()
    mock_redis.from_url.return_value = mock_client

    with patch.dict(sys.modules, {"redis": mock_redis}):
        lock_a = RedisLock(key="test:cross_inst", redis_url="redis://localhost:6379/0", timeout=1.0)
        lock_b = RedisLock(key="test:cross_inst", redis_url="redis://localhost:6379/0", timeout=1.0)

        assert lock_a.acquire()
        assert lock_b.acquire()

        # Non-LIFO release order: a releases first, b releases second
        lock_a.release()
        assert mock_client.eval.call_count == 0  # Still held by b
        lock_b.release()
        assert mock_client.eval.call_count == 1  # Released on outer exit with stored token


def test_create_lock_redis_urls() -> None:
    """Test create_lock handles redis:// and rediss:// schemes."""
    lock = create_lock("redis://localhost:6379/0", key="app:tasks")
    assert isinstance(lock, RedisLock)
    assert lock.key == "app:tasks"
    assert lock.redis_url == "redis://localhost:6379/0"

    lock_tls = create_lock("rediss://default:secret@upstash:6379", key="app:tasks_tls", ttl=45.0)
    assert isinstance(lock_tls, RedisLock)
    assert lock_tls.ttl == 45.0

    with pytest.raises(ValueError, match="requires a key"):
        create_lock("redis://localhost:6379/0")


def test_live_redis_lock() -> None:
    """Live integration test against Redis if SUPPORT_PYTHON_TEST_REDIS_URL is configured."""
    redis_url = _get_test_env("SUPPORT_PYTHON_TEST_REDIS_URL") or _get_test_env("PLAN_TEST_REDIS_URL")
    if not redis_url:
        pytest.skip("SUPPORT_PYTHON_TEST_REDIS_URL not configured")
    try:
        import redis  # noqa: F401
    except ImportError:
        pytest.skip("redis package not installed")

    lock1 = RedisLock(key="support_python:test_live_redis_lock", redis_url=redis_url, timeout=5.0, ttl=10.0)
    lock2 = RedisLock(key="support_python:test_live_redis_lock", redis_url=redis_url, timeout=0.1, ttl=10.0)

    # 1. Basic acquire & re-entrancy
    with lock1:
        assert lock1.is_locked
        with lock1:
            assert lock1.is_locked

        # 2. Contention from separate thread should timeout
        contention_failed = threading.Event()

        def try_compete() -> None:
            try:
                with lock2:
                    pass
            except LockTimeoutError:
                contention_failed.set()

        t = threading.Thread(target=try_compete)
        t.start()
        t.join(timeout=3.0)
        assert contention_failed.is_set(), "Competing thread should have timed out"

    assert not lock1.is_locked

    # 3. Once released, second lock acquires cleanly
    with lock2:
        assert lock2.is_locked
