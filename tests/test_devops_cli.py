from __future__ import annotations

import io
import sys
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Sequence
from unittest import mock

from support_python.devops.cli import DevopsCli
from support_python.devops.projects import Project, PythonProject

CHANGELOG = """# Versioned Changes

---

## v1.2.0-pre
- Added a feature.
"""

PYPROJECT = '[project]\nname = "demo"\nversion = "1.2.0-pre"\n'


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
        """Return each recorded command without its python executable."""
        return [call[1:] for call in self.calls]


def make_repo(root: Path, *, venv: bool = True, changelog: str = CHANGELOG, pyproject: str = PYPROJECT) -> None:
    (root / "pyproject.toml").write_text(pyproject, encoding="utf-8")
    (root / "CHANGELOG.md").write_text(changelog, encoding="utf-8")
    if venv:
        python = root / ".venv" / ("Scripts/python.exe" if sys.platform == "win32" else "bin/python")
        python.parent.mkdir(parents=True)
        python.write_text("", encoding="utf-8")


def run_cli(cli: DevopsCli, *argv: str) -> tuple[int, str, str]:
    out, err = io.StringIO(), io.StringIO()
    with redirect_stdout(out), redirect_stderr(err):
        code = cli.run(list(argv))
    return code, out.getvalue(), err.getvalue()


class DevopsCliTestCase(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = TemporaryDirectory()
        self.root = Path(self._tmp.name)
        self.runner = StubRunner()

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def cli(self, *, venv: bool = True, failures: Sequence[str] = (), **repo: str) -> DevopsCli:
        make_repo(self.root, venv=venv, **repo)
        self.runner.failures = list(failures)
        return DevopsCli(PythonProject(self.root, runner=self.runner))


class PythonProjectActionTests(DevopsCliTestCase):
    def test_lint_runs_ruff_check_and_format_check(self) -> None:
        code, _, _ = run_cli(self.cli(), "lint")
        self.assertEqual(code, 0)
        self.assertEqual(self.runner.tails(), [["-m", "ruff", "check", "."], ["-m", "ruff", "format", "--check", "."]])

    def test_lint_uses_the_venv_python(self) -> None:
        run_cli(self.cli(), "lint")
        expected = self.root / ".venv" / ("Scripts/python.exe" if sys.platform == "win32" else "bin/python")
        self.assertEqual(Path(self.runner.calls[0][0]), expected)

    def test_lint_failure_exits_1_and_stops(self) -> None:
        code, _, _ = run_cli(self.cli(failures=["check"]), "lint")
        self.assertEqual(code, 1)
        self.assertEqual(len(self.runner.calls), 1)

    def test_format_runs_ruff_format(self) -> None:
        code, _, _ = run_cli(self.cli(), "format")
        self.assertEqual(code, 0)
        self.assertEqual(self.runner.tails(), [["-m", "ruff", "format", "."]])

    def test_format_failure_exits_1(self) -> None:
        code, _, _ = run_cli(self.cli(failures=["format"]), "format")
        self.assertEqual(code, 1)

    def test_test_runs_pytest_quietly(self) -> None:
        code, _, _ = run_cli(self.cli(), "test")
        self.assertEqual(code, 0)
        self.assertEqual(self.runner.tails(), [["-m", "pytest", "-q"]])

    def test_test_passes_selection_through(self) -> None:
        code, _, _ = run_cli(self.cli(), "test", "tests/test_a.py", "--", "-k", "fast")
        self.assertEqual(code, 0)
        self.assertEqual(self.runner.tails(), [["-m", "pytest", "-q", "tests/test_a.py", "-k", "fast"]])

    def test_test_failure_exits_1(self) -> None:
        code, _, _ = run_cli(self.cli(failures=["pytest"]), "test")
        self.assertEqual(code, 1)

    def test_build_removes_dist_then_builds(self) -> None:
        cli = self.cli()
        stale = self.root / "dist" / "stale.whl"
        stale.parent.mkdir()
        stale.write_text("", encoding="utf-8")
        code, _, _ = run_cli(cli, "build")
        self.assertEqual(code, 0)
        self.assertFalse(stale.exists())
        self.assertEqual(self.runner.tails(), [["-m", "build", "-o", "dist"]])

    def test_build_failure_exits_1(self) -> None:
        code, _, _ = run_cli(self.cli(failures=["build"]), "build")
        self.assertEqual(code, 1)

    def test_check_runs_lint_test_and_build_in_order(self) -> None:
        code, _, _ = run_cli(self.cli(), "check")
        self.assertEqual(code, 0)
        self.assertEqual(
            self.runner.tails(),
            [
                ["-m", "ruff", "check", "."],
                ["-m", "ruff", "format", "--check", "."],
                ["-m", "pytest", "-q"],
                ["-m", "build", "-o", "dist"],
            ],
        )

    def test_check_stops_at_the_first_failure(self) -> None:
        code, _, _ = run_cli(self.cli(failures=["pytest"]), "check")
        self.assertEqual(code, 1)
        self.assertEqual(self.runner.tails()[-1], ["-m", "pytest", "-q"])
        self.assertNotIn(["-m", "build", "-o", "dist"], self.runner.tails())

    def test_clean_removes_build_outputs_without_the_venv(self) -> None:
        cli = self.cli(venv=False)
        for path in ("dist/a.whl", "build/lib/x.py", "src/demo.egg-info/PKG-INFO"):
            (self.root / path).parent.mkdir(parents=True, exist_ok=True)
            (self.root / path).write_text("", encoding="utf-8")
        (self.root / "src" / "demo").mkdir()
        code, _, _ = run_cli(cli, "clean")
        self.assertEqual(code, 0)
        for name in ("dist", "build", "src/demo.egg-info"):
            self.assertFalse((self.root / name).exists(), name)
        self.assertTrue((self.root / "src" / "demo").is_dir())
        self.assertEqual(self.runner.calls, [])

    def test_release_assets_are_wheels_and_sdists(self) -> None:
        make_repo(self.root)
        dist = self.root / "dist"
        dist.mkdir()
        for name in ("demo-1.2.0-py3-none-any.whl", "demo-1.2.0.tar.gz", "notes.txt"):
            (dist / name).write_text("", encoding="utf-8")
        assets = PythonProject(self.root, runner=self.runner).release_assets()
        self.assertEqual([asset.name for asset in assets], ["demo-1.2.0-py3-none-any.whl", "demo-1.2.0.tar.gz"])


class MissingVenvTests(DevopsCliTestCase):
    def test_venv_actions_exit_1_with_the_bootstrap_hint(self) -> None:
        for action in ("lint", "format", "test", "build", "check"):
            with self.subTest(action=action):
                self._tmp.cleanup()
                self._tmp = TemporaryDirectory()
                self.root = Path(self._tmp.name)
                code, out, err = run_cli(self.cli(venv=False), action)
                self.assertEqual(code, 1)
                self.assertIn("scripts/bootstrap-dev-environment.py", out + err)
                self.assertEqual(self.runner.calls, [])


class VersionsActionTests(DevopsCliTestCase):
    def test_versions_exit_0_when_version_file_and_changelog_agree(self) -> None:
        code, out, err = run_cli(self.cli(venv=False), "versions")
        self.assertEqual(code, 0)
        self.assertIn("1.2.0-pre", out + err)

    def test_versions_exit_1_on_drift(self) -> None:
        drifted = CHANGELOG.replace("v1.2.0-pre", "v1.1.0-pre")
        code, out, err = run_cli(self.cli(venv=False, changelog=drifted), "versions")
        self.assertEqual(code, 1)
        self.assertIn("1.1.0-pre", out + err)

    def test_versions_exit_1_without_a_changelog_heading(self) -> None:
        code, _, _ = run_cli(self.cli(venv=False, changelog="# Versioned Changes\n"), "versions")
        self.assertEqual(code, 1)

    def test_versions_exit_1_without_a_version_file(self) -> None:
        cli = self.cli(venv=False)
        (self.root / "pyproject.toml").unlink()
        code, _, _ = run_cli(cli, "versions")
        self.assertEqual(code, 1)


class ReleaseActionTests(DevopsCliTestCase):
    def release(self, *flags: str) -> tuple[int, mock.MagicMock]:
        cli = self.cli()
        with mock.patch("support_python.devops.cli.ReleasePipeline") as pipeline:
            pipeline.return_value.run.return_value = 0
            code, _, _ = run_cli(cli, "release", *flags)
        return code, pipeline

    def test_release_defaults_run_checks_and_confirm(self) -> None:
        code, pipeline = self.release()
        self.assertEqual(code, 0)
        kwargs = pipeline.call_args.kwargs
        self.assertEqual(Path(kwargs["root"]), self.root)
        self.assertFalse(kwargs["dry_run"])
        self.assertFalse(kwargs["assume_yes"])
        self.assertIsNotNone(kwargs["quality_check"])
        pipeline.return_value.run.assert_called_once_with()

    def test_release_passes_dry_run_skip_checks_and_yes(self) -> None:
        code, pipeline = self.release("--dry-run", "--skip-checks", "--yes")
        self.assertEqual(code, 0)
        kwargs = pipeline.call_args.kwargs
        self.assertTrue(kwargs["dry_run"])
        self.assertTrue(kwargs["assume_yes"])
        self.assertIsNone(kwargs["quality_check"])

    def test_release_uses_check_as_quality_check_and_build_outputs_as_assets(self) -> None:
        _, pipeline = self.release()
        kwargs = pipeline.call_args.kwargs
        self.assertTrue(kwargs["quality_check"]())
        self.assertEqual(self.runner.tails()[-1], ["-m", "build", "-o", "dist"])
        (self.root / "dist").mkdir()
        (self.root / "dist" / "demo-1.2.0.tar.gz").write_text("", encoding="utf-8")
        self.assertEqual([asset.name for asset in kwargs["assets"]()], ["demo-1.2.0.tar.gz"])

    def test_release_rebuilds_assets_after_the_freeze(self) -> None:
        # The pre-freeze `check` build carries the -pre version, so assets must come from the post-freeze build hook.
        _, pipeline = self.release("--skip-checks")
        build = pipeline.call_args.kwargs["build"]
        self.assertIsNotNone(build)
        self.assertTrue(build())
        self.assertEqual(self.runner.tails(), [["-m", "build", "-o", "dist"]])

    def test_release_failure_exits_1(self) -> None:
        cli = self.cli()
        with mock.patch("support_python.devops.cli.ReleasePipeline") as pipeline:
            pipeline.return_value.run.return_value = 1
            code, _, _ = run_cli(cli, "release", "--yes")
        self.assertEqual(code, 1)


class HarnessTests(DevopsCliTestCase):
    def test_version_banner_shows_name_and_project_version(self) -> None:
        code, out, _ = run_cli(self.cli(venv=False), "version")
        self.assertEqual(code, 0)
        self.assertEqual(out.strip(), "devops v1.2.0-pre")

    def test_devops_cli_forwards_copyright(self) -> None:
        make_repo(self.root, venv=False)
        cli = DevopsCli(
            PythonProject(self.root, runner=self.runner),
            copyright="Copyright (c) Custom Author",
        )
        code, out, _ = run_cli(cli, "version")
        self.assertEqual(code, 0)
        self.assertEqual(out.strip(), "devops v1.2.0-pre - Copyright (c) Custom Author")

    def test_help_lists_the_standard_actions(self) -> None:
        code, out, _ = run_cli(self.cli(venv=False), "help", "--verbose")
        self.assertEqual(code, 0)
        for action in ("lint", "format", "test", "build", "check", "clean", "versions", "release"):
            self.assertIn(f"devops {action}", out)

    def test_help_examples_use_the_project_test_selection_example(self) -> None:
        code, out, _ = run_cli(self.cli(venv=False), "help", "--verbose")
        self.assertEqual(code, 0)
        self.assertIn("devops test tests/test_cli.py -- -k version", out)

    def test_help_keeps_the_generic_summaries_for_python_projects(self) -> None:
        code, out, _ = run_cli(self.cli(venv=False), "help")
        self.assertEqual(code, 0)
        self.assertIn("run lint, test, and build, stopping at the first failure", out)

    def test_default_description_names_deploy_after_set_deploy(self) -> None:
        cli = self.cli(venv=False)
        cli.set_deploy([])
        self.assertIn("versions, release, and deploy operations of this project.", cli.harness.description)

    def test_default_description_names_enabled_service_groups(self) -> None:
        from support_python.devops.services import LocalDockerManager, LocalMailManager, LocalServerManager

        cli = self.cli(venv=False)
        server = LocalServerManager(port=8080, repo_root=self.root)
        cli.add_services(docker=LocalDockerManager(), server=server, mail=LocalMailManager(server_manager=server))
        self.assertIn("It also manages the docker, server, and mail services.", cli.harness.description)

    def test_default_description_names_a_group_that_replaces_a_custom_action(self) -> None:
        from support_python.devops.services import LocalDockerManager

        cli = self.cli(venv=False)
        cli.add_action("docker", "custom docker action", lambda args, logger: 0)
        cli.add_services(docker=LocalDockerManager())
        cli.add_services(docker=LocalDockerManager())
        self.assertTrue(cli.harness.description.endswith(" It also manages the docker services."))

    def test_default_description_joins_two_groups_and_keeps_deploy_in_any_order(self) -> None:
        from support_python.devops.services import LocalDockerManager, LocalVerifier

        cli = self.cli(venv=False)
        cli.add_services(docker=LocalDockerManager(), verifier=LocalVerifier(port=8080))
        cli.set_deploy([])
        self.assertIn("release, and deploy operations", cli.harness.description)
        self.assertTrue(cli.harness.description.endswith(" It also manages the docker and client services."))

    def test_custom_description_stays_after_set_deploy_and_add_services(self) -> None:
        from support_python.devops.services import LocalDockerManager

        make_repo(self.root, venv=False)
        cli = DevopsCli(PythonProject(self.root, runner=self.runner), description="Custom ops.")
        cli.set_deploy([])
        cli.add_services(docker=LocalDockerManager())
        self.assertEqual(cli.harness.description, "Custom ops.")

    def test_custom_name_and_description(self) -> None:
        make_repo(self.root, venv=False)
        cli = DevopsCli(PythonProject(self.root, runner=self.runner), name="ops", description="Custom ops.")
        code, out, _ = run_cli(cli, "help")
        self.assertEqual(code, 0)
        self.assertTrue(out.startswith("ops v1.2.0-pre"))
        self.assertIn("Custom ops.", out)

    def test_unknown_action_exits_2(self) -> None:
        code, _, _ = run_cli(self.cli(venv=False), "deploy")
        self.assertEqual(code, 2)

    def test_added_project_specific_action_dispatches(self) -> None:
        cli = self.cli(venv=False)
        received: list[str] = []

        def handler(args: object, logger: object) -> int:
            received.append(args.target)  # type: ignore[attr-defined]
            return 3

        cli.add_action(
            "deploy",
            "deploy the project",
            handler,
            configure_parser=lambda parser: parser.add_argument("target"),
        )
        code, _, _ = run_cli(cli, "deploy", "staging")
        self.assertEqual(code, 3)
        self.assertEqual(received, ["staging"])

    def test_handler_exception_exits_1(self) -> None:
        cli = self.cli()
        with mock.patch.object(PythonProject, "lint", side_effect=RuntimeError("boom")):
            code, _, _ = run_cli(cli, "lint")
        self.assertEqual(code, 1)


class ProjectBaseTests(unittest.TestCase):
    def test_check_is_lint_then_test_then_build(self) -> None:
        calls: list[str] = []

        class Demo(Project):
            def lint(self) -> bool:
                calls.append("lint")
                return True

            def format(self) -> bool:
                return True

            def test(self, selection: Sequence[str] = ()) -> bool:
                calls.append("test")
                return False

            def build(self) -> bool:
                calls.append("build")
                return True

            def clean(self) -> bool:
                return True

        with TemporaryDirectory() as tmp:
            self.assertFalse(Demo(Path(tmp)).check())
            self.assertEqual(Demo(Path(tmp)).release_assets(), [])
        self.assertEqual(calls, ["lint", "test"])


if __name__ == "__main__":
    unittest.main()
