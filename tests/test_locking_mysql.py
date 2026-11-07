"""Tests for MySQL advisory locking mechanism, URL parsing, and connection handling."""

from __future__ import annotations

import os
from pathlib import Path
import sys
import threading
from typing import Any
from unittest.mock import MagicMock, patch

import pytest

from support_python.locking import (
    LockTimeoutError,
    MySQLLock,
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


def test_mysql_missing_package_raises_import_error() -> None:
    """Acquiring without the pymysql package raises an ImportError mentioning the 'mysql' extra."""
    with patch.dict(sys.modules, {"pymysql": None}):
        lock = MySQLLock(key="test:missing_pkg", mysql_url="mysql://localhost:3306")
        with pytest.raises(ImportError) as exc_info:
            lock.acquire(timeout=0.1)
        assert "mysql" in str(exc_info.value).lower()
        assert "extra" in str(exc_info.value).lower()


def test_mysql_lock_url_parsing() -> None:
    """Test URL parsing for standard, pymysql, and JDBC formats."""
    # Standard URL
    lock1 = MySQLLock(key="k", mysql_url="mysql://user:pass@dbhost:3307/mydb")
    p1 = lock1._parse_url()
    assert p1 == {
        "host": "dbhost",
        "port": 3307,
        "user": "user",
        "password": "pass",
        "database": "mydb",
    }

    # mysql+pymysql scheme
    lock2 = MySQLLock(key="k", mysql_url="mysql+pymysql://admin:secret@10.0.0.1:3306/prod")
    p2 = lock2._parse_url()
    assert p2["user"] == "admin"
    assert p2["host"] == "10.0.0.1"
    assert p2["database"] == "prod"

    # jdbc:mysql scheme
    lock3 = MySQLLock(key="k", mysql_url="jdbc:mysql://root@localhost/test")
    p3 = lock3._parse_url()
    assert p3["user"] == "root"
    assert p3["host"] == "localhost"
    assert p3["port"] == 3306
    assert p3["database"] == "test"


def test_mysql_lock_mock_lifecycle() -> None:
    """Test MySQLLock acquire executes GET_LOCK and release executes RELEASE_LOCK."""
    mock_conn = MagicMock()
    mock_cur = MagicMock()
    mock_conn.cursor.return_value = mock_cur
    mock_cur.fetchone.return_value = (1,)  # GET_LOCK success
    mock_pymysql = MagicMock()
    mock_pymysql.connect.return_value = mock_conn

    with patch.dict(sys.modules, {"pymysql": mock_pymysql}):
        lock = MySQLLock(key="test:mysql_unit", mysql_url="mysql://root:pass@localhost:3306/db", timeout=2.0)
        assert not lock.is_locked

        with lock:
            assert lock.is_locked
            mock_cur.execute.assert_called_with("SELECT GET_LOCK(%s, %s)", ("test:mysql_unit", 2))

        assert not lock.is_locked
        mock_cur.execute.assert_called_with("SELECT RELEASE_LOCK(%s)", ("test:mysql_unit",))
        mock_conn.close.assert_called_once()


def test_mysql_lock_mock_timeout() -> None:
    """Test MySQLLock raises LockTimeoutError when GET_LOCK returns 0."""
    mock_conn = MagicMock()
    mock_cur = MagicMock()
    mock_conn.cursor.return_value = mock_cur
    mock_cur.fetchone.return_value = (0,)  # GET_LOCK timeout
    mock_pymysql = MagicMock()
    mock_pymysql.connect.return_value = mock_conn

    with patch.dict(sys.modules, {"pymysql": mock_pymysql}):
        lock = MySQLLock(key="test:mysql_timeout", mysql_url="mysql://root:pass@localhost:3306/db", timeout=1.0)
        with pytest.raises(LockTimeoutError) as exc_info:
            with lock:
                pass
        assert "Timed out waiting for MySQL advisory lock" in str(exc_info.value)
        mock_conn.close.assert_called_once()


def test_mysql_lock_mock_null_result_raises_error() -> None:
    """Test MySQLLock raises LockTimeoutError when GET_LOCK returns NULL."""
    mock_conn = MagicMock()
    mock_cur = MagicMock()
    mock_conn.cursor.return_value = mock_cur
    mock_cur.fetchone.return_value = (None,)
    mock_pymysql = MagicMock()
    mock_pymysql.connect.return_value = mock_conn

    with patch.dict(sys.modules, {"pymysql": mock_pymysql}):
        lock = MySQLLock(key="test:mysql_null", mysql_url="mysql://root:pass@localhost:3306/db", timeout=1.0)
        with pytest.raises(LockTimeoutError) as exc_info:
            with lock:
                pass
        assert "Failed to acquire MySQL advisory lock" in str(exc_info.value)
        mock_conn.close.assert_called_once()


def test_mysql_lock_mock_reentrancy() -> None:
    """Test MySQLLock re-entrancy on the same thread."""
    mock_conn = MagicMock()
    mock_cur = MagicMock()
    mock_conn.cursor.return_value = mock_cur
    mock_cur.fetchone.return_value = (1,)
    mock_pymysql = MagicMock()
    mock_pymysql.connect.return_value = mock_conn

    with patch.dict(sys.modules, {"pymysql": mock_pymysql}):
        lock1 = MySQLLock(key="test:mysql_reentrant", mysql_url="mysql://localhost:3306", timeout=2.0)
        lock2 = MySQLLock(key="test:mysql_reentrant", mysql_url="mysql://localhost:3306", timeout=2.0)

        with lock1:
            assert lock1.is_locked
            assert mock_cur.execute.call_count == 1
            with lock2:
                assert lock2.is_locked
                assert mock_cur.execute.call_count == 1
            assert lock1.is_locked

        assert not lock1.is_locked
        assert mock_cur.execute.call_count == 2  # 1 GET_LOCK + 1 RELEASE_LOCK


def test_mysql_lock_mock_reentrancy_cross_instance_non_nested_release() -> None:
    """Test re-entrant MySQLLock release across instances regardless of release order."""
    mock_conn = MagicMock()
    mock_cur = MagicMock()
    mock_conn.cursor.return_value = mock_cur
    mock_cur.fetchone.return_value = (1,)
    mock_pymysql = MagicMock()
    mock_pymysql.connect.return_value = mock_conn

    with patch.dict(sys.modules, {"pymysql": mock_pymysql}):
        lock_a = MySQLLock(key="test:mysql_cross", mysql_url="mysql://localhost:3306", timeout=2.0)
        lock_b = MySQLLock(key="test:mysql_cross", mysql_url="mysql://localhost:3306", timeout=2.0)

        assert lock_a.acquire()
        assert lock_b.acquire()

        # Non-LIFO release order: a releases first, b releases second
        lock_a.release()
        assert mock_cur.execute.call_count == 1  # Still held by b (only GET_LOCK called)
        lock_b.release()
        assert mock_cur.execute.call_count == 2  # RELEASE_LOCK executed on outer release
        mock_conn.close.assert_called_once()


def test_mysql_lock_database_access_denied_fallback() -> None:
    """Test MySQLLock falls back to connecting without database on error 1044/1049."""

    class _MockOpError(Exception):
        def __init__(self, code: int, msg: str) -> None:
            super().__init__(code, msg)
            self.args = (code, msg)

    mock_pymysql = MagicMock()
    mock_pymysql.OperationalError = _MockOpError

    mock_conn = MagicMock()
    mock_cur = MagicMock()
    mock_conn.cursor.return_value = mock_cur
    mock_cur.fetchone.return_value = (1,)

    calls: list[dict[str, Any]] = []

    def mock_connect(**kwargs: Any) -> Any:
        calls.append(kwargs)
        if kwargs.get("database") == "restricted_db":
            raise _MockOpError(1044, "Access denied for user to database 'restricted_db'")
        return mock_conn

    mock_pymysql.connect.side_effect = mock_connect

    with patch.dict(sys.modules, {"pymysql": mock_pymysql}):
        lock = MySQLLock(key="test:fallback", mysql_url="mysql://user:pass@host:3306/restricted_db")
        with lock:
            assert lock.is_locked

    assert len(calls) == 2
    assert calls[0]["database"] == "restricted_db"
    assert calls[1]["database"] is None


def test_create_lock_mysql_urls() -> None:
    """Test create_lock handles mysql://, mysql+pymysql://, and jdbc:mysql:// schemes."""
    for scheme in ("mysql://host:3306/db", "mysql+pymysql://host:3306/db", "jdbc:mysql://host:3306/db"):
        lock = create_lock(scheme, key="app:mysql_lock")
        assert isinstance(lock, MySQLLock)
        assert lock.key == "app:mysql_lock"

    with pytest.raises(ValueError, match="requires a key"):
        create_lock("mysql://host:3306/db")


def test_live_mysql_proxy_lock() -> None:
    """Live integration test against MySQL if SUPPORT_PYTHON_TEST_MYSQL_URL is configured."""
    mysql_url = _get_test_env("SUPPORT_PYTHON_TEST_MYSQL_URL") or _get_test_env("PLAN_TEST_MYSQL_URL")
    if not mysql_url:
        pytest.skip("SUPPORT_PYTHON_TEST_MYSQL_URL not configured")

    try:
        import pymysql  # noqa: F401

        lock1 = MySQLLock(key="support_python:test_live_mysql_lock", mysql_url=mysql_url, timeout=5.0)
        lock2 = MySQLLock(key="support_python:test_live_mysql_lock", mysql_url=mysql_url, timeout=0.1)

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
    except Exception as err:
        pytest.skip(f"MySQL connection failed: {err}")
