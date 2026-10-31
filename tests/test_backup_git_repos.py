#!/usr/bin/env python3
"""
Unit and integration tests for scripts/backup-git-repos.py.
"""

from __future__ import annotations

import contextlib
import importlib.util
import io
import json
import os
import re
import subprocess
import sys
import tempfile
import unittest
from collections.abc import Sequence
from pathlib import Path
from typing import Any
from unittest import mock

SCRIPTS_DIR = Path(__file__).resolve().parent.parent / "scripts"
sys.path.insert(0, str(SCRIPTS_DIR))

_MODULE_PATH = SCRIPTS_DIR / "backup-git-repos.py"
_spec = importlib.util.spec_from_file_location("backup_git_repos", _MODULE_PATH)
backup_git_repos = importlib.util.module_from_spec(_spec)
sys.modules[_spec.name] = backup_git_repos
_spec.loader.exec_module(backup_git_repos)

GIT_ENV = {
    "GIT_AUTHOR_NAME": "Test",
    "GIT_AUTHOR_EMAIL": "test@example.com",
    "GIT_COMMITTER_NAME": "Test",
    "GIT_COMMITTER_EMAIL": "test@example.com",
}
PASSWORD_ENV = "BACKUP_GIT_REPOS_TEST_PASSWORD"
SEVEN_ZIP = backup_git_repos.find_seven_zip(None)


def git(cwd: Path, *args: str) -> str:
    """Run git in cwd and return its stripped standard output."""
    result = subprocess.run(
        ["git", *args],
        cwd=cwd,
        env={**os.environ, **GIT_ENV},
        capture_output=True,
        text=True,
        check=True,
    )
    return result.stdout.strip()


def make_repo(path: Path, commits: int = 1, tag: str | None = None) -> Path:
    """Create a repo with the given number of commits on branch main."""
    path.mkdir(parents=True, exist_ok=True)
    git(path, "init", "-q", "-b", "main")
    for index in range(commits):
        add_commit(path, f"commit {index}")
    if tag:
        git(path, "tag", tag)
    return path


def add_commit(repo: Path, message: str) -> str:
    """Append a line to a tracked file, commit it, and return the new commit hash."""
    with (repo / "file.txt").open("a", encoding="utf-8") as handle:
        handle.write(message + "\n")
    git(repo, "add", "file.txt")
    git(repo, "commit", "-q", "-m", message)
    return git(repo, "rev-parse", "HEAD")


def refs_of(repo: Path) -> dict[str, str]:
    """Return the branch and tag refs of a repo mapped to their object names."""
    output = git(repo, "for-each-ref", "--format=%(refname) %(objectname)", "refs/heads", "refs/tags")
    return dict(line.split(" ", 1) for line in output.splitlines())


class BackupTestCase(unittest.TestCase):
    """Base class providing an isolated temporary workspace and an empty config file."""

    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.tmp = Path(self._tmp.name)
        self.config = self.tmp / "config.json"
        self.config.write_text("{}", encoding="utf-8")
        self.root = self.tmp / "root"
        self.root.mkdir()
        self.mirrors = self.tmp / "mirrors"
        self.archives = self.tmp / "archives"

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def run_main(self, *args: str, password: str | None = "secret") -> tuple[int, str, str]:
        """Run main() with the isolated config and return the exit code, stdout, and stderr."""
        return self.run_raw(*args, "--config", str(self.config), password=password)

    def run_raw(self, *args: str, password: str | None = "secret") -> tuple[int, str, str]:
        """Run main() with exactly the given arguments and return the exit code, stdout, and stderr."""
        env = {PASSWORD_ENV: password} if password is not None else {}
        out, err = io.StringIO(), io.StringIO()
        with mock.patch.dict(os.environ, env), contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            try:
                code = backup_git_repos.main(list(args))
            except KeyboardInterrupt:
                # An escaping interrupt would otherwise stop the whole pytest session.
                code = None
        if code is None:
            self.fail(f"KeyboardInterrupt escaped main(); stderr: {err.getvalue()!r}")
        return code, out.getvalue(), err.getvalue()

    def foreign_owner_env(self, *trusted: Path) -> dict[str, str]:
        """Return an environment making git treat every repo except the trusted ones as foreign-owned."""
        global_config = self.tmp / "global.gitconfig"
        lines = ["[safe]"]
        for path in trusted:
            posix = Path(os.path.abspath(path)).as_posix()
            lines += [f"\tdirectory = {posix}", f"\tdirectory = {posix}/.git"]
        global_config.write_text("\n".join(lines) + "\n", encoding="utf-8")
        return {"GIT_TEST_ASSUME_DIFFERENT_OWNER": "1", "GIT_CONFIG_GLOBAL": str(global_config)}

    def backup_args(self, *extra: str) -> list[str]:
        """Return backup arguments for both layers on the default root."""
        return [
            "backup",
            "--root",
            str(self.root),
            "--mirror-dir",
            str(self.mirrors),
            "--archive-dir",
            str(self.archives),
            "--password-env",
            PASSWORD_ENV,
            *extra,
        ]


class TestCli(BackupTestCase):
    def test_help_and_version_exit_zero(self) -> None:
        for args in (["help"], ["--help"], ["version"], ["--version"]):
            with self.subTest(args=args):
                self.assertEqual(self.run_main(*args)[0], 0)

    def test_help_verbose_adds_details(self) -> None:
        self.assertNotIn("Detailed Action Descriptions:", backup_git_repos.get_long_usage(verbose=False))
        self.assertIn("Detailed Action Descriptions:", backup_git_repos.get_long_usage(verbose=True))
        self.assertEqual(self.run_main("help", "--verbose")[0], 0)

    def test_action_specific_help_shows_only_target_action(self) -> None:
        for action in ("backup", "list", "restore", "set-password"):
            with self.subTest(action=action):
                code, out, err = self.run_main(action, "--help")
                self.assertEqual(code, 0)
                self.assertEqual(err, "")
                self.assertIn(f"Detailed Action Description: {action}", out)
                self.assertIn(f"Usage:\n  backup-git-repos {action} [options]", out)
                for other_action in ("backup", "list", "restore", "set-password"):
                    if other_action != action:
                        self.assertNotIn(f"Detailed Action Description: {other_action}", out)

    def test_help_subcommand_with_action_argument(self) -> None:
        code, out, err = self.run_main("help", "restore")
        self.assertEqual(code, 0)
        self.assertEqual(err, "")
        self.assertIn("Detailed Action Description: restore", out)
        self.assertNotIn("Detailed Action Description: backup", out)

    def test_version_banner_format(self) -> None:
        code, out, _ = self.run_main("version")
        self.assertEqual(code, 0)
        self.assertRegex(out.strip(), r"^backup-git-repos v\S+ - Copyright")

    def test_backup_without_roots_exits_two(self) -> None:
        code, _, _ = self.run_main("backup", "--mirror-dir", str(self.mirrors))
        self.assertEqual(code, 2)

    def test_backup_without_layers_exits_two(self) -> None:
        self.assertEqual(self.run_main("backup", "--root", str(self.root))[0], 2)
        code, _, _ = self.run_main("backup", "--root", str(self.root), "--mirror-dir", str(self.mirrors), "--no-mirror")
        self.assertEqual(code, 2)

    def test_missing_explicit_config_exits_two(self) -> None:
        self.config.unlink()
        self.assertEqual(self.run_main("list", "--root", str(self.root))[0], 2)

    def test_invalid_config_json_exits_two(self) -> None:
        self.config.write_text("{not json", encoding="utf-8")
        self.assertEqual(self.run_main("list", "--root", str(self.root))[0], 2)

    def test_missing_password_env_exits_two(self) -> None:
        make_repo(self.root / "alpha")
        code, _, _ = self.run_main(*self.backup_args("--no-mirror"), password=None)
        self.assertEqual(code, 2)
        self.assertFalse((self.archives / "alpha.7z").exists())


ERROR_INDENT = " " * 12
FINISHED_PATTERN = r"Finished backup-git-repos {action} in \d+\.\ds with status: {status}"


class TestHarnessCli(BackupTestCase):
    """Default help, argument errors, and lifecycle banners required by the CLI and logging guidelines."""

    def test_bare_invocation_shows_help_and_exits_zero(self) -> None:
        code, out, err = self.run_raw()
        self.assertEqual(code, 0)
        self.assertEqual(err, "")
        self.assertRegex(out.splitlines()[0], r"^backup-git-repos v\S+ - Copyright")
        self.assertIn("Usage:", out)
        self.assertIn("Exit codes:", out)
        self.assertNotIn("Detailed Action Descriptions:", out)

    def test_help_requires_explicit_backup_action(self) -> None:
        _, out, _ = self.run_raw("help")
        self.assertIn("  backup-git-repos backup [options]", out)
        self.assertNotIn("[backup]", out)
        self.assertNotIn("default action", out)

    def test_options_without_action_exit_two_with_formatted_error(self) -> None:
        code, out, err = self.run_raw("--root", str(self.root), "--mirror-dir", str(self.mirrors))
        self.assertEqual(code, 2)
        self.assertEqual(out, "")
        self.assertFalse(self.mirrors.exists())
        lines = err.splitlines()
        self.assertTrue(lines[0].startswith("**[ERROR]** "), err)
        self.assertIn("--root", lines[0])
        self.assertTrue(lines[1].startswith(f"{ERROR_INDENT}Usage: backup-git-repos {{help|version|"), err)

    def test_unknown_action_exits_two_with_formatted_usage(self) -> None:
        code, out, err = self.run_raw("bogus")
        self.assertEqual(code, 2)
        self.assertEqual(out, "")
        lines = err.splitlines()
        self.assertEqual(lines[0], "**[ERROR]** Unknown subcommand: 'bogus'")
        self.assertTrue(lines[1].startswith(f"{ERROR_INDENT}Usage: backup-git-repos {{help|version|"), err)
        for action in ("backup", "list", "restore", "set-password"):
            self.assertIn(action, lines[1])

    def test_unknown_option_exits_two_with_formatted_error(self) -> None:
        code, _, err = self.run_main("list", "--bogus")
        self.assertEqual(code, 2)
        lines = err.splitlines()
        self.assertTrue(lines[0].startswith("**[ERROR]** "), err)
        self.assertIn("--bogus", lines[0])
        self.assertTrue(lines[1].startswith(f"{ERROR_INDENT}Usage: backup-git-repos list"), err)

    def test_startup_banner_lists_configuration(self) -> None:
        make_repo(self.root / "alpha")
        code, out, err = self.run_main("list", "--root", str(self.root))
        self.assertEqual(code, 0, err)
        lines = out.splitlines()
        self.assertRegex(lines[0], r"^Starting backup-git-repos v\S+ with configuration:$")
        self.assertEqual(lines[1], "- Command: list")
        self.assertIn("- Command: list", lines)
        self.assertIn(f"- Config file: {self.config}", lines)
        self.assertIn("- Dry run: false", lines)
        self.assertIn(f"alpha  {self.root / 'alpha'}", lines)

    def test_startup_banner_names_default_config_file(self) -> None:
        home = self.tmp / "home"
        with mock.patch.object(backup_git_repos, "default_config_path", return_value=home / "config.json"):
            code, out, _ = self.run_raw("list", "--root", str(self.root), "--dry-run")
        self.assertEqual(code, 0)
        self.assertIn(f"- Config file: {home / 'config.json'} (default, absent)", out.splitlines())
        self.assertIn("- Dry run: true", out.splitlines())

    def test_backup_emits_completion_summary_with_duration(self) -> None:
        make_repo(self.root / "alpha")
        code, out, err = self.run_main(*self.backup_args("--no-archive"))
        self.assertEqual(code, 0, err)
        self.assertRegex(out.splitlines()[-1], "^" + FINISHED_PATTERN.format(action="backup", status="succeeded") + "$")

    def test_list_emits_completion_summary_with_duration(self) -> None:
        code, out, err = self.run_main("list", "--root", str(self.root))
        self.assertEqual(code, 0, err)
        self.assertRegex(out.splitlines()[-1], "^" + FINISHED_PATTERN.format(action="list", status="succeeded") + "$")

    def test_usage_error_exits_two_with_failed_summary(self) -> None:
        code, out, err = self.run_main("backup", "--mirror-dir", str(self.mirrors))
        self.assertEqual(code, 2)
        self.assertIn("**[ERROR]** No roots given", err)
        self.assertRegex(err, FINISHED_PATTERN.format(action="backup", status="failed"))
        self.assertNotIn("Execution error", err)
        self.assertNotIn("Finished", out)

    def test_log_file_receives_banner_and_summary(self) -> None:
        log_file = self.tmp / "logs" / "backup.log"
        code, _, err = self.run_main("list", "--root", str(self.root), "--log-file", str(log_file))
        self.assertEqual(code, 0, err)
        text = log_file.read_text(encoding="utf-8")
        self.assertRegex(text, r"\*\*\[INFO\]\*\*  Starting backup-git-repos v")
        self.assertRegex(text, FINISHED_PATTERN.format(action="list", status="succeeded"))

    def test_list_writes_discovered_repos_to_log_file(self) -> None:
        make_repo(self.root / "alpha")
        log_file = self.tmp / "logs" / "list.log"
        code, out, err = self.run_main("list", "--root", str(self.root), "--log-file", str(log_file))
        self.assertEqual(code, 0, err)
        self.assertIn(f"alpha  {self.root / 'alpha'}", out)
        text = log_file.read_text(encoding="utf-8")
        self.assertIn(f"alpha  {self.root / 'alpha'}", text)
        self.assertRegex(text, rf"\[\d{{4}}-\d{{2}}-\d{{2}} \d{{2}}:\d{{2}}:\d{{2}}\] alpha  {re.escape(str(self.root / 'alpha'))}")

    def test_script_entry_point_shows_help_and_version(self) -> None:
        for args, expected in (([], "Usage:"), (["version"], "backup-git-repos v")):
            with self.subTest(args=args):
                result = subprocess.run(
                    [sys.executable, str(_MODULE_PATH), *args], capture_output=True, text=True, encoding="utf-8"
                )
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertIn(expected, result.stdout)
                self.assertEqual(result.stderr, "")


class TestConfig(BackupTestCase):
    def test_config_supplies_settings(self) -> None:
        make_repo(self.root / "alpha")
        self.config.write_text(json.dumps({"roots": [str(self.root)]}), encoding="utf-8")
        code, out, _ = self.run_main("list")
        self.assertEqual(code, 0)
        self.assertIn("alpha", out)

    def test_cli_root_overrides_config_roots(self) -> None:
        other = self.tmp / "other"
        make_repo(self.root / "alpha")
        make_repo(other / "beta")
        self.config.write_text(json.dumps({"roots": [str(self.root)]}), encoding="utf-8")
        code, out, _ = self.run_main("list", "--root", str(other))
        self.assertEqual(code, 0)
        self.assertIn("beta", out)
        self.assertNotIn("alpha", out)


class TestDiscovery(BackupTestCase):
    def test_discovers_repos_up_to_depth(self) -> None:
        make_repo(self.root / "alpha")
        make_repo(self.root / "group" / "beta")
        make_repo(self.root / "a" / "b" / "too-deep")
        found = backup_git_repos.discover_repos([self.root], depth=2)
        self.assertEqual([path.name for path in found], ["alpha", "beta"])

    def test_skips_git_files_and_nested_repos(self) -> None:
        alpha = make_repo(self.root / "alpha")
        make_repo(alpha / "nested")
        worktree = self.root / "linked"
        worktree.mkdir()
        (worktree / ".git").write_text("gitdir: elsewhere\n", encoding="utf-8")
        found = backup_git_repos.discover_repos([self.root], depth=3)
        self.assertEqual(found, [alpha])

    def test_duplicate_names_exit_two(self) -> None:
        other = self.tmp / "other"
        make_repo(self.root / "same")
        make_repo(other / "same")
        code, _, err = self.run_main("list", "--root", str(self.root), "--root", str(other))
        self.assertEqual(code, 2)
        self.assertIn("same", err)

    def test_list_writes_nothing(self) -> None:
        alpha = make_repo(self.root / "alpha")
        before = sorted(p.name for p in self.tmp.iterdir())
        code, out, _ = self.run_main(
            "list", "--root", str(self.root), "--mirror-dir", str(self.mirrors), "--archive-dir", str(self.archives)
        )
        self.assertEqual(code, 0)
        self.assertIn(str(alpha), out)
        self.assertEqual(sorted(p.name for p in self.tmp.iterdir()), before)


class TestMirror(BackupTestCase):
    def test_creates_bare_mirror_with_all_refs(self) -> None:
        alpha = make_repo(self.root / "alpha", commits=2, tag="v1")
        git(alpha, "branch", "feature")
        code, _, _ = self.run_main(*self.backup_args("--no-archive"))
        self.assertEqual(code, 0)
        mirror = self.mirrors / "alpha.git"
        self.assertEqual(git(mirror, "rev-parse", "--is-bare-repository"), "true")
        self.assertEqual(git(mirror, "config", "core.logAllRefUpdates"), "always")
        self.assertEqual(refs_of(mirror), refs_of(alpha))

    def test_amended_commit_keeps_previous_tip_in_reflog(self) -> None:
        alpha = make_repo(self.root / "alpha", commits=2)
        old_tip = git(alpha, "rev-parse", "HEAD")
        self.assertEqual(self.run_main(*self.backup_args("--no-archive"))[0], 0)
        git(alpha, "commit", "-q", "--amend", "-m", "amended")
        new_tip = git(alpha, "rev-parse", "HEAD")
        self.assertEqual(self.run_main(*self.backup_args("--no-archive"))[0], 0)
        mirror = self.mirrors / "alpha.git"
        self.assertEqual(git(mirror, "rev-parse", "refs/heads/main"), new_tip)
        self.assertEqual(git(mirror, "rev-parse", "refs/heads/main@{1}"), old_tip)

    def test_repo_without_commits_is_skipped(self) -> None:
        empty = self.root / "empty"
        empty.mkdir()
        git(empty, "init", "-q")
        code, _, err = self.run_main(*self.backup_args("--no-archive"))
        self.assertEqual(code, 0)
        self.assertIn("empty", err)
        self.assertFalse((self.mirrors / "empty.git").exists())

    def test_dry_run_writes_nothing(self) -> None:
        make_repo(self.root / "alpha")
        code, _, _ = self.run_main(*self.backup_args("--dry-run"))
        self.assertEqual(code, 0)
        self.assertFalse(self.mirrors.exists())
        self.assertFalse(self.archives.exists())


@unittest.skipUnless(SEVEN_ZIP, "7-Zip executable not available")
class TestArchive(BackupTestCase):
    def archive_mtime(self, name: str) -> int:
        return (self.archives / f"{name}.7z").stat().st_mtime_ns

    def test_archive_is_encrypted(self) -> None:
        make_repo(self.root / "alpha")
        self.assertEqual(self.run_main(*self.backup_args("--no-mirror"))[0], 0)
        archive = self.archives / "alpha.7z"
        self.assertTrue(archive.exists())
        listing = subprocess.run([SEVEN_ZIP, "l", str(archive)], input="\n", capture_output=True, text=True)
        self.assertNotEqual(listing.returncode, 0)
        self.assertNotIn("alpha.bundle", listing.stdout)

    def test_skips_unchanged_and_rearchives_changes(self) -> None:
        alpha = make_repo(self.root / "alpha")
        self.assertEqual(self.run_main(*self.backup_args("--no-mirror"))[0], 0)
        first = self.archive_mtime("alpha")
        self.assertEqual(self.run_main(*self.backup_args("--no-mirror"))[0], 0)
        self.assertEqual(self.archive_mtime("alpha"), first)
        add_commit(alpha, "change")
        self.assertEqual(self.run_main(*self.backup_args("--no-mirror"))[0], 0)
        self.assertNotEqual(self.archive_mtime("alpha"), first)
        (self.archives / "alpha.7z").unlink()
        self.assertEqual(self.run_main(*self.backup_args("--no-mirror"))[0], 0)
        self.assertTrue((self.archives / "alpha.7z").exists())

    def test_wrong_password_writes_no_archive(self) -> None:
        alpha = make_repo(self.root / "alpha")
        self.assertEqual(self.run_main(*self.backup_args("--no-mirror"))[0], 0)
        first = self.archive_mtime("alpha")
        add_commit(alpha, "change")
        code, _, _ = self.run_main(*self.backup_args("--no-mirror"), password="wrong")
        self.assertEqual(code, 1)
        self.assertEqual(self.archive_mtime("alpha"), first)

    def test_unreachable_mirror_still_archives(self) -> None:
        make_repo(self.root / "alpha")
        blocker = self.tmp / "blocker.txt"
        blocker.write_text("not a directory", encoding="utf-8")
        self.mirrors = blocker / "mirrors"
        code, _, _ = self.run_main(*self.backup_args())
        self.assertEqual(code, 1)
        self.assertTrue((self.archives / "alpha.7z").exists())


@unittest.skipUnless(SEVEN_ZIP, "7-Zip executable not available")
class TestIntegration(BackupTestCase):
    def test_end_to_end_backup_and_restore(self) -> None:
        other = self.tmp / "other"
        alpha = make_repo(self.root / "alpha", commits=2, tag="v1")
        beta = make_repo(other / "group" / "beta", commits=3)
        git(beta, "branch", "feature")
        command = [
            sys.executable,
            str(_MODULE_PATH),
            "backup",
            "--config",
            str(self.config),
            "--root",
            str(self.root),
            "--root",
            str(other),
            "--mirror-dir",
            str(self.mirrors),
            "--archive-dir",
            str(self.archives),
            "--password-env",
            PASSWORD_ENV,
        ]
        result = subprocess.run(command, env={**os.environ, PASSWORD_ENV: "secret"}, capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)

        for repo in (alpha, beta):
            with self.subTest(repo=repo.name):
                mirror_clone = self.tmp / "restore-mirror" / repo.name
                git(self.tmp, "clone", "-q", "--mirror", str(self.mirrors / f"{repo.name}.git"), str(mirror_clone))
                self.assertEqual(refs_of(mirror_clone), refs_of(repo))

                extract_dir = self.tmp / "extract" / repo.name
                subprocess.run(
                    [SEVEN_ZIP, "x", str(self.archives / f"{repo.name}.7z"), f"-o{extract_dir}", "-y"],
                    input="secret\n",
                    capture_output=True,
                    text=True,
                    check=True,
                )
                bundle_clone = self.tmp / "restore-bundle" / repo.name
                git(self.tmp, "clone", "-q", "--mirror", str(extract_dir / f"{repo.name}.bundle"), str(bundle_clone))
                self.assertEqual(refs_of(bundle_clone), refs_of(repo))


class TestReviewRound1(BackupTestCase):
    """Regression tests for the findings of review round 1."""

    def test_detached_head_repo_is_mirrored(self) -> None:
        alpha = make_repo(self.root / "alpha", commits=2, tag="v1")
        git(alpha, "checkout", "-q", "--detach")
        code, _, err = self.run_main(*self.backup_args("--no-archive"))
        self.assertEqual(code, 0, err)
        mirror = self.mirrors / "alpha.git"
        self.assertEqual(refs_of(mirror), refs_of(alpha))
        self.assertEqual(git(mirror, "symbolic-ref", "HEAD"), "refs/heads/main")

    def test_non_string_config_values_exit_two(self) -> None:
        for key, value in (("seven-zip", 7), ("password-env", ["NAME"]), ("mirror-dir", 5), ("archive-dir", True)):
            with self.subTest(key=key):
                config = {"roots": [str(self.root)], "mirror-dir": str(self.mirrors), key: value}
                self.config.write_text(json.dumps(config), encoding="utf-8")
                self.assertEqual(self.run_main("backup")[0], 2)

    def test_empty_password_env_is_rejected(self) -> None:
        make_repo(self.root / "alpha")
        code, _, _ = self.run_main(*self.backup_args("--no-mirror"), password="")
        self.assertEqual(code, 1)
        self.assertFalse((self.archives / "alpha.7z").exists())
        self.assertFalse((self.archives / backup_git_repos.PASSWORD_CHECK_NAME).exists())

    def test_repo_with_only_remote_tracking_refs_is_skipped(self) -> None:
        alpha = make_repo(self.root / "alpha")
        git(alpha, "update-ref", "refs/remotes/origin/main", "HEAD")
        git(alpha, "checkout", "-q", "--detach")
        git(alpha, "branch", "-q", "-D", "main")
        code, _, err = self.run_main(*self.backup_args("--no-archive"))
        self.assertEqual(code, 0)
        self.assertIn("alpha", err)
        self.assertFalse((self.mirrors / "alpha.git").exists())

    def test_fingerprint_ignores_refs_outside_branches_and_tags(self) -> None:
        alpha = make_repo(self.root / "alpha")
        before = backup_git_repos.ref_fingerprint(alpha, backup_git_repos.ToolLogger())
        git(alpha, "update-ref", "refs/remotes/origin/main", "HEAD")
        (alpha / "file.txt").write_text("stashed change\n", encoding="utf-8")
        git(alpha, "stash", "-q")
        self.assertEqual(backup_git_repos.ref_fingerprint(alpha, backup_git_repos.ToolLogger()), before)

    def test_store_file_removes_partial_on_failure(self) -> None:
        source = self.tmp / "source.bin"
        source.write_bytes(b"data")
        target = self.tmp / "target.7z"
        with mock.patch.object(backup_git_repos.os, "replace", side_effect=OSError("disk full")):
            with self.assertRaises(OSError):
                backup_git_repos.store_file(source, target)
        self.assertEqual(sorted(p.name for p in self.tmp.iterdir() if p.name.endswith(".partial")), [])

    def test_save_state_removes_partial_on_failure(self) -> None:
        with mock.patch.object(backup_git_repos.os, "replace", side_effect=OSError("disk full")):
            with self.assertRaises(OSError):
                backup_git_repos.save_state(self.tmp, {"alpha": "0" * 64})
        self.assertEqual(sorted(p.name for p in self.tmp.iterdir() if p.name.endswith(".partial")), [])


class TestForeignOwnedMirror(BackupTestCase):
    """Regression tests for mirrors on network shares owned by another account."""

    def test_foreign_owned_mirror_is_created_and_updated(self) -> None:
        alpha = make_repo(self.root / "alpha", commits=2, tag="v1")
        with mock.patch.dict(os.environ, self.foreign_owner_env(alpha)):
            code, _, err = self.run_main(*self.backup_args("--no-archive"))
            self.assertEqual(code, 0, err)
            add_commit(alpha, "after first backup")
            code, _, err = self.run_main(*self.backup_args("--no-archive"))
            self.assertEqual(code, 0, err)
        mirror = self.mirrors / "alpha.git"
        self.assertEqual(git(mirror, "config", "core.logAllRefUpdates"), "always")
        self.assertEqual(refs_of(mirror), refs_of(alpha))

    def test_half_initialized_mirror_is_repaired(self) -> None:
        alpha = make_repo(self.root / "alpha")
        mirror = self.mirrors / "alpha.git"
        mirror.parent.mkdir()
        git(mirror.parent, "init", "-q", "--bare", "-b", "other", mirror.name)
        code, _, err = self.run_main(*self.backup_args("--no-archive"))
        self.assertEqual(code, 0, err)
        self.assertEqual(git(mirror, "config", "core.logAllRefUpdates"), "always")
        self.assertEqual(git(mirror, "symbolic-ref", "HEAD"), "refs/heads/main")
        self.assertEqual(refs_of(mirror), refs_of(alpha))

    def test_help_documents_restoring_foreign_owned_mirrors(self) -> None:
        _, out, _ = self.run_main("help", "--verbose")
        self.assertIn("safe.directory", out)


class FakeKeyring:
    """In-memory stand-in for the keyring package."""

    def __init__(self) -> None:
        self.entries: dict[tuple[str, str], str] = {}
        self.reads = 0

    def get_password(self, service: str, username: str) -> str | None:
        """Return the stored password, counting every read."""
        self.reads += 1
        return self.entries.get((service, username))

    def set_password(self, service: str, username: str, password: str) -> None:
        """Store the password under the service and user name."""
        self.entries[(service, username)] = password


class KeyringTestCase(BackupTestCase):
    """Base class replacing keyring access and interactive prompts with in-memory fakes."""

    SERVICE = "backup-git-repos-test"
    use_fake_keyring = True

    def setUp(self) -> None:
        super().setUp()
        self.keyring = FakeKeyring()
        if self.use_fake_keyring:
            self.start_patch(mock.patch.object(backup_git_repos, "keyring_backend", return_value=self.keyring))
        if SEVEN_ZIP is None:
            # Tests needing a working 7-Zip are skip-gated; the others only need the lookup to succeed.
            self.start_patch(mock.patch.object(backup_git_repos, "find_seven_zip", return_value="7z-not-installed"))

    def start_patch(self, patcher: Any) -> None:
        """Start a patcher and stop it when the test ends."""
        patcher.start()
        self.addCleanup(patcher.stop)

    def stored(self) -> str | None:
        """Return the password stored in the fake keyring without counting it as a read."""
        return self.keyring.entries.get((self.SERVICE, backup_git_repos.KEYRING_USER))

    def store(self, password: str) -> None:
        """Store a password in the fake keyring."""
        self.keyring.set_password(self.SERVICE, backup_git_repos.KEYRING_USER, password)

    def run_with_prompts(self, *args: str, prompts: Sequence[str] = ()) -> tuple[int, str, str]:
        """Run main() answering getpass prompts in order; an unexpected prompt fails the test."""
        answers = list(prompts)

        def fake_getpass(prompt: str = "") -> str:
            if not answers:
                raise AssertionError(f"Unexpected password prompt: {prompt}")
            return answers.pop(0)

        with mock.patch.object(backup_git_repos.getpass, "getpass", side_effect=fake_getpass):
            result = self.run_main(*args, password=None)
        self.assertEqual(answers, [], "Not every expected prompt was shown.")
        return result

    def keyring_backup_args(self, *extra: str) -> list[str]:
        """Return archive-only backup arguments reading the password from the keyring."""
        return [
            "backup",
            "--root",
            str(self.root),
            "--no-mirror",
            "--archive-dir",
            str(self.archives),
            "--password-keyring",
            self.SERVICE,
            *extra,
        ]

    def set_password_args(self, *extra: str) -> list[str]:
        """Return set-password arguments for the default archive directory and service."""
        return ["set-password", "--archive-dir", str(self.archives), "--password-keyring", self.SERVICE, *extra]


class TestKeyring(KeyringTestCase):
    @unittest.skipUnless(SEVEN_ZIP, "7-Zip executable not available")
    def test_backup_reads_password_from_keyring_without_prompt(self) -> None:
        make_repo(self.root / "alpha")
        self.store("secret")
        code, _, err = self.run_with_prompts(*self.keyring_backup_args())
        self.assertEqual(code, 0, err)
        self.assertTrue((self.archives / "alpha.7z").exists())
        self.assertEqual(self.keyring.reads, 1)

    def test_backup_without_stored_entry_exits_two(self) -> None:
        make_repo(self.root / "alpha")
        code, _, err = self.run_with_prompts(*self.keyring_backup_args())
        self.assertEqual(code, 2)
        self.assertIn(f"set-password --archive-dir {self.archives} --password-keyring {self.SERVICE}", err)
        self.assertFalse((self.archives / "alpha.7z").exists())

    def test_backup_with_empty_stored_password_exits_two(self) -> None:
        make_repo(self.root / "alpha")
        self.store("")
        code, _, err = self.run_with_prompts(*self.keyring_backup_args("--mirror-dir", str(self.mirrors)))
        self.assertEqual(code, 2)
        self.assertIn("set-password", err)
        self.assertFalse(self.mirrors.exists())
        self.assertFalse((self.archives / "alpha.7z").exists())

    def test_both_password_sources_exit_two(self) -> None:
        make_repo(self.root / "alpha")
        self.store("secret")
        plain_args = ["backup", "--root", str(self.root), "--no-mirror", "--archive-dir", str(self.archives)]
        cases = (
            ("cli", {}, self.keyring_backup_args("--password-env", PASSWORD_ENV)),
            ("config-and-cli", {"password-env": PASSWORD_ENV}, self.keyring_backup_args()),
            ("config", {"password-env": PASSWORD_ENV, "password-keyring": self.SERVICE}, plain_args),
        )
        for name, config, args in cases:
            with self.subTest(source=name):
                self.config.write_text(json.dumps(config), encoding="utf-8")
                code, _, err = self.run_main(*args)
                self.assertEqual(code, 2)
                self.assertIn("Set only one of --password-env and --password-keyring", err)
                self.assertFalse((self.archives / "alpha.7z").exists())

    def test_non_string_keyring_config_exits_two(self) -> None:
        config = {"roots": [str(self.root)], "mirror-dir": str(self.mirrors), "password-keyring": 3}
        self.config.write_text(json.dumps(config), encoding="utf-8")
        self.assertEqual(self.run_main("backup")[0], 2)

    @unittest.skipUnless(SEVEN_ZIP, "7-Zip executable not available")
    def test_set_password_creates_verifier_and_stores_password(self) -> None:
        code, _, err = self.run_with_prompts(*self.set_password_args(), prompts=["pw-1", "pw-1"])
        self.assertEqual(code, 0, err)
        self.assertTrue((self.archives / backup_git_repos.PASSWORD_CHECK_NAME).exists())
        self.assertEqual(self.stored(), "pw-1")

    def test_set_password_mismatch_exits_one(self) -> None:
        code, _, _ = self.run_with_prompts(*self.set_password_args(), prompts=["pw-1", "pw-2"])
        self.assertEqual(code, 1)
        self.assertIsNone(self.stored())
        self.assertFalse((self.archives / backup_git_repos.PASSWORD_CHECK_NAME).exists())

    def test_set_password_empty_exits_one(self) -> None:
        code, _, _ = self.run_with_prompts(*self.set_password_args(), prompts=["", ""])
        self.assertEqual(code, 1)
        self.assertIsNone(self.stored())

    @unittest.skipUnless(SEVEN_ZIP, "7-Zip executable not available")
    def test_set_password_rejected_by_existing_verifier_exits_one(self) -> None:
        make_repo(self.root / "alpha")
        self.assertEqual(self.run_main(*self.backup_args("--no-mirror"))[0], 0)
        code, _, _ = self.run_with_prompts(*self.set_password_args(), prompts=["wrong", "wrong"])
        self.assertEqual(code, 1)
        self.assertIsNone(self.stored())

    @unittest.skipUnless(SEVEN_ZIP, "7-Zip executable not available")
    def test_set_password_accepted_by_existing_verifier(self) -> None:
        make_repo(self.root / "alpha")
        self.assertEqual(self.run_main(*self.backup_args("--no-mirror"))[0], 0)
        code, _, err = self.run_with_prompts(*self.set_password_args(), prompts=["secret", "secret"])
        self.assertEqual(code, 0, err)
        self.assertEqual(self.stored(), "secret")

    def test_set_password_requires_archive_dir_and_service(self) -> None:
        cases = (
            ["set-password", "--password-keyring", self.SERVICE],
            ["set-password", "--archive-dir", str(self.archives)],
            [*self.set_password_args(), "--no-archive"],
        )
        for args in cases:
            with self.subTest(args=args):
                self.assertEqual(self.run_with_prompts(*args)[0], 2)
        self.assertIsNone(self.stored())

    def test_help_verbose_documents_set_password_and_scheduling(self) -> None:
        self.assertIn("set-password", backup_git_repos.get_long_usage(verbose=False))
        self.assertIn("--password-keyring", backup_git_repos.get_long_usage(verbose=False))
        details = backup_git_repos.get_long_usage(verbose=True)
        texts = ("schtasks /Create", "0 2 * * *", "--password-env, --password-keyring", "Credential Manager")
        for text in (*texts, "python {{script-path}} backup", '"password-keyring": "{{keyring-service}}"'):
            with self.subTest(text=text):
                self.assertIn(text, details)


class TestMissingKeyringPackage(KeyringTestCase):
    use_fake_keyring = False

    def test_missing_keyring_package_exits_two(self) -> None:
        make_repo(self.root / "alpha")
        with mock.patch.dict(sys.modules, {"keyring": None}):
            for args in (self.keyring_backup_args(), self.set_password_args()):
                with self.subTest(action=args[0]):
                    code, _, err = self.run_with_prompts(*args)
                    self.assertEqual(code, 2)
                    self.assertIn("pip install keyring", err)
                    self.assertFalse((self.archives / "alpha.7z").exists())

    def test_password_env_backup_never_imports_keyring(self) -> None:
        make_repo(self.root / "alpha")
        with mock.patch.dict(sys.modules, {"keyring": None}):
            code, _, err = self.run_main(*self.backup_args("--no-archive"))
        self.assertEqual(code, 0, err)

    @unittest.skipUnless(SEVEN_ZIP, "7-Zip executable not available")
    def test_password_env_archive_backup_never_imports_keyring(self) -> None:
        make_repo(self.root / "alpha")
        with mock.patch.dict(sys.modules, {"keyring": None}):
            code, _, err = self.run_main(*self.backup_args("--no-mirror"))
        self.assertEqual(code, 0, err)
        self.assertTrue((self.archives / "alpha.7z").exists())


@unittest.skipUnless(SEVEN_ZIP, "7-Zip executable not available")
class TestKeyringIntegration(KeyringTestCase):
    def test_set_password_then_unattended_backup(self) -> None:
        alpha = make_repo(self.root / "alpha", commits=2, tag="v1")
        code, _, err = self.run_with_prompts(*self.set_password_args(), prompts=["nightly", "nightly"])
        self.assertEqual(code, 0, err)
        code, _, err = self.run_with_prompts(*self.keyring_backup_args())
        self.assertEqual(code, 0, err)

        extract_dir = self.tmp / "extract"
        subprocess.run(
            [SEVEN_ZIP, "x", str(self.archives / "alpha.7z"), f"-o{extract_dir}", "-y"],
            input=f"{self.stored()}\n",
            capture_output=True,
            text=True,
            check=True,
        )
        clone = self.tmp / "clone"
        git(self.tmp, "clone", "-q", "--mirror", str(extract_dir / "alpha.bundle"), str(clone))
        self.assertEqual(refs_of(clone), refs_of(alpha))


class RestoreTestCase(KeyringTestCase):
    """Base class creating a source repo with two branches and a tag, plus restore helpers."""

    def setUp(self) -> None:
        super().setUp()
        self.target = self.tmp / "restored"
        self.alpha = make_repo(self.root / "alpha", commits=2, tag="v1")
        git(self.alpha, "checkout", "-q", "-b", "feature")
        add_commit(self.alpha, "feature work")

    def backup(self, *extra: str) -> None:
        """Back up the source repo with the given extra arguments and assert success."""
        code, _, err = self.run_main(*self.backup_args(*extra))
        self.assertEqual(code, 0, err)

    def restore(self, *args: str, prompts: Sequence[str] = ()) -> tuple[int, str, str]:
        """Run the restore action into the default target."""
        return self.run_with_prompts("restore", "--target", str(self.target), *args, prompts=prompts)

    def assert_restored(self, head: str = "refs/heads/feature") -> None:
        """Assert that the target holds every branch and tag of the source repo, checked out and remote-free."""
        self.assertEqual(refs_of(self.target), refs_of(self.alpha))
        self.assertEqual(git(self.target, "symbolic-ref", "HEAD"), head)
        self.assertEqual(git(self.target, "status", "--porcelain"), "")
        self.assertEqual(git(self.target, "remote"), "")
        source_file = (self.alpha / "file.txt").read_text(encoding="utf-8")
        self.assertEqual((self.target / "file.txt").read_text(encoding="utf-8"), source_file)


class TestActionCompletionSummaries(RestoreTestCase):
    """Restore and set-password report their runtime duration and final status on exit."""

    def test_restore_emits_completion_summary(self) -> None:
        self.backup("--no-archive")
        code, out, err = self.restore("--source", str(self.mirrors / "alpha.git"))
        self.assertEqual(code, 0, err)
        self.assertIn("- Command: restore", out.splitlines())
        self.assertRegex(out.splitlines()[-1], "^" + FINISHED_PATTERN.format(action="restore", status="succeeded") + "$")

    def test_failed_restore_emits_failed_summary(self) -> None:
        code, _, err = self.restore("--source", str(self.root / "missing.7z"))
        self.assertEqual(code, 2)
        self.assertRegex(err, FINISHED_PATTERN.format(action="restore", status="failed"))

    def test_set_password_emits_completion_summary(self) -> None:
        code, out, err = self.run_with_prompts(*self.set_password_args(), prompts=["pw-1", "pw-1"])
        self.assertEqual(code, 0, err)
        self.assertIn("- Command: set-password", out.splitlines())
        self.assertRegex(out.splitlines()[-1], "^" + FINISHED_PATTERN.format(action="set-password", status="succeeded") + "$")

    def test_rejected_set_password_emits_failed_summary(self) -> None:
        code, _, err = self.run_with_prompts(*self.set_password_args(), prompts=["pw-1", "pw-2"])
        self.assertEqual(code, 1)
        pattern = FINISHED_PATTERN.format(action="set-password", status="failed")
        self.assertRegex(err.splitlines()[-1], r"^\*\*\[ERROR\]\*\* " + pattern + "$")

    def assert_interrupted(self, action: str, code: int, out: str, err: str) -> None:
        """Assert exit code 130, an interruption error, and exactly one failed completion summary as the last line."""
        self.assertEqual(code, 130)
        self.assertIn(f"**[ERROR]** {action} interrupted", err)
        pattern = FINISHED_PATTERN.format(action=action, status="failed")
        self.assertRegex(err.splitlines()[-1], r"^\*\*\[ERROR\]\*\* " + pattern + "$")
        self.assertEqual((out + err).count("Finished backup-git-repos"), 1)

    def test_interrupted_backup_emits_failed_summary(self) -> None:
        with mock.patch.object(backup_git_repos, "mirror_repo", side_effect=KeyboardInterrupt):
            code, out, err = self.run_main(*self.backup_args("--no-archive"))
        self.assert_interrupted("backup", code, out, err)

    def test_interrupted_set_password_prompt_emits_failed_summary(self) -> None:
        log_file = self.tmp / "logs" / "set-password.log"
        with mock.patch.object(backup_git_repos.getpass, "getpass", side_effect=KeyboardInterrupt):
            code, out, err = self.run_main(*self.set_password_args("--log-file", str(log_file)), password=None)
        self.assert_interrupted("set-password", code, out, err)
        self.assertIsNone(self.stored())
        self.assertFalse((self.archives / backup_git_repos.PASSWORD_CHECK_NAME).exists())
        pattern = FINISHED_PATTERN.format(action="set-password", status="failed")
        self.assertRegex(log_file.read_text(encoding="utf-8"), r"\*\*\[ERROR\]\*\* " + pattern)

    @unittest.skipUnless(SEVEN_ZIP, "7-Zip executable not available")
    def test_interrupted_restore_password_prompt_emits_failed_summary(self) -> None:
        self.backup("--no-mirror")
        args = ("--source", str(self.archives / "alpha.7z"))
        with mock.patch.object(backup_git_repos.getpass, "getpass", side_effect=KeyboardInterrupt):
            code, out, err = self.run_main("restore", "--target", str(self.target), *args, password=None)
        self.assert_interrupted("restore", code, out, err)
        self.assertFalse(self.target.exists())

    def test_interrupted_restore_cleanup_keeps_single_summary(self) -> None:
        self.backup("--no-archive")
        with mock.patch.object(backup_git_repos, "restore_from_mirror", side_effect=KeyboardInterrupt):
            code, out, err = self.restore("--source", str(self.mirrors / "alpha.git"))
        self.assertEqual(code, 130)
        self.assertFalse(self.target.exists())
        pattern = FINISHED_PATTERN.format(action="restore", status="failed")
        self.assertRegex(err.splitlines()[-1], r"^\*\*\[ERROR\]\*\* " + pattern + "$")
        self.assertEqual((out + err).count("Finished backup-git-repos"), 1)


class TestRestoreMirror(RestoreTestCase):
    def test_restore_from_mirror_recreates_all_refs(self) -> None:
        self.backup("--no-archive")
        code, _, err = self.restore("--source", str(self.mirrors / "alpha.git"))
        self.assertEqual(code, 0, err)
        self.assertEqual(refs_of(self.target), refs_of(self.alpha))
        self.assertEqual(sorted(refs_of(self.target)), ["refs/heads/feature", "refs/heads/main", "refs/tags/v1"])

    def test_restore_from_mirror_checks_out_head_without_remotes(self) -> None:
        self.backup("--no-archive")
        code, out, err = self.restore("--source", str(self.mirrors / "alpha.git"))
        self.assertEqual(code, 0, err)
        self.assert_restored()
        self.assertIn("git remote add origin", out + err)

    def test_restore_from_foreign_owned_mirror(self) -> None:
        # HEAD names main, which does not sort first, so a failed HEAD lookup would pick feature instead.
        git(self.alpha, "checkout", "-q", "main")
        self.backup("--no-archive")
        with mock.patch.dict(os.environ, self.foreign_owner_env(self.target)):
            code, _, err = self.restore("--source", str(self.mirrors / "alpha.git"))
        self.assertEqual(code, 0, err)
        self.assert_restored(head="refs/heads/main")

    def test_interrupted_restore_cleans_up_target(self) -> None:
        self.backup("--no-archive")
        interrupt = mock.patch.object(backup_git_repos, "restore_from_mirror", side_effect=KeyboardInterrupt)
        for existing in (False, True):
            with self.subTest(existing=existing):
                if existing:
                    self.target.mkdir()
                with interrupt:
                    code, _, err = self.restore("--source", str(self.mirrors / "alpha.git"))
                self.assertEqual(code, 130)
                self.assertIn("interrupted", err)
                if existing:
                    self.assertEqual(list(self.target.iterdir()), [])
                else:
                    self.assertFalse(self.target.exists())

    def test_second_interrupt_during_cleanup_exits_130(self) -> None:
        self.backup("--no-archive")
        with (
            mock.patch.object(backup_git_repos, "restore_from_mirror", side_effect=KeyboardInterrupt),
            mock.patch.object(backup_git_repos, "clear_target", side_effect=KeyboardInterrupt),
        ):
            code, _, err = self.restore("--source", str(self.mirrors / "alpha.git"))
        self.assertEqual(code, 130)
        self.assertIn("cleanup abandoned", err)

    def test_interrupted_extraction_reports_leftover_bundle(self) -> None:
        archive = self.tmp / "alpha.7z"
        archive.write_bytes(b"placeholder")
        real_remove_tree = backup_git_repos.remove_tree

        def extract_then_interrupt(seven_zip: str, args: Sequence[str], password: str, cwd: Path, logger: Any) -> int:
            (cwd / "alpha.bundle").write_bytes(b"decrypted")
            raise KeyboardInterrupt

        def locked_work_dir(path: Path) -> None:
            if path.name.startswith("backup-git-repos-"):
                raise PermissionError("file in use")
            real_remove_tree(path)

        with (
            mock.patch.object(backup_git_repos, "run_seven_zip", side_effect=extract_then_interrupt),
            mock.patch.object(backup_git_repos, "remove_tree", side_effect=locked_work_dir),
        ):
            code, _, err = self.restore("--source", str(archive), prompts=["secret"])
        self.assertEqual(code, 130)
        self.assertIn("decrypted bundle", err)
        self.assertFalse(self.target.exists())

    def test_restore_into_file_target_exits_two(self) -> None:
        self.backup("--no-archive")
        self.target.write_text("not a directory\n", encoding="utf-8")
        code, _, err = self.restore("--source", str(self.mirrors / "alpha.git"))
        self.assertEqual(code, 2)
        self.assertIn("is not a directory", err)

    def test_restore_from_bare_repo_subdirectory_exits_two(self) -> None:
        self.backup("--no-archive")
        code, _, err = self.restore("--source", str(self.mirrors / "alpha.git" / "refs"))
        self.assertEqual(code, 2)
        self.assertIn("Unsupported restore source", err)
        self.assertFalse(self.target.exists())

    def test_restore_from_foreign_owned_mirror_with_quote_in_path(self) -> None:
        self.mirrors = self.tmp / "it's mirrors"
        self.backup("--no-archive")
        with mock.patch.dict(os.environ, self.foreign_owner_env(self.target)):
            code, _, err = self.restore("--source", str(self.mirrors / "alpha.git"))
        self.assertEqual(code, 0, err)
        self.assert_restored()

    def test_restore_into_non_empty_target_exits_two(self) -> None:
        self.backup("--no-archive")
        self.target.mkdir()
        (self.target / "keep.txt").write_text("keep\n", encoding="utf-8")
        code, _, err = self.restore("--source", str(self.mirrors / "alpha.git"))
        self.assertEqual(code, 2)
        self.assertIn("is not empty", err)
        self.assertEqual(sorted(p.name for p in self.target.iterdir()), ["keep.txt"])

    def test_restore_into_existing_empty_target(self) -> None:
        self.backup("--no-archive")
        self.target.mkdir()
        code, _, err = self.restore("--source", str(self.mirrors / "alpha.git"))
        self.assertEqual(code, 0, err)
        self.assert_restored()

    def test_restore_argument_errors_exit_two(self) -> None:
        self.backup("--no-archive")
        mirror = str(self.mirrors / "alpha.git")
        cases = (
            ("no-target", ["restore", "--source", mirror], "restore needs --target"),
            ("both", ["restore", "--target", str(self.target), "--source", mirror, "--name", "alpha"], "exactly one"),
            ("neither", ["restore", "--target", str(self.target)], "exactly one"),
        )
        for name, args, message in cases:
            with self.subTest(case=name):
                code, _, err = self.run_with_prompts(*args)
                self.assertEqual(code, 2)
                self.assertIn(message, err)
                self.assertFalse(self.target.exists())

    def test_restore_from_unsupported_source_exits_two(self) -> None:
        plain_dir = self.tmp / "plain"
        plain_dir.mkdir()
        text_file = self.tmp / "notes.txt"
        text_file.write_text("not a backup\n", encoding="utf-8")
        for source in (plain_dir, text_file, self.alpha, self.tmp / "missing.git"):
            with self.subTest(source=source.name):
                code, _, err = self.restore("--source", str(source))
                self.assertEqual(code, 2)
                self.assertIn(".7z", err)
                self.assertIn("bare", err)
                self.assertFalse(self.target.exists())

    def test_restore_dry_run_writes_nothing(self) -> None:
        self.backup("--no-archive")
        code, out, err = self.restore("--source", str(self.mirrors / "alpha.git"), "--dry-run")
        self.assertEqual(code, 0, err)
        self.assertIn("Would restore mirror", out + err)
        self.assertIn(str(self.target), out + err)
        self.assertFalse(self.target.exists())

    def test_restore_runs_without_roots(self) -> None:
        self.backup("--no-archive")
        self.config.write_text(json.dumps({"depth": 1}), encoding="utf-8")
        code, _, err = self.restore("--source", str(self.mirrors / "alpha.git"))
        self.assertEqual(code, 0, err)
        self.assertNotIn("No roots", err)

    def test_restore_by_name_without_candidates_exits_two(self) -> None:
        code, _, err = self.restore("--name", "alpha", "--mirror-dir", str(self.mirrors), "--archive-dir", str(self.archives))
        self.assertEqual(code, 2)
        self.assertIn(str(self.mirrors / "alpha.git"), err)
        self.assertIn(str(self.archives / "alpha.7z"), err)
        self.assertFalse(self.target.exists())

    def test_restore_by_name_rejects_paths(self) -> None:
        for name in ("group/alpha", "group\\alpha", "..", "alpha..git", "C:alpha"):
            with self.subTest(name=name):
                code, _, err = self.restore("--name", name, "--mirror-dir", str(self.mirrors))
                self.assertEqual(code, 2)
                self.assertIn("Invalid backup name", err)
                self.assertFalse(self.target.exists())

    def test_help_verbose_documents_restore(self) -> None:
        self.assertIn("restore", backup_git_repos.get_long_usage(verbose=False))
        details = backup_git_repos.get_long_usage(verbose=True)
        for text in ("--source PATH", "--name NAME", "--target DIR", "backup-git-repos restore --name"):
            with self.subTest(text=text):
                self.assertIn(text, details)
        self.assertNotIn("then git clone", details)


@unittest.skipUnless(SEVEN_ZIP, "7-Zip executable not available")
class TestRestoreArchive(RestoreTestCase):
    def test_restore_from_archive_with_password_env(self) -> None:
        self.backup("--no-mirror")
        code, _, err = self.run_main(
            "restore", "--target", str(self.target), "--source", str(self.archives / "alpha.7z"), "--password-env", PASSWORD_ENV
        )
        self.assertEqual(code, 0, err)
        self.assert_restored()

    def test_restore_from_archive_with_unset_password_env_exits_two(self) -> None:
        self.backup("--no-mirror")
        args = ["restore", "--target", str(self.target), "--source", str(self.archives / "alpha.7z"), "--password-env", "UNSET_VAR"]
        code, _, err = self.run_main(*args, password=None)
        self.assertEqual(code, 2)
        self.assertIn("UNSET_VAR is not set", err)
        self.assertFalse(self.target.exists())

    def test_restore_from_upper_case_archive_suffix(self) -> None:
        self.backup("--no-mirror")
        renamed = self.tmp / "copies" / "ALPHA.7Z"
        renamed.parent.mkdir()
        renamed.write_bytes((self.archives / "alpha.7z").read_bytes())
        code, _, err = self.restore("--source", str(renamed), prompts=["secret"])
        self.assertEqual(code, 0, err)
        self.assert_restored()

    def test_restore_from_archive_with_wrong_password_exits_one(self) -> None:
        self.backup("--no-mirror")
        args = ["restore", "--source", str(self.archives / "alpha.7z"), "--password-env", PASSWORD_ENV]
        code, _, err = self.run_main(*args, "--target", str(self.target), password="wrong")
        self.assertEqual(code, 1)
        self.assertIn("password", err.lower())
        self.assertFalse(self.target.exists())
        self.target.mkdir()
        code, _, _ = self.run_main(*args, "--target", str(self.target), password="wrong")
        self.assertEqual(code, 1)
        self.assertEqual(list(self.target.iterdir()), [])

    def test_restore_from_archive_reads_keyring_without_prompt(self) -> None:
        self.backup("--no-mirror")
        self.store("secret")
        code, _, err = self.restore("--source", str(self.archives / "alpha.7z"), "--password-keyring", self.SERVICE)
        self.assertEqual(code, 0, err)
        self.assert_restored()
        self.assertEqual(self.keyring.reads, 1)

    def test_restore_from_archive_prompts_once(self) -> None:
        self.backup("--no-mirror")
        code, out, err = self.restore("--source", str(self.archives / "alpha.7z"), prompts=["secret"])
        self.assertEqual(code, 0, err)
        self.assertIn(f"Extracting {self.archives / 'alpha.7z'}", out + err)
        self.assert_restored()

    def test_restore_from_archive_without_verifier(self) -> None:
        self.backup("--no-mirror")
        (self.archives / backup_git_repos.PASSWORD_CHECK_NAME).unlink()
        code, _, err = self.restore("--source", str(self.archives / "alpha.7z"), prompts=["secret"])
        self.assertEqual(code, 0, err)
        self.assertFalse((self.archives / backup_git_repos.PASSWORD_CHECK_NAME).exists())

    def test_restore_by_name_from_archive_only(self) -> None:
        self.backup("--no-mirror")
        code, _, err = self.restore("--name", "alpha", "--archive-dir", str(self.archives), prompts=["secret"])
        self.assertEqual(code, 0, err)
        self.assert_restored()

    def test_restore_by_name_prefers_mirror(self) -> None:
        self.backup()
        mirror_args = ["--name", "alpha", "--mirror-dir", str(self.mirrors), "--archive-dir", str(self.archives)]
        code, _, err = self.restore(*mirror_args)
        self.assertEqual(code, 0, err)
        self.assert_restored()
        self.target = self.tmp / "restored-archive"
        code, _, err = self.restore(*mirror_args, "--no-mirror", prompts=["secret"])
        self.assertEqual(code, 0, err)
        self.assert_restored()


@unittest.skipUnless(SEVEN_ZIP, "7-Zip executable not available")
class TestRestoreIntegration(BackupTestCase):
    def test_backup_then_restore_from_both_layers(self) -> None:
        alpha = make_repo(self.root / "alpha", commits=3, tag="v1")
        git(alpha, "branch", "feature")
        git(alpha, "tag", "-a", "v2", "-m", "annotated")
        # A tag on history no branch reaches; tag auto-following would not fetch it.
        git(alpha, "checkout", "-q", "-b", "scratch")
        add_commit(alpha, "abandoned work")
        git(alpha, "tag", "orphan")
        git(alpha, "checkout", "-q", "main")
        git(alpha, "branch", "-q", "-D", "scratch")
        base = [sys.executable, str(_MODULE_PATH)]
        config = ["--config", str(self.config)]
        # A main default branch makes git init create an unborn main, which the fetch must be allowed to update.
        default_main = {"GIT_CONFIG_COUNT": "1", "GIT_CONFIG_KEY_0": "init.defaultBranch", "GIT_CONFIG_VALUE_0": "main"}
        env = {**os.environ, PASSWORD_ENV: "secret", **default_main}
        layers = ["--mirror-dir", str(self.mirrors), "--archive-dir", str(self.archives), "--password-env", PASSWORD_ENV]
        commands = (
            [*base, "backup", *config, "--root", str(self.root), *layers],
            [*base, "restore", *config, "--source", str(self.mirrors / "alpha.git"), "--target", str(self.tmp / "from-mirror")],
            [*base, "restore", *config, "--name", "alpha", "--no-mirror", *layers, "--target", str(self.tmp / "from-archive")],
        )
        for command in commands:
            result = subprocess.run(command, env=env, capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stderr)
        for name in ("from-mirror", "from-archive"):
            with self.subTest(target=name):
                self.assertEqual(refs_of(self.tmp / name), refs_of(alpha))
                self.assertIn("refs/tags/orphan", refs_of(self.tmp / name))
                self.assertEqual(git(self.tmp / name, "symbolic-ref", "HEAD"), "refs/heads/main")


if __name__ == "__main__":
    unittest.main()
