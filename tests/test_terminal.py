"""Tests for terminal utilities."""

from __future__ import annotations

import unittest

from support_python.terminal import configure_utf8_output


class TestTerminalUtils(unittest.TestCase):
    def test_configure_utf8_output_executes_safely(self) -> None:
        # Should not throw any exception
        configure_utf8_output()


if __name__ == "__main__":
    unittest.main()
