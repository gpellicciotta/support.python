"""Tests for environment file parsing in support_python.env."""

from __future__ import annotations

from pathlib import Path
import tempfile
import unittest

from support_python.env import read_env_file


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


if __name__ == "__main__":
    unittest.main()
