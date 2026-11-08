"""Tests for the standalone scripts/lint-markdown.py wrapper."""

from __future__ import annotations

from pathlib import Path
import subprocess
import sys

SCRIPT_PATH = Path(__file__).resolve().parent.parent / "scripts" / "lint-markdown.py"


def run_script(*args: str, cwd: Path | None = None) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(SCRIPT_PATH), *args], capture_output=True, text=True, encoding="utf-8", cwd=cwd, timeout=60
    )


def test_script_reports_version() -> None:
    result = run_script("version")
    assert result.returncode == 0
    assert result.stdout.startswith("lint-markdown v")


def test_script_checks_clean_file_and_flags_bad_file(tmp_path: Path) -> None:
    clean = tmp_path / "clean.md"
    clean.write_text("# Title\n\nSome text.\n", encoding="utf-8")
    assert run_script("check", "--offline", str(clean)).returncode == 0

    bad = tmp_path / "bad.md"
    bad.write_text("# Title\n\nThese items:\n\n- a\n- b\n", encoding="utf-8")
    assert run_script("check", "--offline", str(bad)).returncode != 0
