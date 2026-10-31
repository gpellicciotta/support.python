"""Integration tests for scripts/migrate-namespace.py and scripts/reset-history.py in a throwaway git repo."""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPTS_DIR = Path(__file__).resolve().parent.parent / "scripts"
GIT_ENV = ["-c", "user.name=Test", "-c", "user.email=test@example.com"]
GIT_IDENTITY = {
    "GIT_AUTHOR_NAME": "Test",
    "GIT_AUTHOR_EMAIL": "test@example.com",
    "GIT_COMMITTER_NAME": "Test",
    "GIT_COMMITTER_EMAIL": "test@example.com",
}

CHANGELOG = """# Versioned Changes

---

## v1.2.3-pre
- Something.

## v1.2.2 [released: 2026-01-01]
- Older.
"""


def git(repo: Path, *args: str) -> str:
    result = subprocess.run(["git", *GIT_ENV, *args], cwd=repo, check=True, text=True, capture_output=True)
    return result.stdout.strip()


class TestRepoScripts(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.repo = Path(self.tmp.name) / "acme-lib"
        (self.repo / "scripts").mkdir(parents=True)
        for name in ("_repo_common.py", "migrate-namespace.py", "reset-history.py"):
            shutil.copy(SCRIPTS_DIR / name, self.repo / "scripts" / name)
        (self.repo / ".gitignore").write_text("__pycache__/\n", encoding="utf-8")
        (self.repo / "acme").mkdir()
        (self.repo / "acme" / "core.py").write_text("NAME = 'Acme acme ACME'\n", encoding="utf-8")
        (self.repo / "pyproject.toml").write_text('[project]\nname = "acme-lib"\nversion = "1.2.3-pre"\n', encoding="utf-8")
        (self.repo / "CHANGELOG.md").write_text(CHANGELOG, encoding="utf-8")
        git(self.repo, "init", "-q", "-b", "main")
        git(self.repo, "remote", "add", "origin", "https://github.com/someone/acme-lib.git")
        git(self.repo, "add", "-A")
        git(self.repo, "commit", "-q", "-m", "Initial.")

    def tearDown(self) -> None:
        self.tmp.cleanup()

    def script(self, name: str, *args: str, stdin: str = "") -> subprocess.CompletedProcess:
        return subprocess.run(
            [sys.executable, str(self.repo / "scripts" / name), *args],
            cwd=self.repo,
            input=stdin,
            text=True,
            capture_output=True,
            env={**os.environ, **GIT_IDENTITY},
        )

    def test_rewrite_then_freeze(self) -> None:
        result = self.script("migrate-namespace.py", "--old", "acme", "--new", "widgets", "rewrite")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual((self.repo / "widgets" / "core.py").read_text(encoding="utf-8"), "NAME = 'Widgets widgets WIDGETS'\n")
        self.assertFalse((self.repo / "acme").exists())
        self.assertIn('version = "2.0.0-pre"', (self.repo / "pyproject.toml").read_text(encoding="utf-8"))
        self.assertIn("## v2.0.0-pre", (self.repo / "CHANGELOG.md").read_text(encoding="utf-8"))

        result = self.script("migrate-namespace.py", "--old", "acme", "--new", "widgets", "freeze")
        self.assertEqual(result.returncode, 0, result.stderr)
        changelog = (self.repo / "CHANGELOG.md").read_text(encoding="utf-8")
        self.assertIn("## v2.0.1-pre", changelog)
        self.assertRegex(changelog, r"## v2\.0\.0 \[\d{4}-\d{2}-\d{2}\]")
        self.assertIn('version = "2.0.0"', (self.repo / "pyproject.toml").read_text(encoding="utf-8"))

    def test_rewrite_refuses_dirty_tree(self) -> None:
        (self.repo / "dirty.txt").write_text("x", encoding="utf-8")
        git(self.repo, "add", "dirty.txt")
        result = self.script("migrate-namespace.py", "--old", "acme", "--new", "widgets", "rewrite")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("not clean", result.stderr)

    def test_reset_history_backup_and_reinit(self) -> None:
        backups = Path(self.tmp.name) / "backups"
        result = self.script("reset-history.py", "backup", str(backups))
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertTrue((backups / "acme-lib-mirror.git" / "HEAD").exists())

        result = self.script("reset-history.py", "reinit", "--backup-dir", str(backups), "--version", "1.0.0", stdin="reinit\n")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(git(self.repo, "rev-list", "--count", "HEAD"), "1")
        self.assertEqual(git(self.repo, "branch", "--show-current"), "main")
        self.assertIn('version = "1.0.0-pre"', (self.repo / "pyproject.toml").read_text(encoding="utf-8"))
        changelog = (self.repo / "CHANGELOG.md").read_text(encoding="utf-8")
        self.assertIn("## v1.0.0-pre", changelog)
        self.assertNotIn("v1.2.2", changelog)
        self.assertNotIn("scripts/reset-history.py", git(self.repo, "ls-files"))

    def test_reset_history_backup_inside_repo_is_refused(self) -> None:
        result = self.script("reset-history.py", "backup", str(self.repo / "inside"))
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("outside the repository", result.stderr)


if __name__ == "__main__":
    unittest.main()
