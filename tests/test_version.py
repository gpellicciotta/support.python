"""Tests for project version resolution utilities."""

from __future__ import annotations

import os
from pathlib import Path
import tempfile
import unittest
from unittest import mock

from support_python.version import get_package_version, get_project_version


class TestVersionUtils(unittest.TestCase):
    def test_get_package_version_restores_pre_suffix(self) -> None:
        with mock.patch("importlib.metadata.version", return_value="2.0.1rc0"):
            self.assertEqual(get_package_version("x"), "2.0.1-pre")

    def test_get_package_version_keeps_release_version(self) -> None:
        with mock.patch("importlib.metadata.version", return_value="2.0.1"):
            self.assertEqual(get_package_version("x"), "2.0.1")

    def test_get_package_version_unknown_distribution(self) -> None:
        self.assertEqual(get_package_version("no-such-distribution-xyz"), "0.0.0+unknown")

    def test_get_project_version_from_gradle_properties(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            props = Path(tmpdir) / "gradle.properties"
            props.write_text("group=com.example\nversion=1.4.2\n", encoding="utf-8")
            self.assertEqual(get_project_version(tmpdir), "1.4.2")

    def test_get_project_version_from_nested_server_gradle(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            server_dir = Path(tmpdir) / "server"
            server_dir.mkdir()
            gradle_file = server_dir / "build.gradle"
            gradle_file.write_text("plugins { ... }\nversion = '2.3.0'\n", encoding="utf-8")
            self.assertEqual(get_project_version(tmpdir), "2.3.0")

    def test_get_project_version_from_nested_pyproject(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            client_dir = Path(tmpdir) / "clients" / "python"
            client_dir.mkdir(parents=True)
            pyproject = client_dir / "pyproject.toml"
            pyproject.write_text('[project]\nname = "test-client"\nversion = "0.9.5"\n', encoding="utf-8")
            self.assertEqual(get_project_version(tmpdir), "0.9.5")

    def test_get_project_version_fallback(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            empty_dir = Path(tmpdir) / "empty"
            empty_dir.mkdir()
            # If search_dir is an isolated empty directory with no repo files above it
            ver = get_project_version(empty_dir)
            self.assertTrue(isinstance(ver, str))
            self.assertTrue(len(ver) > 0)

    def test_get_project_version_env_var_fallback(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            original_env = os.environ.get("PROJECT_VERSION")
            try:
                os.environ["PROJECT_VERSION"] = "3.1.4-beta"
                self.assertEqual(get_project_version(tmpdir), "3.1.4-beta")
            finally:
                if original_env is None:
                    os.environ.pop("PROJECT_VERSION", None)
                else:
                    os.environ["PROJECT_VERSION"] = original_env


if __name__ == "__main__":
    unittest.main()
