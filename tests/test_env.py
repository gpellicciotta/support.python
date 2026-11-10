"""Tests for environment file parsing in support_python.env."""

from __future__ import annotations

import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest import mock

from support_python.env import read_env_file, user_config_dir, user_config_path


class TestEnvUtils(unittest.TestCase):
    def test_read_env_file_parses_entries(self) -> None:
        with tempfile.NamedTemporaryFile("w", encoding="utf-8", delete=False) as f:
            f.write(
                "# Comment header\n"
                "KEY1=val1\n"
                "\n"
                "KEY2='single_quoted'\n"
                'KEY3="double_quoted"\n'
                "KEY4=val with spaces\n"
                "KEY5=nested=value\n"
                "INVALID_NO_EQUALS\n"
                "  # Indented comment\n"
            )
            tmp_path = Path(f.name)

        try:
            parsed = read_env_file(tmp_path)
            self.assertEqual(parsed.get("KEY1"), "val1")
            self.assertEqual(parsed.get("KEY2"), "single_quoted")
            self.assertEqual(parsed.get("KEY3"), "double_quoted")
            self.assertEqual(parsed.get("KEY4"), "val with spaces")
            self.assertEqual(parsed.get("KEY5"), "nested=value")
            self.assertNotIn("INVALID_NO_EQUALS", parsed)
            self.assertEqual(len(parsed), 5)
        finally:
            tmp_path.unlink(missing_ok=True)

    def test_read_env_file_missing_file_returns_empty(self) -> None:
        missing_path = Path(tempfile.gettempdir()) / "non_existent_env_file_12345.env"
        self.assertEqual(read_env_file(missing_path), {})


class UserConfigPathTests(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.absolute = Path(self._tmp.name).resolve()

    def test_absolute_xdg_config_home_wins_on_every_platform(self) -> None:
        environ = {"XDG_CONFIG_HOME": str(self.absolute / "xdg"), "APPDATA": str(self.absolute / "roaming")}
        for platform in ("linux", "darwin", "win32"):
            with self.subTest(platform=platform):
                self.assertEqual(user_config_dir("demo", environ=environ, platform=platform), self.absolute / "xdg" / "demo")

    def test_empty_or_relative_xdg_config_home_is_ignored(self) -> None:
        for value in ("", "relative/config", "~/.config"):
            with self.subTest(value=value):
                self.assertEqual(
                    user_config_dir("demo", environ={"XDG_CONFIG_HOME": value}, platform="linux"),
                    Path.home() / ".config" / "demo",
                )
                self.assertEqual(
                    user_config_dir("demo", environ={"XDG_CONFIG_HOME": value, "APPDATA": str(self.absolute)}, platform="win32"),
                    self.absolute / "demo",
                )

    def test_windows_uses_appdata_with_roaming_fallback(self) -> None:
        self.assertEqual(user_config_dir("demo", environ={"APPDATA": str(self.absolute)}, platform="win32"), self.absolute / "demo")
        for environ in ({}, {"APPDATA": ""}, {"APPDATA": "relative/roaming"}):
            with self.subTest(environ=environ):
                self.assertEqual(
                    user_config_dir("demo", environ=environ, platform="win32"), Path.home() / "AppData" / "Roaming" / "demo"
                )

    def test_other_platforms_use_dot_config(self) -> None:
        for platform in ("linux", "darwin"):
            with self.subTest(platform=platform):
                self.assertEqual(
                    user_config_dir("demo", environ={"APPDATA": str(self.absolute)}, platform=platform),
                    Path.home() / ".config" / "demo",
                )

    def test_user_config_path_appends_file_name(self) -> None:
        environ = {"XDG_CONFIG_HOME": str(self.absolute)}
        self.assertEqual(user_config_path("demo", environ=environ, platform="linux"), self.absolute / "demo" / "config.json")
        self.assertEqual(
            user_config_path("demo", "settings.json", environ=environ, platform="linux"), self.absolute / "demo" / "settings.json"
        )

    def test_defaults_read_os_environ_and_sys_platform(self) -> None:
        with mock.patch.dict("os.environ", {"XDG_CONFIG_HOME": str(self.absolute)}):
            self.assertEqual(user_config_path("demo"), self.absolute / "demo" / "config.json")

    def test_invalid_tool_names_raise(self) -> None:
        for name in ("", "a/b", "a\\b", ".", "..", "D:foo"):
            with self.subTest(name=name), self.assertRaises(ValueError):
                user_config_dir(name, environ={}, platform="linux")

    def test_package_root_exports_helpers(self) -> None:
        import support_python
        import support_python.env

        for name in ("user_config_dir", "user_config_path"):
            with self.subTest(name=name):
                self.assertIn(name, support_python.__all__)
                self.assertIs(getattr(support_python, name), getattr(support_python.env, name))

    def test_subprocess_resolves_xdg_config_home(self) -> None:
        src_dir = Path(__file__).resolve().parent.parent / "src"
        env = {**os.environ, "XDG_CONFIG_HOME": str(self.absolute), "PYTHONPATH": str(src_dir)}
        result = subprocess.run(
            [sys.executable, "-c", "import support_python; print(support_python.user_config_path('demo'))"],
            capture_output=True,
            text=True,
            env=env,
            timeout=60,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(Path(result.stdout.strip()), self.absolute / "demo" / "config.json")


if __name__ == "__main__":
    unittest.main()
