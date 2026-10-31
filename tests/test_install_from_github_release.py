"""Tests for scripts/install-from-github-release.py."""

from __future__ import annotations

import importlib.util
import sys
import unittest
from pathlib import Path
from unittest import mock

_PATH = Path(__file__).resolve().parent.parent / "scripts" / "install-from-github-release.py"
_spec = importlib.util.spec_from_file_location("install_from_github_release", _PATH)
installer = importlib.util.module_from_spec(_spec)
sys.modules[_spec.name] = installer
_spec.loader.exec_module(installer)

URL = "https://github.com/acme/my-pkg/releases/download/v1.2.3/my_pkg-1.2.3-py3-none-any.whl"


class TestParsing(unittest.TestCase):
    def test_parse_github_repo_variants(self) -> None:
        for remote in (
            "https://github.com/acme/my-pkg.git",
            "https://github.com/acme/my-pkg",
            "git@github.com:acme/my-pkg.git\n",
            "ssh://git@github.com/acme/my-pkg.git",
        ):
            self.assertEqual(installer.parse_github_repo(remote), "acme/my-pkg", remote)

    def test_parse_github_repo_rejects_other_hosts(self) -> None:
        with self.assertRaises(ValueError):
            installer.parse_github_repo("https://gitlab.com/acme/my-pkg.git")

    def test_read_project_name_uses_project_table_only(self) -> None:
        text = '[build-system]\nname = "wrong"\n\n[project]\nname = "my-pkg"\nversion = "1.0.0"\n'
        self.assertEqual(installer.read_project_name(text), "my-pkg")

    def test_read_project_name_missing_raises(self) -> None:
        with self.assertRaises(ValueError):
            installer.read_project_name('[tool.x]\nname = "x"\n')

    def test_wheel_filename_normalizes_name(self) -> None:
        self.assertEqual(installer.wheel_filename("My-Pkg.core", "1.2.3"), "My_Pkg_core-1.2.3-py3-none-any.whl")

    def test_release_asset_url(self) -> None:
        self.assertEqual(installer.release_asset_url("acme/my-pkg", "1.2.3", "my_pkg-1.2.3-py3-none-any.whl"), URL)


class TestInstallCommand(unittest.TestCase):
    def test_local_install_uses_pip(self) -> None:
        self.assertEqual(installer.build_install_command(URL, False, True), [sys.executable, "-m", "pip", "install", URL])

    def test_global_prefers_pipx(self) -> None:
        self.assertEqual(installer.build_install_command(URL, True, True), ["pipx", "install", URL, "--force"])

    def test_global_falls_back_to_pip_user(self) -> None:
        expected = [sys.executable, "-m", "pip", "install", "--user", URL]
        self.assertEqual(installer.build_install_command(URL, True, False), expected)


class TestMain(unittest.TestCase):
    def test_dry_run_with_explicit_repo_and_package(self) -> None:
        with mock.patch.object(installer.subprocess, "run") as run:
            code = installer.main(["v1.2.3", "--repo", "acme/my-pkg", "--package", "my-pkg", "--dry-run"])
        self.assertEqual(code, 0)
        run.assert_not_called()

    def test_failed_install_returns_2(self) -> None:
        with mock.patch.object(installer.subprocess, "run", return_value=mock.Mock(returncode=1)):
            code = installer.main(["1.2.3", "--repo", "acme/my-pkg", "--package", "my-pkg"])
        self.assertEqual(code, 2)

    def test_successful_install_runs_wheel_url(self) -> None:
        with mock.patch.object(installer.subprocess, "run", return_value=mock.Mock(returncode=0)) as run:
            code = installer.main(["1.2.3", "--repo", "acme/my-pkg", "--package", "my-pkg"])
        self.assertEqual(code, 0)
        self.assertEqual(run.call_args.args[0][-1], URL)

    def test_missing_pyproject_returns_1(self) -> None:
        with mock.patch.object(installer, "_local_package", side_effect=ValueError("no pyproject")):
            self.assertEqual(installer.main(["1.2.3", "--repo", "acme/my-pkg"]), 1)


if __name__ == "__main__":
    unittest.main()
