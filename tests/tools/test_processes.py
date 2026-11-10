"""Unit and integration tests for the processes CLI and process filtering."""

from __future__ import annotations

import contextlib
from datetime import datetime
import io
import json
import os
from pathlib import Path
import subprocess
import sys
import time
from unittest import mock

import pytest

from support_python.tables import render_output
from support_python.tools.processes import build_harness, main, normalize_argv
import support_python.processes as processes
from support_python.processes import (
    ProcessInfo,
    filter_processes,
    find_pids_with_open_path,
    get_process_cwd,
    get_process_descendants,
    list_processes,
)


def run_cli(argv: list[str]) -> tuple[int, str, str]:
    """Run tools.processes.main capturing exit code, stdout, and stderr."""
    out, err = io.StringIO(), io.StringIO()
    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
        code = main(argv)
    return code, out.getvalue(), err.getvalue()


def test_old_cli_module_paths_no_longer_import() -> None:
    import importlib

    for old_mod in (
        "support_python.cli_processes",
        "support_python.agent_files",
        "support_python.agent_files_config",
        "support_python.backup",
    ):
        with pytest.raises(ModuleNotFoundError):
            importlib.import_module(old_mod)
    res = subprocess.run(
        [sys.executable, "-c", "import sys, support_python; assert 'support_python.tools.agent_files' not in sys.modules"],
        capture_output=True,
        text=True,
        timeout=30,
    )
    assert res.returncode == 0, res.stderr


def test_cli_help_version_normalization_and_parser() -> None:
    code, out, err = run_cli([])
    assert code == 0 and "Usage:" in out and out.startswith("processes v") and err == ""
    assert run_cli(["help"])[0] == 0 and run_cli(["version"])[0] == 0
    assert run_cli(["--help"])[0] == 0 and run_cli(["--version"])[0] == 0
    assert "Detailed Action Descriptions:" in run_cli(["help", "--verbose"])[1]
    assert normalize_argv(["1234", "--debug"]) == ["kill", "1234", "--debug"]
    assert normalize_argv(["--force", "1234"]) == ["kill", "--force", "1234"]
    assert normalize_argv(["list", "--cwd", "."]) == ["list", "--cwd", "."]
    assert normalize_argv(["kill", "--help"]) == ["help", "kill"]
    assert normalize_argv(["list", "--help"]) == ["help", "list"]
    assert normalize_argv(["kill", "1234", "--version"]) == ["version"]

    harness = build_harness()
    kill_args = harness._build_parser("kill").parse_args(["123", "456", "--force"])
    assert kill_args.pids == [123, 456] and kill_args.force is True
    list_args = harness._build_parser("list").parse_args(
        [
            "--cwd",
            "/tmp/w",
            "--open-path",
            "/tmp/w/f.txt",
            "--started-before",
            "2026-11-07T12:00:00",
            "--started-after",
            "2026-11-07T10:00:00",
            "--ancestors-of",
            "200",
            "--descendants-of",
            "100",
            "--format",
            "json",
        ]
    )
    assert list_args.cwd == "/tmp/w" and list_args.open_path == "/tmp/w/f.txt" and list_args.format == "json"
    assert list_args.started_before == datetime(2026, 11, 7, 12, 0, 0) and list_args.started_after == datetime(
        2026, 11, 7, 10, 0, 0
    )
    assert list_args.ancestors_of == 200 and list_args.descendants_of == 100
    for bad in (
        ["kill"],
        ["kill", "0"],
        ["kill", "-5"],
        ["kill", "abc"],
        ["list", "--ancestors-of", "0"],
        ["list", "--descendants-of", "abc"],
        ["list", "--started-before", "bad"],
        ["list", "--started-after", "bad"],
    ):
        assert run_cli(bad)[0] == 2


def test_filter_processes_descendants_and_posix_fallbacks(tmp_path: Path) -> None:
    dir_a, dir_b = tmp_path / "dir_a", tmp_path / "dir_b"
    sub_a = dir_a / "sub"
    sub_a.mkdir(parents=True)
    dir_b.mkdir()
    t1, t2, t3 = datetime(2026, 11, 7, 9, 0), datetime(2026, 11, 7, 10, 0), datetime(2026, 11, 7, 11, 0)
    sample = [
        ProcessInfo(pid=10, ppid=1, name="root", started=t1, cwd=str(dir_a)),
        ProcessInfo(pid=20, ppid=10, name="mid", started=t2, cwd=str(sub_a)),
        ProcessInfo(pid=30, ppid=20, name="leaf", started=t3, cwd=str(dir_b)),
    ]
    pmap = {10: 1, 20: 10, 30: 20}
    assert [p.pid for p in filter_processes(sample, cwd=dir_a, parent_map=pmap)] == [10, 20]
    assert [p.pid for p in filter_processes(sample, open_path=dir_b / "f.txt", open_pids={30}, parent_map=pmap)] == [30]
    assert [p.pid for p in filter_processes(sample, started_before=t2, parent_map=pmap)] == [10, 20]
    assert [p.pid for p in filter_processes(sample, started_after=t2, parent_map=pmap)] == [20, 30]
    assert [p.pid for p in filter_processes(sample, ancestors_of=20, parent_map=pmap)] == [10, 20]
    assert [p.pid for p in filter_processes(sample, descendants_of=20, parent_map=pmap)] == [20, 30]
    assert get_process_descendants(10, parent_map={1: 0, 10: 1, 20: 10, 21: 10, 30: 20}) == {10, 20, 21, 30}
    with pytest.raises(OSError):
        get_process_descendants(0, parent_map=pmap)
    assert get_process_cwd(0) is None and get_process_cwd(os.getpid()) == Path.cwd().resolve()
    with (
        mock.patch.object(processes.sys, "platform", "darwin"),
        mock.patch.object(Path, "is_dir", return_value=False),
        mock.patch.object(processes.subprocess, "run", return_value=mock.Mock(returncode=0, stdout="p1234\np5678\n")),
    ):
        assert find_pids_with_open_path(tmp_path) == {1234, 5678}


def test_processes_kill_protects_self_and_ancestors_and_reports_failures() -> None:
    with (
        mock.patch.object(processes, "get_process_hierarchy", return_value={100, 50, 1}),
        mock.patch.object(processes, "terminate_process") as mock_term,
    ):
        code, _, err = run_cli(["kill", "100", "50", "1", "--force"])
    assert code == 0 and mock_term.call_count == 0 and err.count("Skipping protected PID") == 3
    with (
        mock.patch.object(processes, "get_process_hierarchy", return_value={100}),
        mock.patch.object(processes, "terminate_process", side_effect=PermissionError("denied")),
    ):
        code, _, err = run_cli(["kill", "200"])
    assert code == 1 and "Permission denied to kill PID 200" in err


def test_processes_kill_dry_run_reports_targets_without_terminating() -> None:
    harness = build_harness()
    assert harness._build_parser("kill").parse_args(["123"]).dry_run is False
    assert harness._build_parser("kill").parse_args(["123", "--dry-run"]).dry_run is True
    assert normalize_argv(["1234", "--dry-run"]) == ["kill", "1234", "--dry-run"]
    with (
        mock.patch.object(processes, "get_process_hierarchy", return_value={100, 1}),
        mock.patch.object(processes, "terminate_process") as mock_term,
        mock.patch.object(processes, "terminate_process_tree") as mock_tree,
    ):
        code, out, err = run_cli(["kill", "100", "200", "300", "--dry-run", "--force"])
    assert code == 0 and mock_term.call_count == 0 and mock_tree.call_count == 0
    assert "Would kill PID 200" in out and "Would kill PID 300" in out and "Killed PID" not in out
    assert "Would skip protected PID 100" in err and "PID 200" not in err
    with mock.patch.object(processes, "get_process_hierarchy", side_effect=OSError("denied")):
        assert run_cli(["kill", "200", "--dry-run"])[0] == 1


def test_processes_list_text_format_matches_former_table_output() -> None:
    sample = [
        ProcessInfo(pid=10, ppid=1, name="root", started=datetime(2026, 11, 7, 9, 0), cwd="/w"),
        ProcessInfo(pid=20, ppid=10, name="leaf", started=datetime(2026, 11, 7, 10, 0), cwd="/w/sub"),
    ]
    expected = io.StringIO()
    render_output(sample, output_format="table", file=expected)
    with mock.patch("support_python.tools.processes.list_processes", return_value=sample):
        default_code, default_out, _ = run_cli(["list"])
        text_code, text_out, _ = run_cli(["list", "--format", "text"])
        json_code, json_out, _ = run_cli(["list", "--format", "json"])
        table_code, _, table_err = run_cli(["list", "--format", "table"])
    assert default_code == 0 and expected.getvalue() in default_out
    assert text_code == 0 and expected.getvalue() in text_out
    assert json_code == 0 and [p["pid"] for p in json.loads(json_out)] == [10, 20]
    assert table_code == 2 and "table" in table_err
    assert build_harness()._build_parser("list").parse_args([]).format == "text"


def test_processes_kill_dry_run_integration() -> None:
    child = subprocess.Popen([sys.executable, "-c", "import time; time.sleep(60)"])
    processes_bin = str(Path(sys.executable).parent / ("processes.exe" if sys.platform == "win32" else "processes"))
    try:
        assert processes.is_process_alive(child.pid) is True
        dry_res = subprocess.run([processes_bin, "kill", str(child.pid), "--dry-run"], capture_output=True, text=True, timeout=30)
        assert dry_res.returncode == 0 and f"Would kill PID {child.pid}" in dry_res.stdout
        time.sleep(0.5)
        assert child.poll() is None and processes.is_process_alive(child.pid) is True
        # Windows taskkill without /F cannot stop a windowless console process, so the real kill forces it.
        kill_res = subprocess.run([processes_bin, "kill", str(child.pid), "--force"], capture_output=True, text=True, timeout=30)
        assert kill_res.returncode == 0 and f"Killed PID {child.pid}" in kill_res.stdout
        child.wait(timeout=10)
        assert processes.is_process_alive(child.pid) is False
    finally:
        if child.poll() is None:
            subprocess.run([processes_bin, "kill", str(child.pid), "--force"], capture_output=True, text=True, timeout=30)
            child.wait(timeout=10)


def test_processes_list_and_kill_integration(tmp_path: Path) -> None:
    work_dir = tmp_path / "child_cwd"
    work_dir.mkdir()
    open_file, ready_file = work_dir / "locked_resource.txt", work_dir / "ready.txt"
    open_file.write_text("active resource\n", encoding="utf-8")
    child_code = "import pathlib, time\nfh = open('locked_resource.txt', 'r+', encoding='utf-8')\npathlib.Path('ready.txt').write_text('ok', encoding='utf-8')\ntime.sleep(60)\n"
    child = subprocess.Popen([sys.executable, "-c", child_code], cwd=str(work_dir))
    try:
        deadline = time.monotonic() + 10.0
        while time.monotonic() < deadline and not ready_file.exists():
            time.sleep(0.05)
        assert ready_file.exists() and get_process_cwd(child.pid) == work_dir.resolve()
        assert child.pid in find_pids_with_open_path(open_file)
        assert any(p.pid == child.pid for p in list_processes(cwd=work_dir))
        assert any(p.pid == child.pid for p in list_processes(open_path=open_file))
        assert str(child.pid) in run_cli(["list", "--cwd", str(work_dir), "--format", "json"])[1]
        assert str(child.pid) in run_cli(["list", "--open-path", str(open_file)])[1]
        processes_bin = str(Path(sys.executable).parent / ("processes.exe" if sys.platform == "win32" else "processes"))
        list_res = subprocess.run(
            [processes_bin, "list", "--cwd", str(work_dir)],
            capture_output=True,
            text=True,
            timeout=30,
        )
        assert list_res.returncode == 0 and str(child.pid) in list_res.stdout
        kill_res = subprocess.run(
            [processes_bin, "kill", str(child.pid), "--force"],
            capture_output=True,
            text=True,
            timeout=30,
        )
        assert kill_res.returncode == 0 and f"Killed PID {child.pid}" in kill_res.stdout
        child.wait(timeout=10)
        assert processes.is_process_alive(child.pid) is False
    finally:
        if child.poll() is None:
            processes.terminate_process_tree(child.pid)
            child.wait(timeout=5)


def test_processes_help_uses_mustache_placeholders(capsys: pytest.CaptureFixture[str]) -> None:
    """Help text writes placeholders as ``{{name}}``, never as sample paths or single braces."""
    from support_python.tools import processes as processes_tool

    assert processes_tool.main(["help", "--verbose"]) == 0
    out = capsys.readouterr().out
    assert "processes kill {{pid}}... [options]" in out
    assert "processes list --cwd {{project-root}}" in out
    assert "/path/to/" not in out
