from __future__ import annotations

import os
import subprocess
import sys
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from support_python.devops import (
    VERSION_FILES,
    changelog_top_version,
    extract_release_notes,
    find_version_file,
    freeze_changelog,
    next_dev_version,
    open_dev_changelog,
    parse_github_repo,
    read_version,
    release_version,
    write_version,
)

REPO_ROOT = Path(__file__).resolve().parent.parent

CHANGELOG = """# Versioned Changes

> Preamble.

---

## v1.1.0-pre
- Added the new thing.

---

## v1.0.0 [2026-11-01]
- First release.

## v0.9.0 [broken]
"""


def _write_bytes(path: Path, text: str) -> None:
    path.write_bytes(text.encode("utf-8"))


class VersionFileTests(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = TemporaryDirectory()
        self.root = Path(self._tmp.name)

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def test_version_files_are_checked_in_order(self) -> None:
        self.assertEqual([f.name for f in VERSION_FILES], ["pyproject.toml", "gradle.properties", "package.json"])

    def test_reads_and_writes_pyproject(self) -> None:
        _write_bytes(self.root / "pyproject.toml", '[project]\nname = "x"\nversion = "1.2.3-pre"\n')
        self.assertEqual(find_version_file(self.root), self.root / "pyproject.toml")
        self.assertEqual(read_version(self.root), "1.2.3-pre")
        write_version(self.root, "1.2.3")
        self.assertEqual((self.root / "pyproject.toml").read_bytes(), b'[project]\nname = "x"\nversion = "1.2.3"\n')

    def test_reads_and_writes_gradle_properties_preserving_crlf(self) -> None:
        _write_bytes(self.root / "gradle.properties", "group=x\r\nversion=2.0.0-pre\r\nother=1\r\n")
        self.assertEqual(read_version(self.root), "2.0.0-pre")
        write_version(self.root, "2.0.0")
        self.assertEqual((self.root / "gradle.properties").read_bytes(), b"group=x\r\nversion=2.0.0\r\nother=1\r\n")

    def test_reads_and_writes_package_json_preserving_crlf(self) -> None:
        _write_bytes(self.root / "package.json", '{\r\n  "name": "x",\r\n  "version": "0.1.0-pre"\r\n}\r\n')
        self.assertEqual(read_version(self.root), "0.1.0-pre")
        write_version(self.root, "0.1.0")
        self.assertEqual((self.root / "package.json").read_bytes(), b'{\r\n  "name": "x",\r\n  "version": "0.1.0"\r\n}\r\n')

    def test_pyproject_preserves_crlf(self) -> None:
        _write_bytes(self.root / "pyproject.toml", '[project]\r\nversion = "1.0.0"\r\n')
        write_version(self.root, "1.0.1-pre")
        self.assertEqual((self.root / "pyproject.toml").read_bytes(), b'[project]\r\nversion = "1.0.1-pre"\r\n')

    def test_skips_a_file_without_a_version(self) -> None:
        _write_bytes(self.root / "pyproject.toml", '[project]\nname = "x"\ndynamic = ["version"]\n')
        _write_bytes(self.root / "package.json", '{"version": "3.0.0"}\n')
        self.assertEqual(find_version_file(self.root), self.root / "package.json")
        self.assertEqual(read_version(self.root), "3.0.0")

    def test_missing_version_file_raises_file_not_found(self) -> None:
        self.assertIsNone(find_version_file(self.root))
        with self.assertRaises(FileNotFoundError):
            read_version(self.root)
        with self.assertRaises(FileNotFoundError):
            write_version(self.root, "1.0.0")

    def test_version_file_without_version_raises_value_error(self) -> None:
        _write_bytes(self.root / "pyproject.toml", '[project]\nname = "x"\n')
        self.assertIsNone(find_version_file(self.root))
        with self.assertRaises(ValueError):
            read_version(self.root)


class VersionArithmeticTests(unittest.TestCase):
    def test_release_version_strips_pre(self) -> None:
        self.assertEqual(release_version("1.2.3-pre"), "1.2.3")

    def test_release_version_keeps_release(self) -> None:
        self.assertEqual(release_version("1.2.3"), "1.2.3")

    def test_next_dev_version_patch(self) -> None:
        self.assertEqual(next_dev_version("1.2.3"), "1.2.4-pre")
        self.assertEqual(next_dev_version("1.2.9", "patch"), "1.2.10-pre")

    def test_next_dev_version_minor(self) -> None:
        self.assertEqual(next_dev_version("1.2.3", "minor"), "1.3.0-pre")

    def test_next_dev_version_major(self) -> None:
        self.assertEqual(next_dev_version("1.2.3", "major"), "2.0.0-pre")

    def test_next_dev_version_accepts_pre_input(self) -> None:
        self.assertEqual(next_dev_version("1.2.3-pre"), "1.2.4-pre")

    def test_next_dev_version_rejects_bad_input(self) -> None:
        with self.assertRaises(ValueError):
            next_dev_version("1.2.3", "build")
        with self.assertRaises(ValueError):
            next_dev_version("1.2")


class ChangelogTests(unittest.TestCase):
    def test_top_version_keeps_suffix(self) -> None:
        self.assertEqual(changelog_top_version(CHANGELOG), "1.1.0-pre")

    def test_top_version_drops_status(self) -> None:
        self.assertEqual(changelog_top_version("---\n\n## v1.0.0 [2026-11-01]\n- x\n"), "1.0.0")

    def test_top_version_none_without_heading(self) -> None:
        self.assertIsNone(changelog_top_version("# Title\n\nNo versions.\n"))

    def test_extract_present_section(self) -> None:
        self.assertEqual(extract_release_notes(CHANGELOG, "1.0.0"), "- First release.")
        self.assertEqual(extract_release_notes(CHANGELOG, "v1.1.0-pre"), "- Added the new thing.\n\n---")

    def test_extract_does_not_match_prefix_versions(self) -> None:
        with self.assertRaises(ValueError):
            extract_release_notes(CHANGELOG, "1.1.0")

    def test_extract_missing_section_raises(self) -> None:
        with self.assertRaisesRegex(ValueError, "v2.0.0"):
            extract_release_notes(CHANGELOG, "2.0.0")

    def test_extract_empty_section_raises(self) -> None:
        with self.assertRaisesRegex(ValueError, "empty"):
            extract_release_notes("## v1.0.0\n\n## v0.9.0\n- x\n", "1.0.0")
        with self.assertRaisesRegex(ValueError, "empty"):
            extract_release_notes(CHANGELOG, "0.9.0")

    def test_freeze_pre_heading(self) -> None:
        frozen = freeze_changelog(CHANGELOG, "1.1.0", "2026-11-09")
        self.assertIn("\n## v1.1.0 [2026-11-09]\n", frozen)
        self.assertNotIn("v1.1.0-pre", frozen)
        self.assertEqual(frozen.replace("## v1.1.0 [2026-11-09]", "## v1.1.0-pre"), CHANGELOG)

    def test_freeze_accepts_pre_version_and_released_status(self) -> None:
        frozen = freeze_changelog(CHANGELOG, "1.1.0-pre", "released: 2026-11-09")
        self.assertIn("\n## v1.1.0 [released: 2026-11-09]\n", frozen)

    def test_freeze_bare_heading(self) -> None:
        self.assertEqual(freeze_changelog("---\n\n## v1.1.0\n- x\n", "1.1.0", "2026-11-09"), "---\n\n## v1.1.0 [2026-11-09]\n- x\n")

    def test_freeze_preserves_crlf(self) -> None:
        text = "---\r\n\r\n## v1.1.0-pre\r\n- x\r\n"
        self.assertEqual(freeze_changelog(text, "1.1.0", "2026-11-09"), "---\r\n\r\n## v1.1.0 [2026-11-09]\r\n- x\r\n")

    def test_freeze_already_frozen_is_unchanged(self) -> None:
        self.assertEqual(freeze_changelog(CHANGELOG, "1.0.0", "2026-11-09"), CHANGELOG)

    def test_freeze_missing_heading_raises(self) -> None:
        with self.assertRaises(ValueError):
            freeze_changelog(CHANGELOG, "3.0.0", "2026-11-09")

    def test_open_dev_inserts_after_first_separator(self) -> None:
        opened = open_dev_changelog(CHANGELOG, "1.1.1-pre")
        self.assertTrue(opened.startswith("# Versioned Changes\n\n> Preamble.\n\n---\n\n## v1.1.1-pre\n\n## v1.1.0-pre\n"))
        self.assertEqual(changelog_top_version(opened), "1.1.1-pre")

    def test_open_dev_preserves_crlf(self) -> None:
        opened = open_dev_changelog("# T\r\n---\r\n\r\n## v1.0.0\r\n", "1.0.1-pre")
        self.assertEqual(opened, "# T\r\n---\r\n\r\n## v1.0.1-pre\r\n\r\n## v1.0.0\r\n")

    def test_open_dev_without_separator_raises(self) -> None:
        with self.assertRaises(ValueError):
            open_dev_changelog("# T\n## v1.0.0\n", "1.0.1-pre")


class GithubRepoTests(unittest.TestCase):
    def test_https_remote(self) -> None:
        self.assertEqual(parse_github_repo("https://github.com/owner/name"), "owner/name")

    def test_https_remote_with_git_suffix_and_slash(self) -> None:
        self.assertEqual(parse_github_repo("https://github.com/owner/name.git\n"), "owner/name")
        self.assertEqual(parse_github_repo("https://github.com/owner/name/"), "owner/name")

    def test_ssh_remotes(self) -> None:
        self.assertEqual(parse_github_repo("git@github.com:owner/support.python.git"), "owner/support.python")
        self.assertEqual(parse_github_repo("ssh://git@github.com/owner/name.git"), "owner/name")

    def test_non_github_remote_raises(self) -> None:
        with self.assertRaises(ValueError):
            parse_github_repo("https://gitlab.com/owner/name.git")


class RepositoryIntegrationTests(unittest.TestCase):
    def test_version_matches_changelog_top_heading(self) -> None:
        changelog = (REPO_ROOT / "CHANGELOG.md").read_text(encoding="utf-8")
        self.assertEqual(read_version(REPO_ROOT), changelog_top_version(changelog))

    def test_release_notes_match_script_output(self) -> None:
        changelog = (REPO_ROOT / "CHANGELOG.md").read_text(encoding="utf-8")
        result = subprocess.run(
            [sys.executable, str(REPO_ROOT / "scripts" / "extract-release-notes.py"), "1.3.5"],
            cwd=REPO_ROOT,
            capture_output=True,
            text=True,
            encoding="utf-8",
            check=True,
            env={**os.environ, "PYTHONUTF8": "1"},
        )
        self.assertEqual(extract_release_notes(changelog, "1.3.5"), result.stdout.rstrip("\n"))


if __name__ == "__main__":
    unittest.main()
