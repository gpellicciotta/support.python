"""Tests for --help and --version on the standalone scripts under scripts/."""

from __future__ import annotations

import os
import re
import subprocess
import sys
from pathlib import Path

import pytest

SCRIPTS_DIR = Path(__file__).resolve().parent.parent / "scripts"
SCRIPTS = [
    "extract-release-notes",
    "migrate-namespace",
    "reset-history",
    "install-from-github-release",
]


def run_script(name: str, *args: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(SCRIPTS_DIR / f"{name}.py"), *args],
        cwd=SCRIPTS_DIR,
        capture_output=True,
        text=True,
        encoding="utf-8",
        env={**os.environ, "PYTHONUTF8": "1"},
    )


@pytest.mark.parametrize("name", SCRIPTS)
def test_version_prints_header_and_exits_zero(name: str) -> None:
    result = run_script(name, "--version")
    assert result.returncode == 0, result.stderr
    assert re.fullmatch(rf"{name} v\S+ - Copyright \(c\) Giovanni Pellicciotta", result.stdout.strip())


@pytest.mark.parametrize("name", SCRIPTS)
def test_help_exits_zero_and_shows_usage(name: str) -> None:
    result = run_script(name, "--help")
    assert result.returncode == 0, result.stderr
    assert "usage:" in result.stdout.lower()
    assert "--version" in result.stdout


def test_migrate_namespace_new_version_option_replaces_version() -> None:
    assert "--new-version" in run_script("migrate-namespace", "--help").stdout


def test_reset_history_reinit_new_version_option_replaces_version() -> None:
    assert "--new-version" in run_script("reset-history", "reinit", "--help").stdout
