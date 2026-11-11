from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

import pytest

from support_python.devops import DevopsCli, GradleProject, NodeProject, PythonProject
from support_python.devops.release import read_version


@pytest.fixture(
    params=[
        (GradleProject, "gradle.properties", "version=1.0.0-pre\n"),
        (PythonProject, "pyproject.toml", '[project]\nversion = "1.0.0-pre"\n'),
        (NodeProject, "package.json", '{"version": "1.0.0-pre", "name": "demo"}\n'),
    ]
)
def project(request, tmp_path):
    adapter, name, text = request.param
    (tmp_path / name).write_text(text, encoding="utf-8")
    (tmp_path / "CHANGELOG.md").write_bytes(b"# Changes\r\n\r\n## v1.0.0-pre\r\n- Pending.\r\n## v0.9.0 [2026-01-01]\r\n")
    return adapter(tmp_path)


def snapshot(root):
    return {p.name: p.read_bytes() for p in root.iterdir() if p.is_file()}


def test_set_version(project):
    before = (project.root / "CHANGELOG.md").read_bytes()
    assert project.set_version("2.0.0-pre") is True
    assert read_version(project.root) == "2.0.0-pre"
    assert (project.root / "CHANGELOG.md").read_bytes() == before.replace(b"v1.0.0-pre", b"v2.0.0-pre", 1)
    assert DevopsCli(project).run(["versions"]) == 0


@pytest.mark.parametrize("value", ["oops", "v2.0.0", "2.0", "01.0.0", "2.0.0\n", "2.0.0-rc.1"])
def test_invalid_version_changes_nothing(project, value):
    before = snapshot(project.root)
    assert DevopsCli(project).run(["versions", value]) != 0
    assert snapshot(project.root) == before


@pytest.mark.parametrize("heading", ["## v1.0.0 [released: 2026-01-01]", "# Changes", "## v1.0.0-pre [broken]"])
def test_requires_active_heading(project, heading):
    (project.root / "CHANGELOG.md").write_text(heading + "\n", encoding="utf-8")
    before = snapshot(project.root)
    assert DevopsCli(project).run(["versions", "2.0.0"]) == 1
    assert snapshot(project.root) == before


def test_dry_run(project):
    before = snapshot(project.root)
    assert DevopsCli(project).run(["versions", "2.0.0", "--dry-run"]) == 0
    assert snapshot(project.root) == before


def test_cli_sets_development_version(project):
    assert DevopsCli(project).run(["versions", "2.0.0"]) == 0
    assert read_version(project.root) == "2.0.0-pre"


def test_missing_manifest(project):
    for path in project.root.iterdir():
        if path.name != "CHANGELOG.md":
            path.unlink()
    before = snapshot(project.root)
    assert DevopsCli(project).run(["versions", "2.0.0"]) == 1
    assert snapshot(project.root) == before


@pytest.mark.slow
def test_real_gradle_entrypoint(tmp_path):
    script = tmp_path / "devops.py"
    script.write_text(
        "from pathlib import Path\nfrom support_python.devops import DevopsCli, GradleProject\n"
        "raise SystemExit(DevopsCli(GradleProject(Path(__file__).parent)).run())\n",
        encoding="utf-8",
    )
    (tmp_path / "gradle.properties").write_text("version=1.0.0-pre\n", encoding="utf-8")
    (tmp_path / "CHANGELOG.md").write_text("## v1.0.0-pre\n", encoding="utf-8")
    env = dict(os.environ, PYTHONPATH=str(Path(__file__).resolve().parents[1] / "src"))
    for args in (["versions", "2.0.0"], ["versions"]):
        result = subprocess.run([sys.executable, str(script), *args], env=env, capture_output=True, text=True, timeout=30)
        assert result.returncode == 0, result.stdout + result.stderr
    assert read_version(tmp_path) == "2.0.0-pre"
