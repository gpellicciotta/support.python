from __future__ import annotations

import io
import stat
import sys
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Sequence
from unittest import mock

from support_python.devops import GradleProject
from support_python.devops.cli import DevopsCli

CHANGELOG = """# Versioned Changes

---

## v2.0.1-pre
- Added a feature.
"""

WRAPPER = "gradlew.bat" if sys.platform == "win32" else "gradlew"


class StubRunner:
    """Records every command and returns the exit code configured for the first matching argument."""

    def __init__(self, failures: Sequence[str] = ()) -> None:
        self.calls: list[list[str]] = []
        self.failures = list(failures)

    def __call__(self, argv: Sequence[str], cwd: Path, logger: object) -> int:
        args = [str(arg) for arg in argv]
        self.calls.append(args)
        return 1 if any(failure in args for failure in self.failures) else 0

    def tails(self) -> list[list[str]]:
        """Return each recorded command without its wrapper executable and console option."""
        return [[arg for arg in call[1:] if arg != "--console=plain"] for call in self.calls]


def make_repo(root: Path, *, wrapper: bool = True) -> None:
    (root / "gradle.properties").write_text("group=demo\nversion=2.0.1-pre\n", encoding="utf-8")
    (root / "CHANGELOG.md").write_text(CHANGELOG, encoding="utf-8")
    if wrapper:
        (root / WRAPPER).write_text("", encoding="utf-8")


def run_cli(cli: DevopsCli, *argv: str) -> tuple[int, str, str]:
    out, err = io.StringIO(), io.StringIO()
    with redirect_stdout(out), redirect_stderr(err):
        code = cli.run(list(argv))
    return code, out.getvalue(), err.getvalue()


class GradleTestCase(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = TemporaryDirectory()
        self.root = Path(self._tmp.name)
        self.runner = StubRunner()

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def project(self, *, wrapper: bool = True, failures: Sequence[str] = (), **kwargs: object) -> GradleProject:
        make_repo(self.root, wrapper=wrapper)
        self.runner.failures = list(failures)
        return GradleProject(self.root, runner=self.runner, **kwargs)

    def cli(self, **kwargs: object) -> DevopsCli:
        return DevopsCli(self.project(**kwargs))


class GradleTaskMappingTests(GradleTestCase):
    def test_lint_runs_spotless_check_and_checkstyle(self) -> None:
        code, _, _ = run_cli(self.cli(), "lint")
        self.assertEqual(code, 0)
        self.assertEqual(self.runner.tails(), [["spotlessCheck", "checkstyleMain", "checkstyleTest"]])

    def test_format_runs_spotless_apply(self) -> None:
        run_cli(self.cli(), "format")
        self.assertEqual(self.runner.tails(), [["spotlessApply"]])

    def test_test_runs_the_test_task(self) -> None:
        run_cli(self.cli(), "test")
        self.assertEqual(self.runner.tails(), [["test"]])

    def test_test_adds_a_tests_filter_per_selection_item(self) -> None:
        run_cli(self.cli(), "test", "demo.CoreTest", "demo.OtherTest.method")
        self.assertEqual(self.runner.tails(), [["test", "--tests", "demo.CoreTest", "--tests", "demo.OtherTest.method"]])

    def test_test_passes_runner_options_through_unchanged(self) -> None:
        run_cli(self.cli(), "test", "demo.CoreTest", "--", "--info")
        self.assertEqual(self.runner.tails(), [["test", "--tests", "demo.CoreTest", "--info"]])

    def test_test_slow_runs_the_slow_test_task(self) -> None:
        run_cli(self.cli(), "test", "--slow")
        self.assertEqual(self.runner.tails(), [["slowTest"]])

    def test_test_slow_adds_a_tests_filter_per_selection_item(self) -> None:
        run_cli(self.cli(), "test", "--slow", "demo.SlowTest", "demo.OtherSlowTest.method")
        self.assertEqual(self.runner.tails(), [["slowTest", "--tests", "demo.SlowTest", "--tests", "demo.OtherSlowTest.method"]])

    def test_test_slow_skips_with_info_when_no_slow_tasks(self) -> None:
        code, out, err = run_cli(self.cli(slow_test_tasks=[]), "test", "--slow")
        self.assertEqual(code, 0)
        self.assertIn("skipping", (out + err).lower())
        self.assertEqual(self.runner.calls, [])

    def test_build_runs_the_build_task(self) -> None:
        run_cli(self.cli(), "build")
        self.assertEqual(self.runner.tails(), [["build"]])

    def test_check_runs_build_once(self) -> None:
        code, _, _ = run_cli(self.cli(), "check")
        self.assertEqual(code, 0)
        self.assertEqual(self.runner.tails(), [["build"]])

    def test_clean_runs_the_clean_task(self) -> None:
        run_cli(self.cli(), "clean")
        self.assertEqual(self.runner.tails(), [["clean"]])

    def test_every_invocation_uses_plain_console_output(self) -> None:
        run_cli(self.cli(), "build")
        self.assertIn("--console=plain", self.runner.calls[0])

    def test_failed_task_exits_1(self) -> None:
        for action, task in (("lint", "spotlessCheck"), ("test", "test"), ("check", "build"), ("clean", "clean")):
            with self.subTest(action=action):
                self.runner.calls.clear()
                code, _, _ = run_cli(self.cli(failures=[task]), action)
                self.assertEqual(code, 1)

    def test_commands_run_in_the_project_root(self) -> None:
        cwds: list[Path] = []
        project = self.project()
        project.runner = lambda argv, cwd, logger: cwds.append(cwd) or 0
        self.assertTrue(project.build())
        self.assertEqual(cwds, [self.root.resolve()])


class GradleOverrideTests(GradleTestCase):
    def test_keyword_arguments_replace_each_task_list(self) -> None:
        project = self.project(
            lint_tasks=["spotlessCheck"],
            format_tasks=["fmt"],
            test_tasks=["test", "integrationTest"],
            slow_test_tasks=["integrationTest"],
            build_tasks=["assemble"],
            check_tasks=["check", "assemble"],
            clean_tasks=["cleanAll"],
        )
        self.assertTrue(project.lint())
        self.assertTrue(project.format())
        self.assertTrue(project.test(["demo.CoreTest"]))
        self.assertTrue(project.test_slow(["demo.SlowTest"]))
        self.assertTrue(project.build())
        self.assertTrue(project.check())
        self.assertTrue(project.clean())
        self.assertEqual(
            self.runner.tails(),
            [
                ["spotlessCheck"],
                ["fmt"],
                ["test", "integrationTest", "--tests", "demo.CoreTest"],
                ["integrationTest", "--tests", "demo.SlowTest"],
                ["assemble"],
                ["check", "assemble"],
                ["cleanAll"],
            ],
        )

    def test_gradle_options_replace_the_console_option(self) -> None:
        project = self.project(gradle_options=["--offline"])
        project.build()
        self.assertEqual(self.runner.calls[0][1:], ["--offline", "build"])


class GradleWrapperTests(GradleTestCase):
    def test_wrapper_is_gradlew_bat_on_windows(self) -> None:
        project = self.project()
        with mock.patch.object(sys, "platform", "win32"):
            self.assertEqual(project.wrapper, self.root.resolve() / "gradlew.bat")

    def test_wrapper_is_gradlew_elsewhere(self) -> None:
        project = self.project()
        for platform in ("linux", "darwin"):
            with self.subTest(platform=platform), mock.patch.object(sys, "platform", platform):
                self.assertEqual(project.wrapper, self.root.resolve() / "gradlew")

    def test_commands_start_with_the_wrapper(self) -> None:
        self.project().build()
        self.assertEqual(self.runner.calls[0][0], str(self.root.resolve() / WRAPPER))

    def test_missing_wrapper_fails_without_running_anything(self) -> None:
        for action in ("lint", "format", "test", "build", "check", "clean"):
            with self.subTest(action=action):
                code, out, err = run_cli(self.cli(wrapper=False), action)
                self.assertEqual(code, 1)
                self.assertIn("Gradle wrapper missing", out + err)
        self.assertEqual(self.runner.calls, [])


class GradleReleaseAssetTests(GradleTestCase):
    def test_release_assets_glob_root_and_subproject_jars(self) -> None:
        project = self.project()
        for relative in ("build/libs/demo-2.0.1.jar", "build/libs/demo-2.0.1-sources.jar", "core/build/libs/core-2.0.1.jar"):
            path = self.root / relative
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text("", encoding="utf-8")
        (self.root / "build" / "libs" / "notes.txt").write_text("", encoding="utf-8")
        assets = [asset.relative_to(self.root.resolve()).as_posix() for asset in project.release_assets()]
        self.assertEqual(
            assets, ["build/libs/demo-2.0.1-sources.jar", "build/libs/demo-2.0.1.jar", "core/build/libs/core-2.0.1.jar"]
        )

    def test_release_assets_are_empty_before_a_build(self) -> None:
        self.assertEqual(self.project().release_assets(), [])


class GradleReleaseDelegationTests(GradleTestCase):
    def test_release_without_a_release_task_uses_release_pipeline(self) -> None:
        cli = self.cli()
        with mock.patch("support_python.devops.cli.ReleasePipeline") as pipeline:
            pipeline.return_value.run.return_value = 0
            code, _, _ = run_cli(cli, "release", "--yes")
        self.assertEqual(code, 0)
        pipeline.return_value.run.assert_called_once_with()
        self.assertEqual(self.runner.calls, [])

    def test_project_release_returns_none_without_a_release_task(self) -> None:
        self.assertIsNone(self.project().release(assume_yes=True))

    def test_release_task_runs_after_the_typed_confirmation(self) -> None:
        project = self.project(release_task="doFullRelease", release_args=["-PreleaseConfirmed=yes"])
        prompts: list[str] = []
        with redirect_stdout(io.StringIO()):
            released = project.release(input_fn=lambda prompt: prompts.append(prompt) or "release v2.0.1")
        self.assertTrue(released)
        self.assertEqual(prompts, ["Type 'release v2.0.1' to continue: "])
        self.assertEqual(self.runner.tails(), [["doFullRelease", "-PreleaseConfirmed=yes"]])

    def test_declined_confirmation_runs_nothing(self) -> None:
        project = self.project(release_task="doFullRelease")
        with redirect_stdout(io.StringIO()):
            released = project.release(input_fn=lambda prompt: "no")
        self.assertFalse(released)
        self.assertEqual(self.runner.calls, [])

    def test_dry_run_asks_gradle_for_its_dry_run_without_confirmation(self) -> None:
        project = self.project(release_task="doFullRelease", release_args=["-PreleaseConfirmed=yes"])
        released = project.release(dry_run=True, input_fn=lambda prompt: self.fail("prompted during a dry run"))
        self.assertTrue(released)
        self.assertEqual(self.runner.tails(), [["doFullRelease", "--dry-run"]])

    def test_cli_release_delegates_instead_of_running_release_pipeline(self) -> None:
        cli = self.cli(release_task="doFullRelease")
        with mock.patch("support_python.devops.cli.ReleasePipeline") as pipeline:
            code, _, _ = run_cli(cli, "release", "--yes")
        self.assertEqual(code, 0)
        pipeline.assert_not_called()
        self.assertEqual(self.runner.tails(), [["doFullRelease"]])

    def test_cli_release_confirms_with_the_typed_phrase(self) -> None:
        cli = self.cli(release_task="doFullRelease")
        with mock.patch("builtins.input", return_value="release v2.0.1") as prompt:
            code, _, _ = run_cli(cli, "release")
        self.assertEqual(code, 0)
        prompt.assert_called_once_with("Type 'release v2.0.1' to continue: ")
        self.assertEqual(self.runner.tails(), [["doFullRelease"]])

    def test_cli_release_dry_run_passes_dry_run_to_gradle(self) -> None:
        code, _, _ = run_cli(self.cli(release_task="doFullRelease"), "release", "--dry-run")
        self.assertEqual(code, 0)
        self.assertEqual(self.runner.tails(), [["doFullRelease", "--dry-run"]])

    def test_cli_release_task_failure_exits_1(self) -> None:
        code, _, _ = run_cli(self.cli(release_task="doFullRelease", failures=["doFullRelease"]), "release", "--yes")
        self.assertEqual(code, 1)

    def test_cli_release_declined_exits_1(self) -> None:
        cli = self.cli(release_task="doFullRelease")
        with mock.patch("builtins.input", return_value="nope"):
            code, _, _ = run_cli(cli, "release")
        self.assertEqual(code, 1)
        self.assertEqual(self.runner.calls, [])


class GradleHelpTests(GradleTestCase):
    def help_line(self, out: str, action: str) -> str:
        return next(line for line in out.splitlines() if line.strip().startswith(f"{action} ") and "devops" not in line)

    def test_help_summaries_name_the_gradle_tasks_of_each_action(self) -> None:
        code, out, _ = run_cli(self.cli(), "help")
        self.assertEqual(code, 0)
        self.assertIn("spotlessCheck checkstyleMain checkstyleTest", self.help_line(out, "lint"))
        self.assertIn("spotlessApply", self.help_line(out, "format"))
        self.assertIn("gradle build", self.help_line(out, "check"))
        self.assertNotIn("from scratch", self.help_line(out, "build"))
        self.assertNotIn("stopping at the first failure", self.help_line(out, "check"))

    def test_help_summaries_follow_task_list_overrides(self) -> None:
        code, out, _ = run_cli(self.cli(lint_tasks=["ktlintCheck"], check_tasks=["check", "assemble"]), "help")
        self.assertEqual(code, 0)
        self.assertIn("ktlintCheck", self.help_line(out, "lint"))
        self.assertIn("check assemble", self.help_line(out, "check"))

    def test_help_summary_of_an_empty_task_list_names_gradle_default_tasks(self) -> None:
        code, out, _ = run_cli(self.cli(format_tasks=[]), "help")
        self.assertEqual(code, 0)
        self.assertIn("gradle (default tasks)", self.help_line(out, "format"))

    def test_help_release_summary_names_the_release_task(self) -> None:
        code, out, _ = run_cli(self.cli(release_task="doFullRelease"), "help")
        self.assertEqual(code, 0)
        self.assertIn("doFullRelease", self.help_line(out, "release"))

    def test_help_examples_use_a_gradle_test_filter(self) -> None:
        code, out, _ = run_cli(self.cli(), "help", "--verbose")
        self.assertEqual(code, 0)
        self.assertNotIn("tests/test_cli.py", out)
        self.assertIn("devops test com.example.AppTest", out)

    def test_help_exit_codes_do_not_mention_a_virtual_environment(self) -> None:
        code, out, _ = run_cli(self.cli(), "help")
        self.assertEqual(code, 0)
        self.assertNotIn("virtual environment", out)
        self.assertIn("a prerequisite is missing", out)

    def test_skip_checks_with_a_release_task_warns_that_it_is_ignored(self) -> None:
        code, out, err = run_cli(self.cli(release_task="doFullRelease"), "release", "--dry-run", "--skip-checks")
        self.assertEqual(code, 0)
        self.assertIn("--skip-checks", out + err)
        self.assertEqual(self.runner.tails(), [["doFullRelease", "--dry-run"]])


class GradleWrapperIntegrationTests(unittest.TestCase):
    """Runs a fake wrapper script through the real step runner and checks the arguments it received."""

    def test_check_runs_the_wrapper_with_build(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            make_repo(root, wrapper=False)
            record = root / "args.txt"
            wrapper = root / WRAPPER
            if sys.platform == "win32":
                wrapper.write_text(f'@echo %*> "{record}"\r\n@exit /b 0\r\n', encoding="utf-8")
            else:
                wrapper.write_text(f'#!/bin/sh\necho "$@" > "{record}"\n', encoding="utf-8")
                wrapper.chmod(wrapper.stat().st_mode | stat.S_IXUSR)
            code, _, _ = run_cli(DevopsCli(GradleProject(root)), "check")
            self.assertEqual(code, 0)
            self.assertEqual(record.read_text(encoding="utf-8").split(), ["--console=plain", "build"])


if __name__ == "__main__":
    unittest.main()
