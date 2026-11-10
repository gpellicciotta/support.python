"""Tests for scripts/extract-release-notes.py."""

from __future__ import annotations

import importlib.util
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
_PATH = REPO_ROOT / "scripts" / "extract-release-notes.py"
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


def run_script(cwd: Path, *args: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(_PATH), *args],
        cwd=cwd,
        capture_output=True,
        text=True,
        encoding="utf-8",
        env={**os.environ, "PYTHONUTF8": "1"},
    )


class TestExtractReleaseNotesScript(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)

    def tearDown(self) -> None:
        self.tmp.cleanup()

    def test_reads_changelog_of_current_repository_from_subdirectory(self) -> None:
        repo = self.root / "other"
        (repo / "sub").mkdir(parents=True)
        (repo / "CHANGELOG.md").write_text("# Changes\n\n## v0.1.0 [2026-11-10]\n- Other notes.\n", encoding="utf-8")
        subprocess.run(["git", "init", "-q"], cwd=repo, check=True)
        result = run_script(repo / "sub", "0.1.0")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout, "- Other notes.\n")

    def test_this_repository_notes_from_subdirectory(self) -> None:
        changelog = (REPO_ROOT / "CHANGELOG.md").read_text(encoding="utf-8")
        result = run_script(REPO_ROOT / "src", "1.3.5")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout, extract_release_notes.extract_release_notes(changelog, "1.3.5") + "\n")

    def test_outside_repository_fails(self) -> None:
        result = run_script(self.root, "0.1.0")
        self.assertEqual(result.returncode, 1)
        self.assertIn("not inside a Git repository", result.stderr)

    def test_explicit_path_needs_no_repository(self) -> None:
        (self.root / "NOTES.md").write_text("## v0.2.0\n- Explicit.\n", encoding="utf-8")
        result = run_script(self.root, "v0.2.0", "NOTES.md")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout, "- Explicit.\n")


if __name__ == "__main__":
    unittest.main()
