from __future__ import annotations

import io
import json
import subprocess
import sys
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Optional, Sequence

from support_python.devops import EXIT_COMMAND_NOT_FOUND, DeployContext, DeployStep, DevopsCli, PythonProject
from support_python.devops.steps import run_step_command
from support_python.logging import CliLogger

import pytest

pytestmark = pytest.mark.slow

CHANGELOG = """# Versioned Changes

---

## v1.0.0 [released: 2026-11-10]
- Added the first feature.
"""

SUCCESS = [{"status": "completed", "conclusion": "success"}]


def git(cwd: Path, *args: str) -> str:
    result = subprocess.run(["git", *args], cwd=cwd, capture_output=True, text=True, check=True)
    return result.stdout.strip()


class FakeGh:
    """Stubs only ``gh`` commands; every other command runs for real."""

    def __init__(self) -> None:
        self.runs: object = SUCCESS
        self.code = 0
        self.queries: list[list[str]] = []
        self.steps: list[list[str]] = []

    def query(self, argv: Sequence[str], cwd: Path) -> tuple[int, str]:
        argv = [str(a) for a in argv]
        if argv[0] != "gh":
            result = subprocess.run(argv, cwd=cwd, capture_output=True, text=True, check=False)
            return result.returncode, result.stdout if result.returncode == 0 else result.stderr
        self.queries.append(argv)
        if self.code != 0:
            return self.code, "gh failed"
        return 0, self.runs if isinstance(self.runs, str) else json.dumps(self.runs)

    def runner(self, argv: Sequence[str], cwd: Path, logger: CliLogger) -> int:
        argv = [str(a) for a in argv]
        self.steps.append(argv)
        return run_step_command(argv, cwd, logger)


class DeployTestBase(unittest.TestCase):
    version = "1.0.0"

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
        (self.root / "CHANGELOG.md").write_text(CHANGELOG, encoding="utf-8")
        (self.root / ".gitignore").write_text("markers/\n", encoding="utf-8")
        git(self.root, "add", ".")
        git(self.root, "commit", "-q", "-m", "Released version 1.0.0.")
        git(self.root, "tag", "-a", f"v{self.version}", "-m", f"v{self.version}")
        git(self.root, "remote", "add", "origin", str(self.origin))
        git(self.root, "push", "-q", "origin", "main", f"v{self.version}")
        self.gh = FakeGh()
        self.events: list[str] = []
        self.contexts: list[DeployContext] = []
        self.prompts: list[str] = []
        self.answer = f"deploy v{self.version}"
        self.verify_result = True

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def input_fn(self, prompt: str) -> str:
        self.prompts.append(prompt)
        return self.answer

    def record(self, name: str, result: bool = True) -> DeployStep:
        def action(context: DeployContext) -> bool:
            self.events.append(name)
            self.contexts.append(context)
            return result

        return DeployStep(name, action=action)

    def verify(self, context: DeployContext) -> bool:
        self.events.append("verify")
        self.contexts.append(context)
        return self.verify_result

    def cli(self, steps: Optional[Sequence[DeployStep]] = None, *, verify: bool = True, **options: object) -> DevopsCli:
        cli = DevopsCli(PythonProject(self.root, runner=self.gh.runner))
        cli.set_deploy(
            steps if steps is not None else [self.record("first"), self.record("second")],
            self.verify if verify else None,
            query=self.gh.query,
            input_fn=self.input_fn,
            **options,  # type: ignore[arg-type]
        )
        return cli

    def deploy(self, *argv: str, cli: Optional[DevopsCli] = None, **options: object) -> tuple[int, str]:
        out, err = io.StringIO(), io.StringIO()
        with redirect_stdout(out), redirect_stderr(err):
            code = (cli or self.cli(**options)).run(["deploy", *argv])
        return code, out.getvalue() + err.getvalue()

    def marker_step(self, name: str) -> DeployStep:
        script = f"from pathlib import Path; Path('markers').mkdir(exist_ok=True); Path('markers/{name}').write_text('{name}')"
        return DeployStep(name, command=[sys.executable, "-c", script])


class PreconditionTests(DeployTestBase):
    def assert_refused(self, expected: str, *argv: str) -> None:
        code, output = self.deploy("--yes", *argv)
        self.assertEqual(code, 1, output)
        self.assertIn(expected, output)
        self.assertEqual(self.events, [])
        self.assertEqual(self.gh.steps, [])

    def test_rejects_uncommitted_changes(self) -> None:
        (self.root / "notes.txt").write_text("draft", encoding="utf-8")
        self.assert_refused("notes.txt")

    def test_rejects_pre_release_version(self) -> None:
        (self.root / "pyproject.toml").write_text('[project]\nname = "demo"\nversion = "1.0.1-pre"\n', encoding="utf-8")
        git(self.root, "commit", "-q", "-am", "Started version 1.0.1-pre.")
        self.assert_refused("1.0.1-pre")

    def test_rejects_missing_tag_on_origin(self) -> None:
        git(self.root, "push", "-q", "origin", ":refs/tags/v1.0.0")
        self.assert_refused("v1.0.0")

    def test_rejects_tag_on_origin_that_is_not_head(self) -> None:
        (self.root / "extra.txt").write_text("extra", encoding="utf-8")
        git(self.root, "add", "extra.txt")
        git(self.root, "commit", "-q", "-m", "Added an extra file.")
        self.assert_refused("HEAD")

    def test_accepts_lightweight_tag_at_head(self) -> None:
        git(self.root, "push", "-q", "origin", ":refs/tags/v1.0.0")
        git(self.root, "tag", "-d", "v1.0.0")
        git(self.root, "tag", "v1.0.0")
        git(self.root, "push", "-q", "origin", "v1.0.0")
        code, output = self.deploy("--yes")
        self.assertEqual(code, 0, output)

    def test_rejects_head_without_ci_runs(self) -> None:
        self.gh.runs = []
        self.assert_refused("CI")

    def test_rejects_head_with_a_failed_ci_run(self) -> None:
        self.gh.runs = [*SUCCESS, {"status": "completed", "conclusion": "failure"}]
        self.assert_refused("CI")

    def test_rejects_head_with_only_running_ci(self) -> None:
        self.gh.runs = [{"status": "in_progress", "conclusion": ""}]
        self.assert_refused("CI")

    def test_rejects_unparseable_ci_output(self) -> None:
        self.gh.runs = "not json"
        self.assert_refused("CI")

    def test_missing_gh_hints_at_skip_ci_check(self) -> None:
        self.gh.code = EXIT_COMMAND_NOT_FOUND
        self.assert_refused("--skip-ci-check")

    def test_ci_query_names_the_head_commit(self) -> None:
        code, output = self.deploy("--yes")
        self.assertEqual(code, 0, output)
        head = git(self.root, "rev-parse", "HEAD")
        self.assertEqual(self.gh.queries, [["gh", "run", "list", "--commit", head, "--json", "status,conclusion", "--limit", "20"]])

    def test_skip_ci_check_option_skips_the_ci_query(self) -> None:
        self.gh.runs = []
        code, output = self.deploy("--yes", "--skip-ci-check")
        self.assertEqual(code, 0, output)
        self.assertEqual(self.gh.queries, [])

    def test_require_ci_false_skips_the_ci_query(self) -> None:
        self.gh.runs = []
        code, output = self.deploy("--yes", require_ci=False)
        self.assertEqual(code, 0, output)
        self.assertEqual(self.gh.queries, [])


class DryRunTests(DeployTestBase):
    def test_dry_run_lists_the_plan_and_runs_nothing(self) -> None:
        steps = [self.marker_step("image"), self.record("migrate")]
        code, output = self.deploy("--dry-run", cli=self.cli(steps))
        self.assertEqual(code, 0, output)
        self.assertEqual(self.events, [])
        self.assertEqual(self.gh.steps, [])
        self.assertEqual(self.prompts, [])
        for expected in ("image", "migrate", "verify", "v1.0.0", "production"):
            self.assertIn(expected, output)
        self.assertFalse((self.root / "markers").exists())

    def test_dry_run_still_checks_preconditions(self) -> None:
        (self.root / "notes.txt").write_text("draft", encoding="utf-8")
        code, _ = self.deploy("--dry-run")
        self.assertEqual(code, 1)


class ConfirmationTests(DeployTestBase):
    def test_declined_confirmation_runs_nothing(self) -> None:
        self.answer = "deploy"
        code, _ = self.deploy()
        self.assertEqual(code, 1)
        self.assertEqual(self.events, [])
        self.assertEqual(len(self.prompts), 1)
        self.assertIn("deploy v1.0.0", self.prompts[0])

    def test_typed_confirmation_deploys(self) -> None:
        code, output = self.deploy()
        self.assertEqual(code, 0, output)
        self.assertEqual(self.events, ["first", "second", "verify"])

    def test_yes_skips_the_prompt(self) -> None:
        code, _ = self.deploy("--yes")
        self.assertEqual(code, 0)
        self.assertEqual(self.prompts, [])

    def test_confirmation_names_the_environment(self) -> None:
        out = io.StringIO()
        with redirect_stdout(out), redirect_stderr(io.StringIO()):
            code = self.cli(environment="staging").run(["deploy"])
        self.assertEqual(code, 0)
        self.assertIn("staging", out.getvalue())


class StepTests(DeployTestBase):
    def test_failing_action_step_stops_the_rest(self) -> None:
        code, output = self.deploy("--yes", cli=self.cli([self.record("first", result=False), self.record("second")]))
        self.assertEqual(code, 1)
        self.assertEqual(self.events, ["first"])
        self.assertIn("first", output)

    def test_failing_command_step_stops_the_rest(self) -> None:
        failing = DeployStep("push image", command=[sys.executable, "-c", "raise SystemExit(3)"])
        code, _ = self.deploy("--yes", cli=self.cli([failing, self.record("second")]))
        self.assertEqual(code, 1)
        self.assertEqual(self.events, [])
        self.assertEqual(len(self.gh.steps), 1)

    def test_steps_receive_the_deploy_context(self) -> None:
        code, _ = self.deploy("--yes")
        self.assertEqual(code, 0)
        context = self.contexts[0]
        self.assertEqual(context.version, "1.0.0")
        self.assertFalse(context.dry_run)
        self.assertEqual(Path(context.project.root), self.root)

    def test_deploy_step_requires_exactly_one_of_command_and_action(self) -> None:
        with self.assertRaises(ValueError):
            DeployStep("neither")
        with self.assertRaises(ValueError):
            DeployStep("both", command=["echo"], action=lambda context: True)


class VerificationTests(DeployTestBase):
    def test_failing_verification_exits_1(self) -> None:
        self.verify_result = False
        code, output = self.deploy("--yes")
        self.assertEqual(code, 1)
        self.assertEqual(self.events, ["first", "second", "verify"])
        self.assertIn("verif", output.lower())

    def test_deploy_without_verification_succeeds(self) -> None:
        code, _ = self.deploy("--yes", verify=False)
        self.assertEqual(code, 0)
        self.assertEqual(self.events, ["first", "second"])


class RegistrationTests(DeployTestBase):
    def test_deploy_is_absent_without_set_deploy(self) -> None:
        cli = DevopsCli(PythonProject(self.root, runner=self.gh.runner))
        out, err = io.StringIO(), io.StringIO()
        with redirect_stdout(out), redirect_stderr(err):
            help_code = cli.run(["help"])
            deploy_code = cli.run(["deploy", "--yes"])
        self.assertEqual(help_code, 0)
        self.assertNotIn("deploy", out.getvalue())
        self.assertEqual(deploy_code, 2)

    def test_deploy_is_listed_after_set_deploy(self) -> None:
        out = io.StringIO()
        with redirect_stdout(out):
            self.cli().run(["help"])
        self.assertIn("deploy", out.getvalue())


class DeployIntegrationTests(DeployTestBase):
    def test_deploy_runs_command_steps_then_verification_against_a_local_bare_origin(self) -> None:
        def verify(context: DeployContext) -> bool:
            markers = context.project.root / "markers"
            self.events.append("verify:" + ",".join(sorted(p.name for p in markers.iterdir())))
            return True

        steps = [self.marker_step("one"), self.marker_step("two")]
        cli = DevopsCli(PythonProject(self.root, runner=self.gh.runner))
        cli.set_deploy(steps, verify, query=self.gh.query, input_fn=self.input_fn)
        out, err = io.StringIO(), io.StringIO()
        with redirect_stdout(out), redirect_stderr(err):
            code = cli.run(["deploy", "--yes"])
        self.assertEqual(code, 0, out.getvalue() + err.getvalue())
        self.assertEqual(self.gh.steps, [list(step.command or ()) for step in steps])
        self.assertEqual(self.events, ["verify:one,two"])
        self.assertEqual(self.prompts, [])
        self.assertEqual(len(self.gh.queries), 1)


if __name__ == "__main__":
    unittest.main()
