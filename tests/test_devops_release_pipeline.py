from __future__ import annotations

import io
import subprocess
import unittest
from contextlib import redirect_stdout
from datetime import date
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Optional, Sequence

from support_python.devops import ReleasePipeline, confirm_typed, run_step_command
from support_python.logging import CliLogger

import pytest

pytestmark = pytest.mark.slow

TODAY = date(2026, 11, 10)

CHANGELOG = """# Versioned Changes

> Preamble.

---

## v1.0.0-pre
- Added the first feature.
"""

FROZEN_CHANGELOG = """# Versioned Changes

> Preamble.

---

## v1.0.0 [2026-11-01]
- Added the first feature.
"""


def git(cwd: Path, *args: str) -> str:
    result = subprocess.run(["git", *args], cwd=cwd, capture_output=True, text=True, check=True)
    return result.stdout.strip()


class RecordingLogger(CliLogger):
    def __init__(self) -> None:
        super().__init__()
        self.lines: list[tuple[str, str]] = []

    def log(self, message: str = "", level: Optional[str] = None, *args: object, **kwargs: object) -> None:
        self.lines.append((level or "", message))

    def text(self) -> str:
        return "\n".join(message for _, message in self.lines)


class FakeGh:
    """Stubs only ``gh`` commands; every other command runs for real."""

    def __init__(self) -> None:
        self.version_code = 0
        self.auth_code = 0
        self.release_exists = False
        self.create_code = 0
        self.queries: list[list[str]] = []
        self.steps: list[list[str]] = []
        self.notes: list[str] = []

    def query(self, argv: Sequence[str], cwd: Path) -> tuple[int, str]:
        argv = [str(a) for a in argv]
        if argv[0] != "gh":
            result = subprocess.run(argv, cwd=cwd, capture_output=True, text=True, check=False)
            return result.returncode, result.stdout
        self.queries.append(argv)
        if argv[1:2] == ["--version"]:
            return self.version_code, "gh version 2.0.0"
        if argv[1:3] == ["auth", "status"]:
            return self.auth_code, ""
        if argv[1:3] == ["release", "view"]:
            return (0, "v1.0.0") if self.release_exists else (1, "release not found")
        return 1, f"unexpected gh query {argv}"

    def runner(self, argv: Sequence[str], cwd: Path, logger: CliLogger) -> int:
        argv = [str(a) for a in argv]
        if argv[0] != "gh":
            self.steps.append(argv)
            return run_step_command(argv, cwd, logger)
        self.steps.append(argv)
        if "--notes-file" in argv:
            self.notes.append(Path(argv[argv.index("--notes-file") + 1]).read_text(encoding="utf-8"))
        return self.create_code


class PipelineTestBase(unittest.TestCase):
    changelog = CHANGELOG
    version = "1.0.0-pre"

    def setUp(self) -> None:
        self._tmp = TemporaryDirectory()
        base = Path(self._tmp.name)
        self.origin = base / "origin.git"
        self.root = base / "work"
        self.root.mkdir()
        git(base, "init", "-q", "--bare", "-b", "main", str(self.origin))
        git(self.root, "init", "-q", "-b", "main")
        for key, value in (
            ("user.name", "Test"),
            ("user.email", "test@example.invalid"),
            ("commit.gpgsign", "false"),
            ("tag.gpgsign", "false"),
            ("core.autocrlf", "false"),
        ):
            git(self.root, "config", key, value)
        (self.root / "pyproject.toml").write_text(f'[project]\nname = "demo"\nversion = "{self.version}"\n', encoding="utf-8")
        (self.root / "CHANGELOG.md").write_text(self.changelog, encoding="utf-8")
        (self.root / ".gitignore").write_text("dist/\n", encoding="utf-8")
        (self.root / "dist").mkdir()
        self.asset = self.root / "dist" / "demo-1.0.0.tar.gz"
        self.asset.write_bytes(b"archive")
        git(self.root, "add", ".")
        git(self.root, "commit", "-q", "-m", "Initial commit.")
        git(self.root, "remote", "add", "origin", str(self.origin))
        git(self.root, "push", "-q", "origin", "main")
        self.gh = FakeGh()
        self.logger = RecordingLogger()
        self.prompts: list[str] = []
        self.answer = "release v1.0.0"
        self.quality_calls = 0
        self.quality_result = True

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def input_fn(self, prompt: str) -> str:
        self.prompts.append(prompt)
        return self.answer

    def quality_check(self) -> bool:
        self.quality_calls += 1
        return self.quality_result

    def pipeline(self, **overrides: object) -> ReleasePipeline:
        options: dict[str, object] = {
            "root": self.root,
            "logger": self.logger,
            "quality_check": self.quality_check,
            "assets": lambda: [self.asset],
            "runner": self.gh.runner,
            "query": self.gh.query,
            "input_fn": self.input_fn,
            "today": lambda: TODAY,
        }
        options.update(overrides)
        return ReleasePipeline(**options)  # type: ignore[arg-type]

    def run_pipeline(self, **overrides: object) -> int:
        with redirect_stdout(io.StringIO()):
            return self.pipeline(**overrides).run()

    def snapshot(self) -> tuple[str, str, str, str]:
        return (
            git(self.root, "rev-parse", "HEAD"),
            git(self.root, "tag", "--list"),
            (self.root / "pyproject.toml").read_text(encoding="utf-8"),
            (self.root / "CHANGELOG.md").read_text(encoding="utf-8"),
        )

    def origin_log(self) -> list[str]:
        return git(self.origin, "log", "--format=%s", "main").splitlines()

    def assert_untouched(self, before: tuple[str, str, str, str], origin_before: list[str]) -> None:
        self.assertEqual(self.snapshot(), before)
        self.assertEqual(self.origin_log(), origin_before)
        self.assertEqual(git(self.origin, "tag", "--list"), "")
        self.assertEqual(self.gh.steps, [])


class ChangelogOnlyTests(PipelineTestBase):
    def test_release_without_manifest(self):
        git(self.root, "rm", "pyproject.toml")
        git(self.root, "commit", "-qm", "Removed manifest.")
        before = (self.root / "CHANGELOG.md").read_bytes()
        assert self.run_pipeline(dry_run=True) == 0
        assert (self.root / "CHANGELOG.md").read_bytes() == before
        assert self.gh.steps == []
        assert self.run_pipeline(assume_yes=True) == 0
        text = (self.root / "CHANGELOG.md").read_text(encoding="utf-8")
        assert "## v1.0.1-pre" in text
        heading = "## v1.0.0 [released: 2026-11-10]" if self.version.endswith("-pre") else "## v1.0.0 [2026-11-01]"
        assert heading in text
        frozen = git(self.root, "show", "v1.0.0:CHANGELOG.md")
        assert heading in frozen
        assert "1.0.1-pre" not in frozen
        assert not (self.root / "pyproject.toml").exists()
        adds = [step for step in self.gh.steps if step[:2] == ["git", "add"]]
        assert adds == [["git", "add", "CHANGELOG.md"]] * (2 if self.version.endswith("-pre") else 1)


class FrozenChangelogOnlyTests(ChangelogOnlyTests):
    changelog = FROZEN_CHANGELOG
    version = "1.0.0"


class SyncVersionsTests(PipelineTestBase):
    def sync(self, version):
        from support_python.devops import read_version

        assert read_version(self.root) == version
        assert f"## v{version}" in (self.root / "CHANGELOG.md").read_text(encoding="utf-8")
        assert self.gh.steps[-1][:3] != ["git", "add", "CHANGELOG.md"]
        (self.root / "component.txt").write_text(version, encoding="utf-8")
        return ["component.txt"]

    def test_sync_stages_component_in_next_commit_only(self):
        assert self.run_pipeline(sync_versions=self.sync, assume_yes=True) == 0
        assert git(self.root, "show", "HEAD:component.txt") == "1.0.1-pre"
        assert "component.txt" not in git(self.root, "ls-tree", "--name-only", "v1.0.0")
        assert git(self.root, "status", "--porcelain") == ""
        assert git(self.origin, "show", "main:component.txt") == "1.0.1-pre"

    def test_sync_updates_tracked_component_without_changing_release(self):
        (self.root / "component.txt").write_text("1.0.0", encoding="utf-8")
        git(self.root, "add", "component.txt")
        git(self.root, "commit", "-qm", "Added component version.")
        assert self.run_pipeline(sync_versions=self.sync, assume_yes=True) == 0
        assert git(self.root, "show", "v1.0.0:component.txt") == "1.0.0"
        assert git(self.root, "show", "HEAD:component.txt") == "1.0.1-pre"

    def test_dry_run_plans_sync_without_calling_it(self):
        before, origin_before = self.snapshot(), self.origin_log()
        assert self.run_pipeline(sync_versions=self.sync, dry_run=True) == 0
        self.assert_untouched(before, origin_before)
        assert not (self.root / "component.txt").exists()
        assert "sync extra version targets to 1.0.1-pre" in self.logger.text()

    def test_default_has_no_sync_step(self):
        assert self.run_pipeline(dry_run=True) == 0
        assert "sync extra version targets" not in self.logger.text()

    def test_hook_failure_stops_next_commit_and_push(self):
        def fail(version):
            raise RuntimeError("component sync failed")

        assert self.run_pipeline(sync_versions=fail, assume_yes=True) == 1
        assert "component sync failed" in self.logger.text()
        assert git(self.root, "log", "-1", "--format=%s") == "Released version 1.0.0."
        assert self.gh.steps[-1][:3] == ["gh", "release", "create"]

    def test_cli_passes_project_hook_to_pipeline(self):
        from unittest.mock import patch

        from support_python.devops import DevopsCli, DocsProject

        owner = self

        class ComponentProject(DocsProject):
            def sync_versions(self, version):
                return owner.sync(version)

        project = ComponentProject(self.root, runner=self.gh.runner)
        from support_python.devops import cli

        original = cli.ReleasePipeline

        def pipeline(**kwargs):
            return original(**kwargs, query=self.gh.query)

        with patch.object(cli, "ReleasePipeline", pipeline), redirect_stdout(io.StringIO()):
            assert DevopsCli(project).run(["release", "--yes", "--skip-checks"]) == 0
        assert git(self.root, "show", "HEAD:component.txt") == "1.0.1-pre"


class PreconditionTests(PipelineTestBase):
    def assert_precondition_failure(self, expected: str, **overrides: object) -> None:
        before, origin_before = self.snapshot(), self.origin_log()
        self.assertEqual(self.run_pipeline(**overrides), 1)
        self.assert_untouched(before, origin_before)
        self.assertEqual(self.prompts, [])
        self.assertIn(expected, self.logger.text())

    def test_rejects_unrelated_uncommitted_changes(self) -> None:
        (self.root / "notes.txt").write_text("draft\n", encoding="utf-8")
        self.assert_precondition_failure("notes.txt")

    def test_allows_uncommitted_version_file_and_changelog_when_freezing(self) -> None:
        with open(self.root / "CHANGELOG.md", "a", encoding="utf-8") as f:
            f.write("- Added a late entry.\n")
        self.assertEqual(self.run_pipeline(dry_run=True), 0)

    def test_rejects_uncommitted_changelog_when_already_frozen(self) -> None:
        (self.root / "pyproject.toml").write_text('[project]\nname = "demo"\nversion = "1.0.0"\n', encoding="utf-8")
        (self.root / "CHANGELOG.md").write_text(FROZEN_CHANGELOG, encoding="utf-8")
        self.assert_precondition_failure("CHANGELOG.md")

    def test_rejects_other_branch(self) -> None:
        git(self.root, "checkout", "-q", "-b", "feature")
        self.assert_precondition_failure("feature")

    def test_rejects_missing_gh(self) -> None:
        self.gh.version_code = 127
        self.assert_precondition_failure("gh")

    def test_rejects_unauthenticated_gh(self) -> None:
        self.gh.auth_code = 1
        self.assert_precondition_failure("gh auth login")

    def test_rejects_failed_fetch(self) -> None:
        git(self.root, "remote", "set-url", "origin", str(self.root.parent / "missing.git"))
        before = self.snapshot()
        self.assertEqual(self.run_pipeline(), 1)
        self.assertEqual(self.snapshot(), before)
        self.assertEqual(self.gh.steps, [])
        self.assertIn("fetch", self.logger.text())

    def test_rejects_existing_remote_tag(self) -> None:
        git(self.root, "tag", "v1.0.0")
        git(self.root, "push", "-q", "origin", "v1.0.0")
        git(self.root, "tag", "-d", "v1.0.0")
        head, _, *files = self.snapshot()
        self.assertEqual(self.run_pipeline(), 1)
        self.assertEqual([self.snapshot()[0], *self.snapshot()[2:]], [head, *files])
        self.assertEqual(self.gh.steps, [])
        self.assertIn("Tag 'v1.0.0' already exists on origin.", self.logger.text())

    def test_rejects_existing_local_tag(self) -> None:
        git(self.root, "tag", "v1.0.0")
        before = self.snapshot()
        self.assertEqual(self.run_pipeline(), 1)
        self.assertEqual(self.snapshot(), before)
        self.assertEqual(self.gh.steps, [])
        self.assertIn("already exists locally", self.logger.text())

    def test_rejects_existing_github_release(self) -> None:
        self.gh.release_exists = True
        self.assert_precondition_failure("already exists")

    def test_rejects_empty_release_notes(self) -> None:
        (self.root / "CHANGELOG.md").write_text(CHANGELOG.replace("- Added the first feature.\n", ""), encoding="utf-8")
        git(self.root, "commit", "-q", "-am", "Emptied notes.")
        git(self.root, "push", "-q", "origin", "main")
        self.assert_precondition_failure("empty")

    def test_rejects_failed_quality_check(self) -> None:
        self.quality_result = False
        self.assert_precondition_failure("Quality check failed")
        self.assertEqual(self.quality_calls, 1)

    def test_rejects_missing_asset(self) -> None:
        self.asset.unlink()
        self.assert_precondition_failure(self.asset.name)


class DryRunTests(PipelineTestBase):
    def test_skip_github_dry_run_never_queries_gh(self) -> None:
        self.gh.version_code = 127
        before, origin_before = self.snapshot(), self.origin_log()
        self.assertEqual(self.run_pipeline(dry_run=True, skip_github_release=True), 0)
        self.assert_untouched(before, origin_before)
        self.assertEqual(self.gh.queries, [])
        self.assertNotIn("gh release", self.logger.text())

    def test_skip_github_still_pushes_tag_and_reopens_development(self) -> None:
        self.gh.auth_code = 1
        self.gh.release_exists = True
        self.assertEqual(self.run_pipeline(skip_github_release=True), 0)
        self.assertEqual(self.gh.queries, [])
        self.assertFalse(any(argv[0] == "gh" for argv in self.gh.steps))
        self.assertEqual(git(self.origin, "tag", "--list"), "v1.0.0")
        self.assertIn("1.0.1-pre", (self.root / "pyproject.toml").read_text(encoding="utf-8"))
        self.assertNotIn("/releases/tag/", self.logger.text())

    def test_dry_run_changes_nothing_and_logs_every_planned_command(self) -> None:
        before, origin_before = self.snapshot(), self.origin_log()
        self.assertEqual(self.run_pipeline(dry_run=True), 0)
        self.assert_untouched(before, origin_before)
        self.assertEqual(self.prompts, [])
        self.assertEqual(self.quality_calls, 0)
        log = self.logger.text()
        for expected in (
            "CHANGELOG.md: ## v1.0.0 [released: 2026-11-10]",
            'pyproject.toml: version = "1.0.0"',
            'git commit -m "Released version 1.0.0."',
            "git tag v1.0.0",
            "git push origin main",
            "git push origin v1.0.0",
            "gh release create v1.0.0 --title v1.0.0 --notes-file",
            self.asset.name,
            "CHANGELOG.md: ## v1.0.1-pre",
            'pyproject.toml: version = "1.0.1-pre"',
            'git commit -m "Started version 1.0.1-pre after the 1.0.0 release."',
        ):
            self.assertIn(expected, log)


class ConfirmationTests(PipelineTestBase):
    def test_declined_confirmation_changes_nothing(self) -> None:
        self.answer = "release v1.0.1"
        before, origin_before = self.snapshot(), self.origin_log()
        self.assertEqual(self.run_pipeline(), 1)
        self.assert_untouched(before, origin_before)
        self.assertEqual(len(self.prompts), 1)
        self.assertIn("release v1.0.0", self.prompts[0])

    def test_typed_confirmation_releases(self) -> None:
        self.assertEqual(self.run_pipeline(), 0)
        self.assertEqual(len(self.prompts), 1)
        self.assertEqual(git(self.origin, "tag", "--list"), "v1.0.0")

    def test_confirm_typed_matches_the_exact_phrase(self) -> None:
        out = io.StringIO()
        with redirect_stdout(out):
            self.assertTrue(
                confirm_typed(["Release v1.0.0", "Push to origin"], "release v1.0.0", input_fn=lambda _: " release v1.0.0 ")
            )
            self.assertFalse(confirm_typed(["Release v1.0.0"], "release v1.0.0", input_fn=lambda _: "yes"))
        self.assertIn("Release v1.0.0", out.getvalue())
        self.assertIn("Push to origin", out.getvalue())

    def test_confirm_typed_treats_end_of_input_as_declined(self) -> None:
        def eof(_: str) -> str:
            raise EOFError

        with redirect_stdout(io.StringIO()):
            self.assertFalse(confirm_typed([], "release v1.0.0", input_fn=eof))


class FrozenVersionTests(PipelineTestBase):
    changelog = FROZEN_CHANGELOG
    version = "1.0.0"

    def test_frozen_version_skips_the_freeze_commit(self) -> None:
        head = git(self.root, "rev-parse", "HEAD")
        self.assertEqual(self.run_pipeline(assume_yes=True), 0)
        self.assertEqual(git(self.origin, "rev-parse", "v1.0.0^{commit}"), head)
        self.assertEqual(self.origin_log(), ["Started version 1.0.1-pre after the 1.0.0 release.", "Initial commit."])
        self.assertIn("## v1.0.0 [2026-11-01]", (self.root / "CHANGELOG.md").read_text(encoding="utf-8"))


class FullReleaseIntegrationTests(PipelineTestBase):
    def test_full_release_against_a_local_bare_origin(self) -> None:
        self.assertEqual(self.run_pipeline(assume_yes=True), 0)
        self.assertEqual(self.prompts, [])
        self.assertEqual(self.quality_calls, 1)
        self.assertEqual(
            self.origin_log(),
            ["Started version 1.0.1-pre after the 1.0.0 release.", "Released version 1.0.0.", "Initial commit."],
        )
        tagged = git(self.origin, "rev-parse", "v1.0.0^{commit}")
        self.assertEqual(git(self.origin, "log", "-1", "--format=%s", tagged), "Released version 1.0.0.")
        self.assertIn('version = "1.0.0"', git(self.origin, "show", "v1.0.0:pyproject.toml"))
        self.assertIn("## v1.0.0 [released: 2026-11-10]", git(self.origin, "show", "v1.0.0:CHANGELOG.md"))
        creates = [step for step in self.gh.steps if step[:3] == ["gh", "release", "create"]]
        self.assertEqual(len(creates), 1)
        self.assertEqual(creates[0][3:6], ["v1.0.0", "--title", "v1.0.0"])
        self.assertEqual(creates[0][-1], str(self.asset))
        self.assertEqual(self.gh.notes, ["- Added the first feature."])
        self.assertFalse(Path(creates[0][creates[0].index("--notes-file") + 1]).exists())
        self.assertEqual(git(self.root, "status", "--porcelain"), "")
        self.assertIn('version = "1.0.1-pre"', (self.root / "pyproject.toml").read_text(encoding="utf-8"))
        changelog = (self.root / "CHANGELOG.md").read_text(encoding="utf-8")
        self.assertLess(changelog.index("## v1.0.1-pre"), changelog.index("## v1.0.0 [released: 2026-11-10]"))
        self.assertEqual(git(self.root, "rev-parse", "HEAD"), git(self.origin, "rev-parse", "main"))

    def test_failed_step_exits_1(self) -> None:
        self.gh.create_code = 1
        self.assertEqual(self.run_pipeline(assume_yes=True), 1)
        self.assertIn("gh release create", self.logger.text())
        self.assertEqual(self.origin_log(), ["Released version 1.0.0.", "Initial commit."])


class BuildHookTests(PipelineTestBase):
    def setUp(self) -> None:
        super().setUp()
        self.events: list[str] = []
        self.build_result = True
        self.built = self.root / "dist" / "demo-1.0.0-py3-none-any.whl"

    def build(self) -> bool:
        version = (self.root / "pyproject.toml").read_text(encoding="utf-8")
        self.events.append(f"build: {git(self.root, 'log', '-1', '--format=%s')} | tags: {git(self.root, 'tag', '--list')!r}")
        self.events.append(f"build version: {version.splitlines()[-1]}")
        self.asset.unlink()
        self.built.write_bytes(b"wheel")
        return self.build_result

    def assets(self) -> list[Path]:
        self.events.append("assets")
        return sorted((self.root / "dist").glob("*"))

    def test_assets_are_built_after_the_freeze_commit_and_before_the_tag(self) -> None:
        self.assertEqual(self.run_pipeline(assume_yes=True, build=self.build, assets=self.assets), 0)
        self.assertEqual(
            self.events,
            ["build: Released version 1.0.0. | tags: ''", 'build version: version = "1.0.0"', "assets"],
        )
        creates = [step for step in self.gh.steps if step[:3] == ["gh", "release", "create"]]
        self.assertEqual(len(creates), 1)
        self.assertEqual(creates[0][-1], str(self.built))
        self.assertNotIn(str(self.asset), creates[0])
        self.assertEqual(git(self.origin, "tag", "--list"), "v1.0.0")

    def test_failed_build_stops_before_tagging_and_pushing(self) -> None:
        self.build_result = False
        self.assertEqual(self.run_pipeline(assume_yes=True, build=self.build, assets=self.assets), 1)
        self.assertIn("build release assets", self.logger.text())
        self.assertEqual(git(self.root, "tag", "--list"), "")
        self.assertEqual(git(self.root, "log", "-1", "--format=%s"), "Released version 1.0.0.")
        self.assertEqual(self.origin_log(), ["Initial commit."])
        self.assertNotIn("assets", self.events)
        self.assertEqual([step for step in self.gh.steps if step[0] == "gh"], [])

    def test_dry_run_plans_the_build_without_running_it_or_resolving_assets(self) -> None:
        before, origin_before = self.snapshot(), self.origin_log()
        self.assertEqual(self.run_pipeline(dry_run=True, build=self.build, assets=self.assets), 0)
        self.assert_untouched(before, origin_before)
        self.assertEqual(self.events, [])
        log = self.logger.text()
        self.assertLess(log.index('git commit -m "Released version 1.0.0."'), log.index("build release assets"))
        self.assertLess(log.index("build release assets"), log.index("git tag v1.0.0"))
        self.assertIn("gh release create v1.0.0 --title v1.0.0 --notes-file <notes-file> <built-assets>", log)

    def test_missing_built_asset_fails_before_tagging(self) -> None:
        missing = self.root / "dist" / "absent.whl"
        self.assertEqual(self.run_pipeline(assume_yes=True, build=self.build, assets=lambda: [missing]), 1)
        self.assertIn(missing.name, self.logger.text())
        self.assertEqual(git(self.root, "tag", "--list"), "")
        self.assertEqual(self.origin_log(), ["Initial commit."])
        self.assertEqual([step for step in self.gh.steps if step[0] == "gh"], [])


if __name__ == "__main__":
    unittest.main()
