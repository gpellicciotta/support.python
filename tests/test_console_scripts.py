"""Unit and integration tests for installed console scripts and removed entry points."""

from __future__ import annotations

import importlib
import importlib.metadata
from pathlib import Path
import subprocess
import sys
import sysconfig

import pytest

import support_python
from support_python import cli
from support_python.tools import agent_files, git_repository_backup, lint_markdown, processes

EXPECTED_SCRIPTS = {
    "processes": "support_python.tools.processes:main",
    "agent-files": "support_python.tools.agent_files:main",
    "lint-markdown": "support_python.tools.lint_markdown:main",
    "git-repository-backup": "support_python.tools.git_repository_backup:main",
}


def resolve_console_script(name: str) -> str:
    """Resolve an installed console script executable in the active Python environment."""
    search_dirs = [Path(sysconfig.get_path("scripts")), Path(sys.executable).parent]
    for scripts_dir in search_dirs:
        for suffix in ("", ".exe", ".cmd", ".bat"):
            candidate = scripts_dir / f"{name}{suffix}"
            if candidate.is_file():
                return str(candidate)
    raise AssertionError(f"Console script '{name}' not found in {search_dirs}")


def run_console_script(name: str, *args: str, cwd: Path | None = None) -> subprocess.CompletedProcess[str]:
    """Run an installed console script as a subprocess and return the completed process."""
    executable = resolve_console_script(name)
    return subprocess.run(
        [executable, *args],
        capture_output=True,
        text=True,
        encoding="utf-8",
        cwd=cwd,
        timeout=60,
    )


def test_distribution_console_scripts_match_expected() -> None:
    dist = importlib.metadata.distribution("support-python")
    console_eps = {ep.name: ep.value for ep in dist.entry_points if ep.group == "console_scripts"}
    assert console_eps == EXPECTED_SCRIPTS
    assert "support-python" not in console_eps


def test_support_python_main_and_cli_demo_removed() -> None:
    with pytest.raises(ModuleNotFoundError):
        importlib.import_module("support_python.__main__")

    for removed_name in ("main", "_build_demo_parser", "format_support_message", "PROG", "DESCRIPTION", "ACTIONS"):
        assert not hasattr(cli, removed_name), f"support_python.cli still has {removed_name}"
        assert removed_name not in cli.__all__
        assert not hasattr(support_python, removed_name), f"support_python still exports {removed_name}"
        assert removed_name not in support_python.__all__


def test_agent_files_banner_and_usage_name() -> None:
    assert agent_files.TOOL_NAME == "agent-files"
    harness = agent_files.build_harness()
    assert harness.name == "agent-files"
    assert harness.format_version().startswith("agent-files v")
    help_text = harness.format_help(verbose=True)
    assert "Usage:\n  agent-files list" in help_text
    assert "update-global-agent-files" not in help_text


def test_each_tool_harness_version_banner() -> None:
    expected_banners = [
        (processes.build_harness(), "processes v"),
        (agent_files.build_harness(), "agent-files v"),
        (lint_markdown.build_harness(), "lint-markdown v"),
        (git_repository_backup.build_harness(), "backup-git-repos v"),
    ]
    for harness, prefix in expected_banners:
        assert harness.format_version().startswith(prefix)


@pytest.mark.parametrize(
    ("script_name", "expected_prefix"),
    [
        ("processes", "processes v"),
        ("agent-files", "agent-files v"),
        ("lint-markdown", "lint-markdown v"),
        ("git-repository-backup", "backup-git-repos v"),
    ],
)
def test_console_script_version_action(script_name: str, expected_prefix: str) -> None:
    result = run_console_script(script_name, "version")
    assert result.returncode == 0, result.stderr
    assert result.stdout.startswith(expected_prefix)
    assert " - Copyright (c) Giovanni Pellicciotta" in result.stdout


def test_agent_files_console_script_lists_tools() -> None:
    result = run_console_script("agent-files", "list")
    assert result.returncode == 0, result.stderr
    assert "Configured AI tools" in result.stdout


def test_lint_markdown_console_script_checks_files_and_docs(tmp_path: Path) -> None:
    clean = tmp_path / "clean.md"
    clean.write_text("# Title\n\nSome text.\n", encoding="utf-8")
    assert run_console_script("lint-markdown", "check", "--offline", str(clean)).returncode == 0

    bad = tmp_path / "bad.md"
    bad.write_text("# Title\n\nThese items:\n\n- a\n- b\n", encoding="utf-8")
    bad_res = run_console_script("lint-markdown", "check", "--offline", str(bad))
    assert bad_res.returncode == 1
    assert "MD007" in bad_res.stdout or "bad.md" in bad_res.stdout

    repo_root = Path(__file__).resolve().parent.parent
    docs_res = run_console_script("lint-markdown", "check", "--offline", "docs", cwd=repo_root)
    assert docs_res.returncode in (0, 1)
    assert "markdown files" in docs_res.stdout
