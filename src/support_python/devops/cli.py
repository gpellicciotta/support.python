"""Standard ``devops`` command line for a repository, built on :class:`~support_python.cli.ToolHarness`.

:class:`DevopsCli` exposes the operations of a :class:`~support_python.devops.projects.Project` as the
actions lint, format, test, build, check, clean, versions, and release, plus help and version.
:meth:`DevopsCli.set_deploy` adds a ``deploy`` action, and :meth:`DevopsCli.add_services` adds the opt-in
``docker``, ``db``, ``server``, ``mail``, and ``client`` action groups. A consumer's ``scripts/devops.py`` stays thin:
``sys.exit(DevopsCli(PythonProject(REPO_ROOT)).run())``.
"""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any, Callable, Optional, Sequence

from ..cli import ToolHarness
from ..logging import CliLogger
from .deploy import DeployContext, DeployPipeline, DeployStep
from .projects import Project
from .release import ReleasePipeline, capture_command, changelog_top_version, read_version
from .service_actions import ServiceActions
from .services import (
    CloudSqlProxyManager,
    LocalDockerManager,
    LocalMailManager,
    LocalMySqlManager,
    LocalServerManager,
    LocalVerifier,
)

#: Default description shown in the help screen.
DEFAULT_DESCRIPTION = "Runs the lint, format, test, build, check, clean, versions, and release operations of this project."

#: Exit codes of the standard actions.
EXIT_CODES: dict[int, str] = {
    0: "success",
    1: "an operation failed, the virtual environment is missing, or versions drift",
    2: "invalid arguments or unknown action",
}


class DevopsCli:
    """Standard ``devops`` command line over one :class:`~support_python.devops.projects.Project`.

    Attributes:
        project: Project whose operations the actions run.
        harness: Underlying :class:`~support_python.cli.ToolHarness`.
    """

    def __init__(self, project: Project, *, name: str = "devops", description: Optional[str] = None) -> None:
        self.project = project
        try:
            version = read_version(project.root)
        except (FileNotFoundError, ValueError):
            version = "0.0.0+unknown"
        self.harness = ToolHarness(
            name, description or DEFAULT_DESCRIPTION, version=version, exit_codes=EXIT_CODES, repo_dir=project.root
        )
        test_example = [f"{name} test {project.test_selection_example}"] if project.test_selection_example else []
        self.harness.set_examples([f"{name} check", *test_example, f"{name} versions", f"{name} release --dry-run"])
        self._add_standard_actions()

    def add_action(self, name: str, summary: str, handler: Callable[..., int], **kwargs: Any) -> None:
        """Register a project-specific action; ``kwargs`` go to :meth:`~support_python.cli.ToolHarness.add_action`."""
        self.harness.add_action(name, summary, handler, **kwargs)

    def set_deploy(
        self,
        steps: Sequence[DeployStep],
        verify: Optional[Callable[[DeployContext], bool]] = None,
        require_ci: bool = True,
        environment: str = "production",
        *,
        query: Callable[[Sequence[str], Path], tuple[int, str]] = capture_command,
        input_fn: Callable[[str], str] = input,
    ) -> None:
        """Enable the ``deploy`` action, which runs a :class:`~support_python.devops.deploy.DeployPipeline`.

        Args:
            steps: Project-local deploy steps, run in order and stopping at the first failure.
            verify: Optional post-deploy verification; returning ``False`` makes ``deploy`` exit 1.
            require_ci: Require a successful CI run for HEAD; ``--skip-ci-check`` overrides it per run.
            environment: Target environment named in the plan and the confirmation.
            query: Runs the read-only precondition queries as ``query(argv, root)``.
            input_fn: Prompt function used for the typed confirmation.
        """
        steps = tuple(steps)

        def handler(args: argparse.Namespace, logger: CliLogger) -> int:
            self.project.logger = logger
            pipeline = DeployPipeline(
                project=self.project,
                steps=steps,
                logger=logger,
                verify=verify,
                require_ci=require_ci and not args.skip_ci_check,
                environment=environment,
                dry_run=args.dry_run,
                assume_yes=args.yes,
                query=query,
                input_fn=input_fn,
            )
            return pipeline.run()

        names = ", ".join(step.name for step in steps) or "none"
        self.harness.add_action(
            "deploy",
            f"check the preconditions, confirm, and deploy the released version to {environment}",
            handler,
            detail=(
                f"Deploy the released version to {environment} after checking for a clean working tree, a version\n"
                "without -pre, a v<version> tag on origin at HEAD, and a successful CI run for HEAD.\n"
                f"Steps: {names}{'; then the post-deploy verification' if verify is not None else ''}."
            ),
            usage_suffix="[--dry-run] [--yes] [--skip-ci-check]",
            configure_parser=_configure_deploy,
        )
        example = f"{self.harness.name} deploy --dry-run"
        if example not in self.harness.examples:
            self.harness.examples.append(example)

    def add_services(
        self,
        *,
        docker: Optional[LocalDockerManager] = None,
        mysql: Optional[LocalMySqlManager] = None,
        proxy: Optional[CloudSqlProxyManager] = None,
        server: Optional[LocalServerManager] = None,
        mail: Optional[LocalMailManager] = None,
        verifier: Optional[LocalVerifier] = None,
        db_targets: Sequence[str] = ("local", "testdb"),
        service_url: Optional[str] = None,
        testdb_env_file: Optional[Path] = None,
    ) -> None:
        """Register the service action groups whose managers are supplied, such as ``devops db start``.

        Args:
            docker: Enables ``docker status|start``.
            mysql: Enables ``db status|start|stop|snapshot|load-snapshot``; ``server start`` also starts it.
            proxy: Enables ``db proxy``; its options override the manager's settings per run.
            server: Enables ``server status|start|stop``.
            mail: Enables ``mail test-emails``.
            verifier: Enables ``client verify|verify-deployment`` and ``server start --verify``.
            db_targets: Choices of ``db snapshot --load-target`` and ``db load-snapshot --target``: ``local``,
                ``testdb``, or ``<name>_test`` aliases, which load into the named Cloud SQL test database.
            service_url: Default ``--url`` of ``client verify-deployment``; without it, ``--url`` is required.
            testdb_env_file: Enables ``server start --testdb``, which runs the server with this environment file.

        Raises:
            ValueError: A ``db_targets`` entry is not ``local``, ``testdb``, or ``<name>_test``.
        """
        ServiceActions(
            docker=docker,
            mysql=mysql,
            proxy=proxy,
            server=server,
            mail=mail,
            verifier=verifier,
            db_targets=db_targets,
            service_url=service_url,
            testdb_env_file=testdb_env_file,
        ).register(self.harness)

    def run(self, argv: Optional[Sequence[str]] = None) -> int:
        """Run the command line in ``argv`` (default ``sys.argv[1:]``) and return its exit code."""
        return self.harness.run(argv)

    def _add_standard_actions(self) -> None:
        overrides = self.project.action_summaries()

        def add(name: str, summary: str, handler: Callable[..., int], **kwargs: Any) -> None:
            self.harness.add_action(name, overrides.get(name, summary), handler, **kwargs)

        add("lint", "check lint and formatting without changing files", self._operation("lint"), usage_suffix="")
        add("format", "reformat the sources in place", self._operation("format"), usage_suffix="")
        add(
            "test",
            "run the test suite, or a selection of it",
            self._test,
            detail="Run the test suite. Pass test paths or names as SELECTION; put runner options after `--`.",
            usage_suffix="[SELECTION...] [-- RUNNER-OPTIONS...]",
            configure_parser=lambda parser: parser.add_argument("selection", nargs="*"),
        )
        add("build", "build the distributable outputs from scratch", self._operation("build"), usage_suffix="")
        add(
            "check",
            "run lint, test, and build, stopping at the first failure",
            self._operation("check"),
            usage_suffix="",
        )
        add("clean", "remove build outputs", self._operation("clean"), usage_suffix="")
        add(
            "versions",
            "compare the version file with the CHANGELOG.md top heading",
            self._versions,
            detail="Compare the version file with the CHANGELOG.md top heading; exit 1 when they differ.",
            usage_suffix="",
        )
        add(
            "release",
            "freeze, tag, push, publish a GitHub release, and reopen development",
            self._release,
            detail=(
                "Release the project with ReleasePipeline after running `check` as its quality check.\n"
                "The project is rebuilt after the version freeze, and those outputs are attached to the GitHub release.\n"
                "A project with its own release, such as a GradleProject with a release_task, runs that instead."
            ),
            usage_suffix="[--dry-run] [--skip-checks] [--yes]",
            configure_parser=_configure_release,
        )

    def _operation(self, name: str) -> Callable[[argparse.Namespace, CliLogger], int]:
        def handler(args: argparse.Namespace, logger: CliLogger) -> int:
            self.project.logger = logger
            return 0 if getattr(self.project, name)() else 1

        return handler

    def _test(self, args: argparse.Namespace, logger: CliLogger) -> int:
        self.project.logger = logger
        return 0 if self.project.test(args.selection) else 1

    def _versions(self, args: argparse.Namespace, logger: CliLogger) -> int:
        root = self.project.root
        try:
            version = read_version(root)
        except (FileNotFoundError, ValueError) as exc:
            logger.error(str(exc))
            return 1
        changelog = root / "CHANGELOG.md"
        heading = changelog_top_version(changelog.read_text(encoding="utf-8")) if changelog.is_file() else None
        logger.info(f"Version file: {version}")
        logger.info(f"CHANGELOG.md: {heading or 'no version heading'}")
        if heading != version:
            logger.error(f"Version drift: version file has {version}, CHANGELOG.md has {heading or 'no version heading'}.")
            return 1
        logger.info("Versions agree.")
        return 0

    def _release(self, args: argparse.Namespace, logger: CliLogger) -> int:
        self.project.logger = logger
        released = self.project.release(dry_run=args.dry_run, assume_yes=args.yes)
        if released is not None:
            if args.skip_checks:
                logger.warning("--skip-checks has no effect on a project with its own release.")
            return 0 if released else 1
        pipeline = ReleasePipeline(
            root=self.project.root,
            logger=logger,
            quality_check=None if args.skip_checks else self.project.check,
            assets=self.project.release_assets,
            build=self.project.build,
            dry_run=args.dry_run,
            assume_yes=args.yes,
            runner=self.project.runner,
        )
        return pipeline.run()


def _configure_release(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--dry-run", action="store_true", help="log the planned steps without changing anything")
    parser.add_argument("--skip-checks", action="store_true", help="skip the `check` quality check")
    parser.add_argument("--yes", action="store_true", help="skip the typed confirmation")


def _configure_deploy(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--dry-run", action="store_true", help="check the preconditions and log the plan without deploying")
    parser.add_argument("--yes", action="store_true", help="skip the typed confirmation")
    parser.add_argument("--skip-ci-check", action="store_true", help="skip the CI check for HEAD")


__all__ = ["DEFAULT_DESCRIPTION", "DevopsCli", "EXIT_CODES"]
