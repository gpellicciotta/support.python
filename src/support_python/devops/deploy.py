"""Deploy steps, their context, and the dry-runnable pipeline behind the ``deploy`` action of ``DevopsCli``.

The preconditions, the typed confirmation, and the post-deploy verification are shared; the steps stay
project-local. A step is either a command, run through the project's runner, or a callable taking a
:class:`DeployContext`.
"""

from __future__ import annotations

import json
import subprocess
import tempfile
import time
import uuid
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Optional, Sequence

from ..git import parse_status_porcelain
from ..logging import CliLogger
from .projects import Project
from .release import capture_command, confirm_typed, read_version
from .steps import EXIT_COMMAND_NOT_FOUND

#: Conclusions of a GitHub Actions run that count as failed.
FAILED_CONCLUSIONS = frozenset({"failure", "timed_out", "startup_failure"})

#: Attempts to remove the temporary worktree, and the seconds waited between them.
CLEANUP_ATTEMPTS = 3
CLEANUP_DELAY = 0.5


@dataclass(frozen=True)
class DeployStep:
    """One project-local deploy step: exactly one of ``command`` and ``action``.

    Attributes:
        name: Short name shown in the plan, the confirmation, and failure messages.
        command: Command run in the deploy root (``DeployContext.root``) through the project's runner; exit code 0 is success.
        action: Callable receiving the :class:`DeployContext` and returning success.
    """

    name: str
    command: Sequence[str] | None = None
    action: Callable[[DeployContext], bool] | None = None

    def __post_init__(self) -> None:
        """Require exactly one of ``command`` and ``action`` and freeze the command into a tuple."""
        if (self.command is None) == (self.action is None):
            raise ValueError(f"Deploy step '{self.name}' needs exactly one of command and action")
        if self.command is not None:
            object.__setattr__(self, "command", tuple(str(arg) for arg in self.command))

    def describe(self) -> str:
        """Return the step name, followed by its command line for a command step."""
        return f"{self.name}: {subprocess.list2cmdline(self.command)}" if self.command is not None else self.name


@dataclass
class DeployContext:
    """State handed to action steps and to the verification callback.

    Attributes:
        project: Project being deployed.
        version: Deployed version, without a leading ``v``.
        logger: Logger of the running ``deploy`` action.
        dry_run: Whether the deploy is a dry run.
        root: Folder the deploy runs from: the project root, or the temporary worktree of the tag for
            ``deploy VERSION``. Action steps and ``verify`` must use this, not ``project.root``.
    """

    project: Project
    version: str
    logger: CliLogger
    dry_run: bool = False
    root: Optional[Path] = None

    def __post_init__(self) -> None:
        """Default ``root`` to the project root."""
        if self.root is None:
            self.root = Path(self.project.root)


@dataclass
class DeployPipeline:
    """Deploy ``project``: check the preconditions, confirm, run the steps in order, then verify.

    The preconditions are a clean working tree, a version without ``-pre``, a tag ``v<version>`` on
    ``origin`` pointing at HEAD, and, with ``require_ci``, a successful CI run for HEAD with none failed.

    Attributes:
        project: Project to deploy; its runner runs the command steps.
        steps: Steps run in order, stopping at the first failure.
        logger: Logger receiving progress, the plan, and errors.
        verify: Optional callback run after the last step; returning ``False`` fails the deploy.
        require_ci: Check the GitHub Actions runs for HEAD with ``gh``.
        environment: Target environment named in the plan and the confirmation.
        dry_run: Check the preconditions and log the plan without prompting or running anything.
        assume_yes: Skip the typed confirmation.
        query: Runs a read-only command as ``query(argv, root)`` and returns its exit code and output.
        input_fn: Prompt function used for the typed confirmation.
        version: Version to deploy, with or without a leading ``v``. Set, the deploy runs from a temporary
            worktree of its tag, and the dirty-tree and tag-at-HEAD checks are skipped.
    """

    project: Project
    steps: Sequence[DeployStep]
    logger: CliLogger
    verify: Callable[[DeployContext], bool] | None = None
    require_ci: bool = True
    environment: str = "production"
    dry_run: bool = False
    assume_yes: bool = False
    query: Callable[[Sequence[str], Path], tuple[int, str]] = capture_command
    input_fn: Callable[[str], str] = input
    version: Optional[str] = None

    def run(self) -> int:
        """Run the pipeline.

        Returns:
            0 when deployed and verified, or when a dry run completes; 1 when a precondition, the
            confirmation, a step, or the verification fails. A failed step leaves earlier steps in place.
        """
        if self.version:
            return self._run_tag(self.version)
        root = Path(self.project.root)
        try:
            version = read_version(root)
        except (FileNotFoundError, ValueError) as exc:
            return self._fail(str(exc))
        tag = f"v{version}"
        self.logger.info(f"Deploy version: {tag}")
        self.logger.info(f"Environment: {self.environment}")
        self.logger.info(f"Dry run: {self.dry_run}")
        if not self._check_preconditions(root, version, tag):
            return 1

        plan = self._plan()
        if self.dry_run:
            for number, description in enumerate(plan, 1):
                self.logger.info(f"[dry-run] {number}. {description}")
            self.logger.info(f"[dry-run] Nothing was deployed to {self.environment}.")
            return 0
        if not self.assume_yes:
            summary = [f"About to deploy {tag} to {self.environment}:", *(f"  {number}. {d}" for number, d in enumerate(plan, 1))]
            if not confirm_typed(summary, f"deploy {tag}", input_fn=self.input_fn):
                return self._fail("Deploy not confirmed; nothing was run.")

        return self._execute(DeployContext(self.project, version, self.logger, dry_run=False, root=root), tag)

    def _execute(self, context: DeployContext, tag: str) -> int:
        """Run the steps in ``context.root``, then the verification."""
        for step in self.steps:
            self.logger.info(f"Deploy step: {step.describe()}")
            if not self._run_step(step, context):
                return self._fail(f"Deploy step failed: {step.name}. Later steps were skipped; earlier ones were not rolled back.")
        if self.verify is not None:
            self.logger.info("Verifying the deployment.")
            if not self.verify(context):
                return self._fail(f"Post-deploy verification of {tag} in {self.environment} failed.")
        self.logger.info(f"Deployed {tag} to {self.environment}.")
        return 0

    def _plan(self) -> list[str]:
        plan = [step.describe() for step in self.steps]
        if self.verify is not None:
            plan.append("verify the deployment")
        return plan

    def _run_tag(self, requested: str) -> int:
        """Deploy ``requested`` from a temporary worktree of its tag, removing the worktree afterwards."""
        root = Path(self.project.root)
        version = requested[1:] if requested[:1] in ("v", "V") else requested
        tag = f"v{version}"
        self.logger.info(f"Deploy version: {tag}")
        self.logger.info(f"Environment: {self.environment}")
        self.logger.info(f"Dry run: {self.dry_run}")
        tagged = self._resolve_tag(root, tag)
        if tagged is None:
            return 1
        if version.endswith("-pre"):
            return self._fail(f"Version {version} is still in development; release it before deploying.")
        if self.require_ci and not self._check_ci(root, tagged, f"tag {tag}"):
            return 1

        folder = Path(tempfile.gettempdir()) / f"deploy-{tag}-{uuid.uuid4().hex[:8]}"
        plan = self._plan()
        if self.dry_run:
            self.logger.info(f"[dry-run] 0. create a temporary worktree of {tag} ({tagged[:12]}) in {folder}")
            for number, description in enumerate(plan, 1):
                self.logger.info(f"[dry-run] {number}. {description}")
            self.logger.info(f"[dry-run] Nothing was deployed to {self.environment}.")
            return 0
        if not self.assume_yes:
            summary = [
                f"About to deploy {tag} to {self.environment} from a temporary worktree in {folder}:",
                *(f"  {number}. {d}" for number, d in enumerate(plan, 1)),
            ]
            if not confirm_typed(summary, f"deploy {tag}", input_fn=self.input_fn):
                return self._fail("Deploy not confirmed; nothing was run.")

        try:
            if not self._create_worktree(root, folder, tag, tagged):
                return 1
            try:
                actual = read_version(folder)
            except (FileNotFoundError, ValueError) as exc:
                return self._fail(str(exc))
            if actual != version:
                return self._fail(f"Tag '{tag}' contains version {actual}, not {version}; the tag is wrong.")
            return self._execute(DeployContext(self.project, version, self.logger, dry_run=False, root=folder), tag)
        finally:
            self._remove_worktree(root, folder)

    def _resolve_tag(self, root: Path, tag: str) -> Optional[str]:
        """Return the commit ``tag`` points at on origin, or log the failure and return ``None``."""
        code, out = self.query(["git", "ls-remote", "origin", f"refs/tags/{tag}", f"refs/tags/{tag}^{{}}"], root)
        if code != 0:
            self._fail(f"Could not list the tags on origin: {out}")
            return None
        refs: dict[str, str] = {}
        for line in out.splitlines():
            sha, _, ref = line.partition("\t")
            refs[ref.strip()] = sha.strip()
        tagged = refs.get(f"refs/tags/{tag}^{{}}") or refs.get(f"refs/tags/{tag}")
        if not tagged:
            self._fail(f"Tag '{tag}' is not on origin; release {tag} before deploying it.")
            return None
        return tagged

    def _create_worktree(self, root: Path, folder: Path, tag: str, tagged: str) -> bool:
        """Fetch the tag commit and check it out detached in ``folder``; submodules follow when present."""
        self.logger.info(f"Creating a temporary worktree of {tag} in {folder}")
        for argv in (
            ["git", "fetch", "--quiet", "origin", f"refs/tags/{tag}"],
            ["git", "worktree", "add", "--detach", str(folder), tagged],
        ):
            code, out = self.query(argv, root)
            if code != 0:
                self.logger.error(f"'{' '.join(argv[:3])}' failed: {out.strip()}")
                return False
        if (folder / ".gitmodules").exists():
            code, out = self.query(["git", "submodule", "update", "--init", "--recursive"], folder)
            if code != 0:
                self.logger.error(f"Could not check out the submodules: {out.strip()}")
                return False
        return True

    def _remove_worktree(self, root: Path, folder: Path) -> None:
        """Remove the worktree with retries; a failure logs a warning and never changes the result."""
        if not folder.exists():
            self.query(["git", "worktree", "prune"], root)
            return
        out = ""
        for attempt in range(CLEANUP_ATTEMPTS):
            code, out = self.query(["git", "worktree", "remove", "--force", str(folder)], root)
            if code == 0:
                return
            if attempt + 1 < CLEANUP_ATTEMPTS:
                time.sleep(CLEANUP_DELAY)
        self.logger.warning(f"Could not remove the temporary worktree {folder}: {out.strip()}; remove it manually.")

    def _fail(self, message: str) -> int:
        self.logger.error(message)
        return 1

    def _run_step(self, step: DeployStep, context: DeployContext) -> bool:
        if step.command is not None:
            return self.project.runner(list(step.command), Path(context.root or self.project.root), self.logger) == 0
        return bool(step.action(context)) if step.action is not None else False

    def _check_preconditions(self, root: Path, version: str, tag: str) -> bool:
        """Return whether every precondition holds; otherwise log the first failure."""

        def fail(message: str) -> bool:
            self.logger.error(message)
            return False

        code, out = self.query(["git", "status", "--porcelain=v1", "-z", "--untracked-files=all"], root)
        if code != 0:
            return fail(f"Could not read the git status: {out}")
        dirty = sorted({entry["path"] for entry in parse_status_porcelain(out)})
        if dirty:
            return fail(f"Uncommitted changes in: {', '.join(dirty)}; commit or stash them before deploying.")

        if version.endswith("-pre"):
            return fail(f"Version {version} is still in development; release it before deploying.")

        code, out = self.query(["git", "rev-parse", "HEAD"], root)
        if code != 0:
            return fail(f"Could not resolve HEAD: {out}")
        head = out.strip()
        tagged = self._resolve_tag(root, tag)
        if tagged is None:
            return False
        if tagged != head:
            return fail(f"Tag '{tag}' on origin points at {tagged[:12]}, not HEAD ({head[:12]}); check out {tag} first.")

        return self._check_ci(root, head) if self.require_ci else True

    def _check_ci(self, root: Path, head: str, label: str = "HEAD") -> bool:
        """Return whether a completed CI run for ``head`` succeeded and none failed."""

        def fail(message: str) -> bool:
            self.logger.error(f"{message}; pass --skip-ci-check to deploy without the CI check.")
            return False

        code, out = self.query(["gh", "run", "list", "--commit", head, "--json", "status,conclusion", "--limit", "20"], root)
        if code == EXIT_COMMAND_NOT_FOUND:
            return fail("The 'gh' CLI is not installed (see https://cli.github.com/), so the CI runs cannot be checked")
        if code != 0:
            return fail(f"Could not list the CI runs for {label}: {out}")
        try:
            runs = json.loads(out)
        except json.JSONDecodeError:
            return fail(f"Could not parse the CI runs for {label}: {out.strip()[:200]}")
        if not isinstance(runs, list) or not all(isinstance(run, dict) for run in runs):
            return fail(f"Unexpected CI run list for {label}: {out.strip()[:200]}")
        if any(run.get("conclusion") in FAILED_CONCLUSIONS for run in runs):
            return fail(f"A CI run for {label} ({head[:12]}) failed")
        if not any(run.get("status") == "completed" and run.get("conclusion") == "success" for run in runs):
            return fail(f"No successful CI run for {label} ({head[:12]}) yet")
        return True


__all__ = ["FAILED_CONCLUSIONS", "DeployContext", "DeployPipeline", "DeployStep"]
