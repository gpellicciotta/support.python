"""Unit and integration tests for support_python.processes."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
import os
from pathlib import Path
import signal
import subprocess
import sys
import time
from unittest import mock

import pytest

from support_python import (
    CliLogger,
    get_process_hierarchy,
    get_process_start_time,
    is_process_alive,
    safe_kill,
    terminate_process,
    terminate_process_tree,
    windows_parent_map,
)
import support_python.processes as processes


def test_get_process_hierarchy_contains_current_and_parent_pid() -> None:
    hierarchy = get_process_hierarchy(os.getpid())
    assert {os.getpid(), os.getppid()} <= hierarchy


@pytest.mark.skipif(sys.platform != "win32", reason="Windows process snapshot")
def test_windows_parent_map_and_grandparent_hierarchy() -> None:
    parent_map = windows_parent_map()
    assert os.getpid() in parent_map
    parent = parent_map[os.getpid()]
    hierarchy = get_process_hierarchy(os.getpid())
    assert {os.getpid(), parent} <= hierarchy
    if parent in parent_map and parent_map[parent] > 0:
        assert parent_map[parent] in hierarchy


def test_get_process_hierarchy_from_windows_snapshot_mock() -> None:
    with (
        mock.patch.object(processes.sys, "platform", "win32"),
        mock.patch.object(processes, "windows_parent_map", return_value={100: 99, 99: 98, 98: 0}),
    ):
        assert get_process_hierarchy(100) == {100, 99, 98}


def test_get_process_hierarchy_windows_powershell_fallback() -> None:
    table = '[{"ProcessId":100,"ParentProcessId":99},{"ProcessId":99,"ParentProcessId":98}]'
    with (
        mock.patch.object(processes.sys, "platform", "win32"),
        mock.patch.object(processes, "windows_parent_map", side_effect=OSError("snapshot failed")),
        mock.patch.object(processes.subprocess, "run", return_value=mock.Mock(stdout=table)),
    ):
        assert get_process_hierarchy(100) == {100, 99, 98}


def test_get_process_hierarchy_posix_ps_table() -> None:
    table = "100 99\n99 98\n"
    with (
        mock.patch.object(processes.sys, "platform", "linux"),
        mock.patch.object(processes.subprocess, "run", return_value=mock.Mock(stdout=table)),
    ):
        assert get_process_hierarchy(100) == {100, 99, 98}


def test_get_process_hierarchy_posix_proc_fallback_without_ps() -> None:
    with (
        mock.patch.object(processes.sys, "platform", "linux"),
        mock.patch.object(processes.subprocess, "run", side_effect=FileNotFoundError()),
        mock.patch.object(
            Path,
            "read_text",
            side_effect=["100 (name with ) spaces) S 99 0", "99 (parent) S 1 0", "1 (init) S 0 0"],
        ),
    ):
        assert get_process_hierarchy(100) == {100, 99, 1}


def test_get_process_hierarchy_fails_closed_when_unresolvable() -> None:
    with (
        mock.patch.object(processes.sys, "platform", "linux"),
        mock.patch.object(processes.subprocess, "run", side_effect=FileNotFoundError()),
        mock.patch.object(Path, "read_text", side_effect=PermissionError("denied")),
    ):
        with pytest.raises(OSError):
            get_process_hierarchy(100)


@pytest.mark.parametrize("invalid_pid", [0, -1, -100])
def test_terminate_process_rejects_non_positive_pids(invalid_pid: int) -> None:
    with pytest.raises(ValueError, match="positive"):
        terminate_process(invalid_pid)


@pytest.mark.parametrize("force", [False, True])
@pytest.mark.parametrize("windows", [False, True])
def test_terminate_process_platform_commands_and_signals(force: bool, windows: bool) -> None:
    with (
        mock.patch.object(signal, "SIGKILL", 9, create=True),
        mock.patch.object(processes.sys, "platform", "win32" if windows else "linux"),
        mock.patch.object(processes.os, "kill") as mock_kill,
        mock.patch.object(processes.subprocess, "run") as mock_run,
    ):
        terminate_process(12345, force=force)

    if windows:
        expected_cmd = ["taskkill", "/PID", "12345"] + (["/F"] if force else [])
        assert mock_run.call_args.args[0] == expected_cmd
        mock_kill.assert_not_called()
    else:
        mock_kill.assert_called_once_with(12345, 9 if force else signal.SIGTERM)
        mock_run.assert_not_called()


@pytest.mark.parametrize("invalid_pid", [0, -1, -42])
def test_terminate_process_tree_returns_false_for_non_positive_pids(invalid_pid: int) -> None:
    assert terminate_process_tree(invalid_pid) is False


def test_terminate_process_tree_win32_uses_taskkill_force_tree() -> None:
    with (
        mock.patch.object(processes.sys, "platform", "win32"),
        mock.patch.object(processes.subprocess, "run", return_value=mock.Mock(returncode=0)) as mock_run,
    ):
        assert terminate_process_tree(12345) is True
        assert mock_run.call_args.args[0] == ["taskkill", "/F", "/T", "/PID", "12345"]

    with (
        mock.patch.object(processes.sys, "platform", "win32"),
        mock.patch.object(processes.subprocess, "run", return_value=mock.Mock(returncode=128)),
    ):
        assert terminate_process_tree(12345) is False

    with (
        mock.patch.object(processes.sys, "platform", "win32"),
        mock.patch.object(processes.subprocess, "run", side_effect=OSError("taskkill failed")),
    ):
        assert terminate_process_tree(12345) is False


def test_terminate_process_tree_posix_delegates_and_handles_failures() -> None:
    with (
        mock.patch.object(processes.sys, "platform", "linux"),
        mock.patch.object(processes, "terminate_process") as mock_term,
    ):
        assert terminate_process_tree(12345) is True
        mock_term.assert_called_once_with(12345, force=True)

    with (
        mock.patch.object(processes.sys, "platform", "linux"),
        mock.patch.object(processes, "terminate_process", side_effect=PermissionError("denied")),
    ):
        assert terminate_process_tree(12345) is False


def test_safe_kill_skips_current_and_ancestors_with_warning(capsys: pytest.CaptureFixture[str]) -> None:
    logger = CliLogger()
    with (
        mock.patch.object(processes, "get_process_hierarchy", return_value={100, 99, 98}),
        mock.patch.object(processes, "terminate_process") as mock_term,
    ):
        result = safe_kill([100, 99, 98], logger=logger, force=True)

    assert result is True
    mock_term.assert_not_called()
    err = capsys.readouterr().err
    assert err.count("Skipping protected PID") == 3
    assert "100" in err and "99" in err and "98" in err


def test_safe_kill_reports_failures_and_continues(capsys: pytest.CaptureFixture[str]) -> None:
    logger = CliLogger()
    with (
        mock.patch.object(processes, "get_process_hierarchy", return_value={100}),
        mock.patch.object(
            processes,
            "terminate_process",
            side_effect=[ProcessLookupError(), PermissionError("denied"), None],
        ) as mock_term,
    ):
        result = safe_kill([101, 102, 103], logger=logger, force=False)

    assert result is False
    assert mock_term.call_count == 3
    captured = capsys.readouterr()
    assert "PID 101 not found" in captured.err
    assert "102" in captured.err
    assert "Killed PID 103" in captured.out


def test_safe_kill_fails_closed_when_hierarchy_fails(capsys: pytest.CaptureFixture[str]) -> None:
    logger = CliLogger()
    with (
        mock.patch.object(processes, "get_process_hierarchy", side_effect=OSError("table unavailable")),
        mock.patch.object(processes, "terminate_process") as mock_term,
    ):
        result = safe_kill([12345], logger=logger)

    assert result is False
    mock_term.assert_not_called()
    assert "table unavailable" in capsys.readouterr().err


def test_is_process_alive_current_dead_and_expected_start() -> None:
    current_pid = os.getpid()
    assert is_process_alive(current_pid) is True
    assert is_process_alive(0) is False
    assert is_process_alive(-5) is False

    start_dt = get_process_start_time(current_pid)
    assert isinstance(start_dt, datetime)
    assert get_process_start_time(0) is None

    assert is_process_alive(current_pid, expected_start=start_dt, slack_seconds=5.0) is True
    stale_start = start_dt - timedelta(seconds=60)
    assert is_process_alive(current_pid, expected_start=stale_start, slack_seconds=2.0) is False

    aware_stale = datetime.now(timezone.utc) - timedelta(seconds=60)
    assert is_process_alive(current_pid, expected_start=aware_stale, slack_seconds=2.0) is False


def test_is_process_alive_dead_pid_with_mocked_os_check() -> None:
    with (
        mock.patch.object(processes.sys, "platform", "linux"),
        mock.patch.object(processes.os, "kill", side_effect=ProcessLookupError()),
    ):
        assert is_process_alive(999999) is False


def test_get_process_start_time_posix_proc_and_ps_fallback() -> None:
    stat_fields = ["S", "99"] + ["0"] * 17 + ["500", "0"]
    proc_stat_text = "1234 (proc (with) spaces) " + " ".join(stat_fields)
    with (
        mock.patch.object(processes.sys, "platform", "linux"),
        mock.patch.object(Path, "is_file", return_value=True),
        mock.patch.object(Path, "read_text", side_effect=["cpu 0\nbtime 1700000000\n", proc_stat_text]),
    ):
        dt = get_process_start_time(1234)
        assert isinstance(dt, datetime)

    with (
        mock.patch.object(processes.sys, "platform", "darwin"),
        mock.patch.object(Path, "is_file", return_value=False),
        mock.patch.object(
            processes.subprocess,
            "run",
            return_value=mock.Mock(returncode=0, stdout="Sat Nov  7 10:00:00 2026\n"),
        ),
    ):
        dt = get_process_start_time(1234)
        assert dt == datetime(2026, 11, 7, 10, 0, 0)


def test_safe_kill_called_process_error_detail(capsys: pytest.CaptureFixture[str]) -> None:
    logger = CliLogger()
    err = subprocess.CalledProcessError(128, "taskkill", stderr=b"The process was not found")
    with (
        mock.patch.object(processes, "get_process_hierarchy", return_value={100}),
        mock.patch.object(processes, "terminate_process", side_effect=err),
    ):
        assert safe_kill([999999], logger=logger) is False
    assert "The process was not found" in capsys.readouterr().err


def test_child_process_lifecycle_integration() -> None:
    child = subprocess.Popen([sys.executable, "-c", "import time; time.sleep(60)"])
    try:
        assert is_process_alive(child.pid) is True
        child_start = get_process_start_time(child.pid)
        assert isinstance(child_start, datetime)
        assert is_process_alive(child.pid, expected_start=child_start, slack_seconds=10.0) is True

        assert terminate_process_tree(child.pid) is True
        child.wait(timeout=10)

        deadline = time.monotonic() + 5.0
        while time.monotonic() < deadline and is_process_alive(child.pid):
            time.sleep(0.05)

        assert is_process_alive(child.pid) is False
    finally:
        if child.poll() is None:
            terminate_process_tree(child.pid)
            child.wait(timeout=5)
