"""Tests for the standalone scripts/agent-files.py wrapper."""

from __future__ import annotations

from pathlib import Path
import subprocess
import sys

SCRIPT_PATH = Path(__file__).resolve().parent.parent / "scripts" / "agent-files.py"


def run_script(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run([sys.executable, str(SCRIPT_PATH), *args], capture_output=True, text=True, encoding="utf-8", timeout=60)


def test_script_reports_version() -> None:
    result = run_script("version")
    assert result.returncode == 0
    assert result.stdout.startswith("update-global-agent-files v")


def test_script_lists_tools() -> None:
    result = run_script("list")
    assert result.returncode == 0
    assert result.stdout.strip()
