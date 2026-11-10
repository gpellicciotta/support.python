"""Guards src/ against standard-library calls that Python 3.9, the oldest supported version, rejects."""

from __future__ import annotations

import ast
import unittest
from pathlib import Path

SRC_DIR = Path(__file__).resolve().parent.parent / "src" / "support_python"


class Python39CompatibilityTests(unittest.TestCase):
    def test_no_write_text_or_read_text_newline_argument(self) -> None:
        # Path.write_text(newline=...) arrived in Python 3.10; Path.read_text has no newline argument before 3.13.
        offenders: list[str] = []
        for source in sorted(SRC_DIR.rglob("*.py")):
            tree = ast.parse(source.read_text(encoding="utf-8"), filename=str(source))
            for node in ast.walk(tree):
                if (
                    isinstance(node, ast.Call)
                    and isinstance(node.func, ast.Attribute)
                    and node.func.attr in ("write_text", "read_text")
                    and any(keyword.arg == "newline" for keyword in node.keywords)
                ):
                    offenders.append(f"{source.relative_to(SRC_DIR).as_posix()}:{node.lineno}")
        self.assertEqual(offenders, [])


if __name__ == "__main__":
    unittest.main()
