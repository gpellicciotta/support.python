"""Project build adapters used by :class:`~support_python.devops.cli.DevopsCli`.

A :class:`Project` exposes the standard operations of one repository: lint, format, test, build, clean,
check, and the files to attach to a release. Every command runs through an injectable ``runner``, so tests
can stub it. :class:`PythonProject` runs ruff, pytest, and build through the repository's own ``.venv``.
"""

from __future__ import annotations

import shutil
import sys
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Callable, Optional, Sequence

from ..logging import CliLogger
from .steps import run_step_command

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
    """

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

    @abstractmethod
    def build(self) -> bool:
        """Build the distributable outputs from scratch."""

    @abstractmethod
    def clean(self) -> bool:
        """Remove build outputs."""

    def check(self) -> bool:
        """Run lint, then test, then build, stopping at the first failure."""
        return self.lint() and self.test() and self.build()

    def release_assets(self) -> list[Path]:
        """Return the build outputs to attach to a release."""
        return []

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


__all__ = ["Project", "PythonProject", "Runner"]
