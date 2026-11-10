"""Project build adapters used by :class:`~support_python.devops.cli.DevopsCli`.

A :class:`Project` exposes the standard operations of one repository: lint, format, test, build, clean,
check, and the files to attach to a release. Every command runs through an injectable ``runner``, so tests
can stub it. :class:`PythonProject` runs ruff, pytest, and build through the repository's own ``.venv``;
:class:`GradleProject` runs Gradle tasks through the repository's own Gradle wrapper; :class:`NodeProject` runs
npm scripts.
"""

from __future__ import annotations

import json
import shutil
import sys
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Callable, Optional, Sequence

from ..logging import CliLogger
from .release import confirm_typed, read_version, release_version
from .steps import resolve_executable, run_step_command

#: Runs a command as ``runner(argv, cwd, logger)`` and returns its exit code.
Runner = Callable[[Sequence[str], Path, Optional[CliLogger]], int]


class Project(ABC):
    """Standard operations of one repository rooted at ``root``.

    Version access goes through :func:`~support_python.devops.release.read_version` on ``root``.

    Attributes:
        root: Repository root; every command runs there.
        runner: Runs a command as ``runner(argv, root, logger)`` and returns its exit code.
        logger: Logger receiving progress and errors; :class:`~support_python.devops.cli.DevopsCli` replaces it
            with the logger of the running action.
        test_selection_example: Selection shown in the ``devops test`` help example; empty omits the example.

    :class:`~support_python.devops.cli.DevopsCli` reads the help summaries and the example once, when it is built,
    so set adapter attributes such as task lists before building it.
    """

    test_selection_example: str = ""

    def __init__(self, root: Path, *, runner: Runner = run_step_command, logger: Optional[CliLogger] = None) -> None:
        self.root = Path(root).resolve()
        self.runner = runner
        self.logger = logger if logger is not None else CliLogger()

    @abstractmethod
    def lint(self) -> bool:
        """Run the linters and format checks without changing files."""

    @abstractmethod
    def format(self) -> bool:
        """Reformat the sources in place."""

    @abstractmethod
    def test(self, selection: Sequence[str] = ()) -> bool:
        """Run the test suite, or the tests and runner options in ``selection``."""

    def test_slow(self, selection: Sequence[str] = ()) -> bool:
        """Run the slow test suite, or skip it when the project has none."""
        self.logger.info("No slow test suite configured; skipping.")
        return True

    @abstractmethod
    def build(self) -> bool:
        """Build the distributable outputs from scratch."""

    @abstractmethod
    def clean(self) -> bool:
        """Remove build outputs."""

    def check(self) -> bool:
        """Run lint, then test, then test_slow, then build, stopping at the first failure."""
        return self.lint() and self.test() and self.test_slow() and self.build()

    def release_assets(self) -> list[Path]:
        """Return the build outputs to attach to a release."""
        return []

    def action_summaries(self) -> dict[str, str]:
        """Return help summaries replacing the generic ones of :class:`~support_python.devops.cli.DevopsCli`, by action."""
        return {}

    def release(self, *, dry_run: bool = False, assume_yes: bool = False) -> Optional[bool]:
        """Run the project's own release instead of :class:`~support_python.devops.release.ReleasePipeline`.

        Returns:
            Whether the release succeeded, or ``None`` when the project has no own release (the default).
        """
        return None

    def run_command(self, argv: Sequence[str]) -> bool:
        """Run one command in ``root`` through ``runner`` and return whether it succeeded."""
        return self.runner([str(arg) for arg in argv], self.root, self.logger) == 0

    def remove_tree(self, path: Path) -> None:
        """Remove the directory ``path`` when it exists."""
        if path.exists():
            self.logger.info(f"Removing {path.relative_to(self.root).as_posix()}")
            shutil.rmtree(path)


class PythonProject(Project):
    """A Python project with a ``.venv`` holding ruff, pytest, and build, and a src layout."""

    test_selection_example = "tests/test_cli.py -- -k version"

    @property
    def venv_python(self) -> Path:
        """Return the venv's own python executable (``Scripts/python.exe`` on Windows, ``bin/python`` elsewhere)."""
        return self.root / ".venv" / ("Scripts/python.exe" if sys.platform == "win32" else "bin/python")

    @property
    def dist_dir(self) -> Path:
        return self.root / "dist"

    def lint(self) -> bool:
        return self._python("-m", "ruff", "check", ".") and self._python("-m", "ruff", "format", "--check", ".")

    def format(self) -> bool:
        return self._python("-m", "ruff", "format", ".")

    def test(self, selection: Sequence[str] = ()) -> bool:
        return self._python("-m", "pytest", "-q", *selection)

    def test_slow(self, selection: Sequence[str] = ()) -> bool:
        return self._python("-m", "pytest", "-m", "slow", "--timeout=120", *selection)

    def build(self) -> bool:
        if not self._has_venv():
            return False
        self.remove_tree(self.dist_dir)
        return self._python("-m", "build", "-o", "dist")

    def clean(self) -> bool:
        for path in (self.dist_dir, self.root / "build", *sorted((self.root / "src").glob("*.egg-info"))):
            self.remove_tree(path)
        return True

    def release_assets(self) -> list[Path]:
        return sorted(self.dist_dir.glob("*.whl")) + sorted(self.dist_dir.glob("*.tar.gz"))

    def _has_venv(self) -> bool:
        if self.venv_python.is_file():
            return True
        self.logger.error(f"Virtual environment missing at {self.venv_python}; run scripts/bootstrap-dev-environment.py first.")
        return False

    def _python(self, *args: str) -> bool:
        return self._has_venv() and self.run_command([str(self.venv_python), *args])


class GradleProject(Project):
    """A Gradle project with a Gradle wrapper at its root and the version in ``gradle.properties``.

    Every keyword task list replaces the default Gradle tasks of its operation. ``check`` runs ``build`` once,
    since Gradle's ``build`` already runs the checks and tests.

    Attributes:
        lint_tasks: Tasks run by :meth:`lint`.
        format_tasks: Tasks run by :meth:`format`.
        test_tasks: Tasks run by :meth:`test`.
        slow_test_tasks: Tasks run by :meth:`test_slow`.
        build_tasks: Tasks run by :meth:`build`.
        check_tasks: Tasks run by :meth:`check`.
        clean_tasks: Tasks run by :meth:`clean`.
        gradle_options: Options passed to every Gradle invocation.
        release_task: Gradle task replacing ``ReleasePipeline`` in ``devops release``, or ``None``.
        release_args: Extra arguments passed to ``release_task`` after the confirmation.
    """

    test_selection_example = "com.example.AppTest"

    def __init__(
        self,
        root: Path,
        *,
        runner: Runner = run_step_command,
        logger: Optional[CliLogger] = None,
        lint_tasks: Sequence[str] = ("spotlessCheck", "checkstyleMain", "checkstyleTest"),
        format_tasks: Sequence[str] = ("spotlessApply",),
        test_tasks: Sequence[str] = ("test",),
        slow_test_tasks: Sequence[str] = ("slowTest",),
        build_tasks: Sequence[str] = ("build",),
        check_tasks: Sequence[str] = ("build",),
        clean_tasks: Sequence[str] = ("clean",),
        gradle_options: Sequence[str] = ("--console=plain",),
        release_task: Optional[str] = None,
        release_args: Sequence[str] = (),
    ) -> None:
        super().__init__(root, runner=runner, logger=logger)
        self.lint_tasks = list(lint_tasks)
        self.format_tasks = list(format_tasks)
        self.test_tasks = list(test_tasks)
        self.slow_test_tasks = list(slow_test_tasks)
        self.build_tasks = list(build_tasks)
        self.check_tasks = list(check_tasks)
        self.clean_tasks = list(clean_tasks)
        self.gradle_options = list(gradle_options)
        self.release_task = release_task
        self.release_args = list(release_args)

    @property
    def wrapper(self) -> Path:
        """Return the Gradle wrapper (``gradlew.bat`` on Windows, ``gradlew`` elsewhere)."""
        return self.root / ("gradlew.bat" if sys.platform == "win32" else "gradlew")

    def lint(self) -> bool:
        return self._gradle(*self.lint_tasks)

    def format(self) -> bool:
        return self._gradle(*self.format_tasks)

    def test(self, selection: Sequence[str] = ()) -> bool:
        """Run ``test_tasks`` with a ``--tests`` filter per selection item; items starting with ``-`` pass unchanged."""
        filters: list[str] = []
        for item in selection:
            filters.extend([item] if item.startswith("-") else ["--tests", item])
        return self._gradle(*self.test_tasks, *filters)

    def test_slow(self, selection: Sequence[str] = ()) -> bool:
        """Run ``slow_test_tasks`` with a ``--tests`` filter per selection item; skip when empty."""
        if not self.slow_test_tasks:
            self.logger.info("No slow test tasks configured; skipping.")
            return True
        filters: list[str] = []
        for item in selection:
            filters.extend([item] if item.startswith("-") else ["--tests", item])
        return self._gradle(*self.slow_test_tasks, *filters)

    def build(self) -> bool:
        return self._gradle(*self.build_tasks)

    def check(self) -> bool:
        return self._gradle(*self.check_tasks)

    def clean(self) -> bool:
        return self._gradle(*self.clean_tasks)

    def release_assets(self) -> list[Path]:
        return sorted(self.root.glob("build/libs/*.jar")) + sorted(self.root.glob("*/build/libs/*.jar"))

    def action_summaries(self) -> dict[str, str]:
        """Return help summaries naming the Gradle tasks each action runs."""

        def tasks(names: Sequence[str]) -> str:
            return " ".join(names) or "(default tasks)"

        summaries = {
            "lint": f"check lint and formatting: gradle {tasks(self.lint_tasks)}",
            "format": f"reformat the sources in place: gradle {tasks(self.format_tasks)}",
            "test": f"run the tests, adding --tests per selection item: gradle {tasks(self.test_tasks)}",
            "build": f"build the outputs: gradle {tasks(self.build_tasks)}",
            "check": f"run the full check: gradle {tasks(self.check_tasks)}",
            "clean": f"remove build outputs: gradle {tasks(self.clean_tasks)}",
        }
        if self.release_task is not None:
            summaries["release"] = f"confirm, then release with the Gradle task {self.release_task}"
        return summaries

    def release(
        self, *, dry_run: bool = False, assume_yes: bool = False, input_fn: Optional[Callable[[str], str]] = None
    ) -> Optional[bool]:
        """Run ``release_task`` after the typed confirmation, or with Gradle's ``--dry-run`` and no confirmation.

        ``input_fn`` prompts for the confirmation and defaults to :func:`input`. Returns ``None`` without a
        ``release_task``, so ``devops release`` runs ``ReleasePipeline``.
        """
        if self.release_task is None:
            return None
        if dry_run:
            return self._gradle(self.release_task, "--dry-run")
        try:
            tag = f"v{release_version(read_version(self.root))}"
        except (FileNotFoundError, ValueError) as exc:
            self.logger.error(str(exc))
            return False
        if not assume_yes:
            summary = [f"About to release {tag} with the Gradle task '{self.release_task}'."]
            if not confirm_typed(summary, f"release {tag}", input_fn=input_fn or input):
                self.logger.error("Release not confirmed; nothing was changed.")
                return False
        return self._gradle(self.release_task, *self.release_args)

    def _gradle(self, *args: str) -> bool:
        if not self.wrapper.is_file():
            self.logger.error(f"Gradle wrapper missing at {self.wrapper}; run `gradle wrapper` to generate it.")
            return False
        return self.run_command([str(self.wrapper), *self.gradle_options, *args])


class NodeProject(Project):
    """An npm project with its scripts and version in ``package.json``.

    npm resolves through :func:`~support_python.devops.steps.resolve_executable`, so Windows finds ``npm.cmd``.
    ``build`` runs the ``build`` script when ``package.json`` defines one, then packs the tarball into ``dist/``.
    """

    test_selection_example = "test/cli.test.js"

    @property
    def dist_dir(self) -> Path:
        return self.root / "dist"

    def lint(self) -> bool:
        return self._npm_script("lint")

    def format(self) -> bool:
        return self._npm_script("format")

    def test(self, selection: Sequence[str] = ()) -> bool:
        """Run ``npm test``, passing ``selection`` to the test script after ``--``."""
        return self._has_script("test") and self._npm("test", *(["--", *selection] if selection else []))

    def test_slow(self, selection: Sequence[str] = ()) -> bool:
        """Run ``npm run test:slow``, passing ``selection`` after ``--``, or skip when undefined."""
        scripts = self._scripts()
        if scripts is None:
            return False
        if "test:slow" not in scripts:
            self.logger.info("npm script 'test:slow' is not defined in package.json; skipping.")
            return True
        return self._npm("run", "test:slow", *(["--", *selection] if selection else []))

    def build(self) -> bool:
        scripts = self._scripts()
        if scripts is None:
            return False
        self.remove_tree(self.dist_dir)
        if "build" in scripts and not self._npm("run", "build"):
            return False
        self.dist_dir.mkdir(exist_ok=True)
        return self._npm("pack", "--pack-destination", "dist")

    def clean(self) -> bool:
        self.remove_tree(self.dist_dir)
        return True

    def release_assets(self) -> list[Path]:
        return sorted(self.dist_dir.glob("*.tgz"))

    def _scripts(self) -> Optional[dict]:
        manifest = self.root / "package.json"
        try:
            scripts = json.loads(manifest.read_text(encoding="utf-8")).get("scripts", {})
        except FileNotFoundError:
            self.logger.error(f"package.json missing at {manifest}.")
            return None
        except (ValueError, AttributeError) as exc:
            self.logger.error(f"Cannot read the scripts of {manifest}: {exc}")
            return None
        return scripts if isinstance(scripts, dict) else {}

    def _has_script(self, name: str) -> bool:
        scripts = self._scripts()
        if scripts is None:
            return False
        if name not in scripts:
            self.logger.error(f"npm script '{name}' is not defined in package.json.")
            return False
        return True

    def _npm_script(self, name: str) -> bool:
        return self._has_script(name) and self._npm("run", name)

    def _npm(self, *args: str) -> bool:
        npm = resolve_executable("npm")
        if npm is None:
            self.logger.error("npm not found on PATH; install Node.js with npm first.")
            return False
        return self.run_command([npm, *args])


__all__ = ["GradleProject", "NodeProject", "Project", "PythonProject", "Runner"]
