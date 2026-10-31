"""Tests for scripts/extract-release-notes.py."""

from __future__ import annotations

import importlib.util
import sys
import unittest
from pathlib import Path

_PATH = Path(__file__).resolve().parent.parent / "scripts" / "extract-release-notes.py"
_spec = importlib.util.spec_from_file_location("extract_release_notes", _PATH)
extract_release_notes = importlib.util.module_from_spec(_spec)
sys.modules[_spec.name] = extract_release_notes
_spec.loader.exec_module(extract_release_notes)

CHANGELOG = """# Changes

## v2.0.1-pre
- Pending.

## v2.0.1 [released: 2026-10-01]
- Fixed one.
- Fixed two.

## v2.0.10 [released: 2026-10-02]
- Different.
"""


class TestExtractReleaseNotes(unittest.TestCase):
    def test_extracts_section_with_or_without_v_prefix(self) -> None:
        expected = "- Fixed one.\n- Fixed two."
        self.assertEqual(extract_release_notes.extract_release_notes(CHANGELOG, "2.0.1"), expected)
        self.assertEqual(extract_release_notes.extract_release_notes(CHANGELOG, "v2.0.1"), expected)

    def test_does_not_match_longer_version(self) -> None:
        self.assertEqual(extract_release_notes.extract_release_notes(CHANGELOG, "2.0.10"), "- Different.")

    def test_pre_heading_is_found_by_exact_version(self) -> None:
        self.assertEqual(extract_release_notes.extract_release_notes(CHANGELOG, "2.0.1-pre"), "- Pending.")

    def test_missing_version_raises(self) -> None:
        with self.assertRaises(ValueError):
            extract_release_notes.extract_release_notes(CHANGELOG, "9.9.9")


if __name__ == "__main__":
    unittest.main()
