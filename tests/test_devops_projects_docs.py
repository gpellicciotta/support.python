from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path
from unittest.mock import Mock

import pytest

from support_python.devops import DevopsCli, DocsProject, ReleasePipeline


@pytest.mark.parametrize("action,command", [("lint", "check"), ("format", "fix"), ("check", "check")])
@pytest.mark.parametrize("code", [0, 1])
def test_markdown_commands(tmp_path, monkeypatch, action, command, code):
    monkeypatch.setattr("support_python.devops.projects.resolve_executable", lambda name: "lint-markdown.exe")
    runner = Mock(return_value=code)
    project = DocsProject(tmp_path, runner=runner)
    assert getattr(project, action)() is (code == 0)
    runner.assert_called_once_with(["lint-markdown.exe", command, "--offline"], tmp_path.resolve(), project.logger)


@pytest.mark.parametrize("action", ["lint", "format", "check"])
def test_missing_linter(tmp_path, monkeypatch, action):
    monkeypatch.setattr("support_python.devops.projects.resolve_executable", lambda name: None)
    runner = Mock()
    assert getattr(DocsProject(tmp_path, runner=runner), action)() is False
    runner.assert_not_called()


def test_skipped_operations(tmp_path):
    runner = Mock()
    project = DocsProject(tmp_path, runner=runner)
    assert project.test(["anything"])
    assert project.test_slow()
    assert project.build()
    assert project.clean()
    assert project.release_assets() == []
    assert project.release(skip_checks=True, skip_github_release=True) is None
    runner.assert_not_called()
    assert list(tmp_path.iterdir()) == []
    assert "skipped" in project.action_summaries()["test"]


def test_release_dry_run(tmp_path, monkeypatch, capsys):
    (tmp_path / "CHANGELOG.md").write_text("# Changes\n\n---\n\n## v1.0.0-pre\n- Docs: Added guidance.\n", encoding="utf-8")
    before = (tmp_path / "CHANGELOG.md").read_bytes()

    def query(argv, cwd):
        assert cwd == tmp_path
        assert argv[0] == "git"
        if argv[1:3] == ["branch", "--show-current"]:
            return 0, "main"
        if argv[1:3] == ["rev-list", "--count"]:
            return 0, "0"
        if argv[1] == "remote":
            return 0, "https://github.com/example/docs.git"
        if argv[1] == "rev-parse":
            return 1, ""
        return 0, ""

    monkeypatch.setattr("support_python.devops.cli.ReleasePipeline", lambda **kwargs: ReleasePipeline(query=query, **kwargs))
    runner = Mock(return_value=0)
    cli = DevopsCli(DocsProject(tmp_path, runner=runner))
    assert cli.run(["release", "--dry-run", "--skip-checks", "--skip-github-release"]) == 0
    output = capsys.readouterr().out
    assert "CHANGELOG.md" in output
    assert "v1.0.1-pre" in output
    assert (tmp_path / "CHANGELOG.md").read_bytes() == before
    runner.assert_not_called()


@pytest.mark.slow
def test_real_docs_entrypoint(tmp_path):
    script = tmp_path / "devops.py"
    script.write_text(
        "from pathlib import Path\nfrom support_python.devops import DevopsCli, DocsProject\n"
        "raise SystemExit(DevopsCli(DocsProject(Path(__file__).parent)).run())\n",
        encoding="utf-8",
    )
    readme = tmp_path / "README.md"
    readme.write_text("# Documentation\n\nProject guidance.\n", encoding="utf-8")
    env = dict(os.environ, PYTHONPATH=str(Path(__file__).resolve().parents[1] / "src"))
    env["PATH"] = str(Path(sys.executable).parent) + os.pathsep + env["PATH"]
    for args in (["check"], ["format"], ["test"], ["build"], ["clean"]):
        result = subprocess.run([sys.executable, str(script), *args], env=env, capture_output=True, text=True, timeout=30)
        assert result.returncode == 0, result.stdout + result.stderr
    readme.write_text("# Documentation\n\n[Missing](missing.md)\n", encoding="utf-8")
    result = subprocess.run([sys.executable, str(script), "check"], env=env, capture_output=True, text=True, timeout=30)
    assert result.returncode == 1, result.stdout + result.stderr
