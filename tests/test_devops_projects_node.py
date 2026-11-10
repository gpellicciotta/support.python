from __future__ import annotations

import io
import json
import shutil
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Optional, Sequence
from unittest import mock

from support_python.devops import NodeProject
from support_python.devops.cli import DevopsCli

import pytest

CHANGELOG = """# Versioned Changes

---

## v2.0.1-pre
- Added a feature.
"""

NPM = "C:/tools/npm.cmd"
ALL_SCRIPTS = {"lint": "eslint .", "format": "prettier -w .", "test": "vitest run", "build": "vite build"}


class StubRunner:
    """Records every command and its directory, returning 1 for commands containing a configured argument."""

    def __init__(self, failures: Sequence[str] = ()) -> None:
        self.calls: list[list[str]] = []
        self.cwds: list[Path] = []
        self.failures = list(failures)

    def __call__(self, argv: Sequence[str], cwd: Path, logger: object) -> int:
        args = [str(arg) for arg in argv]
        self.calls.append(args)
        self.cwds.append(cwd)
        return 1 if any(failure in args for failure in self.failures) else 0

    def tails(self) -> list[list[str]]:
        """Return each recorded command without its npm executable."""
        return [call[1:] for call in self.calls]


def make_repo(root: Path, scripts: Optional[dict[str, str]] = None) -> None:
    manifest = {"name": "demo", "version": "2.0.1-pre", "scripts": ALL_SCRIPTS if scripts is None else scripts}
    (root / "package.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    (root / "CHANGELOG.md").write_text(CHANGELOG, encoding="utf-8")


def run_cli(cli: DevopsCli, *argv: str) -> tuple[int, str, str]:
    out, err = io.StringIO(), io.StringIO()
    with redirect_stdout(out), redirect_stderr(err):
        code = cli.run(list(argv))
    return code, out.getvalue(), err.getvalue()


class NodeTestCase(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = TemporaryDirectory()
        self.root = Path(self._tmp.name)
        self.runner = StubRunner()
        patcher = mock.patch("support_python.devops.projects.resolve_executable", return_value=NPM)
        self.resolve = patcher.start()
        self.addCleanup(patcher.stop)

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def project(self, *, scripts: Optional[dict[str, str]] = None, failures: Sequence[str] = ()) -> NodeProject:
        make_repo(self.root, scripts)
        self.runner.failures = list(failures)
        return NodeProject(self.root, runner=self.runner)

    def cli(self, **kwargs: object) -> DevopsCli:
        return DevopsCli(self.project(**kwargs))


class NodeScriptMappingTests(NodeTestCase):
    def test_lint_runs_the_lint_script(self) -> None:
        code, _, _ = run_cli(self.cli(), "lint")
        self.assertEqual(code, 0)
        self.assertEqual(self.runner.tails(), [["run", "lint"]])

    def test_format_runs_the_format_script(self) -> None:
        run_cli(self.cli(), "format")
        self.assertEqual(self.runner.tails(), [["run", "format"]])

    def test_test_runs_npm_test(self) -> None:
        run_cli(self.cli(), "test")
        self.assertEqual(self.runner.tails(), [["test"]])

    def test_test_passes_selection_items_after_a_separator(self) -> None:
        run_cli(self.cli(), "test", "tests/core.test.js", "--", "--reporter=dot")
        self.assertEqual(self.runner.tails(), [["test", "--", "tests/core.test.js", "--reporter=dot"]])

    def test_build_runs_the_build_script_then_packs_into_dist(self) -> None:
        code, _, _ = run_cli(self.cli(), "build")
        self.assertEqual(code, 0)
        self.assertEqual(self.runner.tails(), [["run", "build"], ["pack", "--pack-destination", "dist"]])

    def test_build_without_a_build_script_only_packs(self) -> None:
        code, _, _ = run_cli(self.cli(scripts={"lint": "eslint .", "test": "vitest run"}), "build")
        self.assertEqual(code, 0)
        self.assertEqual(self.runner.tails(), [["pack", "--pack-destination", "dist"]])

    def test_build_starts_from_an_empty_dist(self) -> None:
        project = self.project()
        (self.root / "dist").mkdir()
        (self.root / "dist" / "demo-0.0.1.tgz").write_text("stale", encoding="utf-8")
        self.assertTrue(project.build())
        self.assertTrue((self.root / "dist").is_dir())
        self.assertEqual(list((self.root / "dist").iterdir()), [])

    def test_build_keeps_what_the_build_script_writes_to_dist(self) -> None:
        def runner(argv: Sequence[str], cwd: Path, logger: object) -> int:
            if list(argv[1:]) == ["run", "build"]:
                (cwd / "dist").mkdir()
                (cwd / "dist" / "index.js").write_text("", encoding="utf-8")
            return 0

        make_repo(self.root)
        self.assertTrue(NodeProject(self.root, runner=runner).build())
        self.assertTrue((self.root / "dist" / "index.js").is_file())

    def test_check_runs_lint_test_then_build(self) -> None:
        code, _, _ = run_cli(self.cli(), "check")
        self.assertEqual(code, 0)
        self.assertEqual(
            self.runner.tails(),
            [["run", "lint"], ["test"], ["run", "build"], ["pack", "--pack-destination", "dist"]],
        )

    def test_check_stops_at_the_first_failure(self) -> None:
        code, _, _ = run_cli(self.cli(failures=["lint"]), "check")
        self.assertEqual(code, 1)
        self.assertEqual(self.runner.tails(), [["run", "lint"]])

    def test_clean_removes_dist_without_running_npm(self) -> None:
        project = self.project()
        (self.root / "dist").mkdir()
        (self.root / "dist" / "demo-2.0.1.tgz").write_text("", encoding="utf-8")
        code, _, _ = run_cli(DevopsCli(project), "clean")
        self.assertEqual(code, 0)
        self.assertFalse((self.root / "dist").exists())
        self.assertEqual(self.runner.calls, [])

    def test_failed_script_exits_1(self) -> None:
        for action, failure in (("lint", "lint"), ("format", "format"), ("test", "test"), ("build", "pack")):
            with self.subTest(action=action):
                self.runner.calls.clear()
                code, _, _ = run_cli(self.cli(failures=[failure]), action)
                self.assertEqual(code, 1)

    def test_commands_run_npm_resolved_through_resolve_executable_in_the_root(self) -> None:
        run_cli(self.cli(), "lint")
        self.resolve.assert_called_with("npm")
        self.assertEqual(self.runner.calls[0][0], NPM)
        self.assertEqual(self.runner.cwds, [self.root.resolve()])


class NodeMissingScriptTests(NodeTestCase):
    def test_missing_script_fails_naming_the_script_and_package_json(self) -> None:
        for action, script in (("lint", "lint"), ("format", "format"), ("test", "test")):
            with self.subTest(action=action):
                self.runner.calls.clear()
                code, out, err = run_cli(self.cli(scripts={}), action)
                self.assertEqual(code, 1)
                self.assertIn(f"'{script}'", out + err)
                self.assertIn("package.json", out + err)
                self.assertEqual(self.runner.calls, [])

    def test_check_stops_before_test_when_lint_is_missing(self) -> None:
        code, _, _ = run_cli(self.cli(scripts={"test": "vitest run"}), "check")
        self.assertEqual(code, 1)
        self.assertEqual(self.runner.calls, [])

    def test_missing_package_json_fails_without_running_anything(self) -> None:
        project = NodeProject(self.root, runner=self.runner)
        code, out, err = run_cli(DevopsCli(project), "lint")
        self.assertEqual(code, 1)
        self.assertIn("package.json", out + err)
        self.assertEqual(self.runner.calls, [])

    def test_missing_npm_fails_without_running_anything(self) -> None:
        self.resolve.return_value = None
        code, out, err = run_cli(self.cli(), "lint")
        self.assertEqual(code, 1)
        self.assertIn("npm", out + err)
        self.assertEqual(self.runner.calls, [])


class NodeReleaseTests(NodeTestCase):
    def test_release_assets_are_the_packed_tarballs_in_dist(self) -> None:
        project = self.project()
        dist = self.root / "dist"
        dist.mkdir()
        for name in ("demo-b-2.0.1.tgz", "demo-a-2.0.1.tgz", "notes.txt"):
            (dist / name).write_text("", encoding="utf-8")
        self.assertEqual(project.release_assets(), [dist / "demo-a-2.0.1.tgz", dist / "demo-b-2.0.1.tgz"])

    def test_release_assets_are_empty_before_a_build(self) -> None:
        self.assertEqual(self.project().release_assets(), [])

    def test_release_uses_release_pipeline(self) -> None:
        self.assertIsNone(self.project().release())

    def test_help_examples_use_an_npm_test_selection(self) -> None:
        code, out, _ = run_cli(self.cli(), "help", "--verbose")
        self.assertEqual(code, 0)
        self.assertNotIn("tests/test_cli.py", out)
        self.assertIn("devops test test/cli.test.js", out)

    def test_versions_reads_package_json(self) -> None:
        code, out, err = run_cli(self.cli(), "versions")
        self.assertEqual(code, 0, out + err)
        self.assertIn("2.0.1-pre", out + err)


@pytest.mark.slow
@unittest.skipUnless(shutil.which("node") and shutil.which("npm"), "Node.js with npm is not installed")
class NodeNpmIntegrationTests(unittest.TestCase):
    """Runs the real npm through the real step runner."""

    def test_check_passes_and_leaves_a_tarball_in_dist(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            noop = 'node -e "process.exit(0)"'
            make_repo(root, {"lint": noop, "test": noop})
            code, out, err = run_cli(DevopsCli(NodeProject(root)), "check")
            self.assertEqual(code, 0, out + err)
            self.assertEqual([path.name for path in (root / "dist").glob("*.tgz")], ["demo-2.0.1-pre.tgz"])


if __name__ == "__main__":
    unittest.main()
