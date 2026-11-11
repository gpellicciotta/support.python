"""Opt-in ``docker``, ``db``, ``server``, ``mail``, and ``client`` action groups backed by the service managers.

Each group is one :class:`~support_python.cli.ToolHarness` action whose first positional argument selects a
sub-action, as in ``devops db start``. A group is registered only when its manager is supplied; the options of
all sub-actions of a group share one parser. :meth:`support_python.devops.cli.DevopsCli.add_services` is the
usual entry point; :meth:`ServiceActions.register` registers the groups on any harness.
"""

from __future__ import annotations

import argparse
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Optional, Sequence

from ..cli import ToolHarness
from ..logging import CliLogger
from ..net import is_port_in_use
from .services import (
    CloudSqlProxyManager,
    LocalDockerManager,
    LocalMailManager,
    LocalMySqlManager,
    LocalServerManager,
    LocalVerifier,
)

#: Handler of one sub-action, called with the parsed arguments and the run's logger.
SubActionHandler = Callable[[argparse.Namespace, CliLogger], int]


@dataclass(frozen=True)
class SubAction:
    """One sub-action of a service action group."""

    name: str
    summary: str
    handler: SubActionHandler
    #: Destination of the group-level positional argument this sub-action reads; other sub-actions reject it.
    positional: Optional[str] = None


class ServiceActions:
    """Service managers and the handlers of the action groups they back.

    Attributes:
        docker: Backs the ``docker`` group.
        mysql: Backs the ``db`` sub-actions other than ``proxy``; ``server start`` also starts it.
        proxy: Backs ``db proxy``.
        server: Backs the ``server`` group.
        mail: Backs the ``mail`` group.
        verifier: Backs the ``client`` group and ``server start --verify``.
        db_targets: Database targets accepted by ``db snapshot --load-target`` and ``db load-snapshot --target``.
        service_url: Default ``--url`` of ``client verify-deployment``; without it, ``--url`` is required.
        testdb_env_file: Environment file of ``server start --testdb``; without it, ``--testdb`` is not offered.

    Raises:
        ValueError: A ``db_targets`` entry is not a :meth:`LocalMySqlManager.is_valid_target` target.
    """

    def __init__(
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
        """Create the actions from the optional service managers; see the class docstring for the arguments."""
        invalid = [target for target in db_targets if not LocalMySqlManager.is_valid_target(target)]
        if invalid:
            raise ValueError(f"Unsupported db_targets {invalid}: use 'local', 'testdb', or '<name>_test'.")
        self.docker, self.mysql, self.proxy = docker, mysql, proxy
        self.server, self.mail, self.verifier = server, mail, verifier
        self.db_targets = tuple(db_targets)
        self.service_url = service_url
        self.testdb_env_file = Path(testdb_env_file) if testdb_env_file is not None else None

    def register(self, harness: ToolHarness) -> None:
        """Register the group of every supplied manager on ``harness``."""
        if self.docker is not None:
            self._add_group(
                harness,
                "docker",
                "manage the Docker Desktop engine",
                [
                    SubAction("status", "check the Docker engine status", self._docker_status),
                    SubAction("start", "launch Docker Desktop and wait for engine readiness", self._docker_start),
                ],
                example="docker status",
            )
        if self.mysql is not None or self.proxy is not None:
            db: list[SubAction] = []
            if self.mysql is not None:
                db += [
                    SubAction("status", "check the MySQL container status", self._db_status),
                    SubAction("start", "start the isolated MySQL container", self._db_start),
                    SubAction("stop", "stop the MySQL container", self._db_stop),
                    SubAction("snapshot", "extract and anonymize a database snapshot", self._db_snapshot),
                    SubAction(
                        "load-snapshot",
                        "load a SQL snapshot into a local or test database",
                        self._db_load_snapshot,
                        positional="snapshot_path",
                    ),
                ]
            if self.proxy is not None:
                db.append(SubAction("proxy", "launch the Cloud SQL Auth Proxy for remote database access", self._db_proxy))
            self._add_group(
                harness,
                "db",
                "manage the local MySQL container, snapshots, and the Cloud SQL proxy",
                db,
                configure=self._configure_db,
                example="db start" if self.mysql is not None else "db proxy",
                note="Put a positional snapshot path directly after load-snapshot, or use --snapshot-path.",
            )
        if self.server is not None:
            self._add_group(
                harness,
                "server",
                "manage the local application server",
                [
                    SubAction("status", "check the application server status", self._server_status),
                    SubAction("start", "start the application server, after MySQL unless --memory-db", self._server_start),
                    SubAction("stop", "stop the application server", self._server_stop),
                ],
                configure=self._configure_server,
                example="server start --background",
            )
        if self.mail is not None:
            self._add_group(
                harness,
                "mail",
                "send test emails through the application server",
                [
                    SubAction(
                        "test-emails",
                        "send sample emails for all templates to a recipient",
                        self._mail_test_emails,
                        positional="recipient",
                    )
                ],
                configure=_configure_mail,
                default="test-emails",
                example="mail test-emails me@example.com",
            )
        if self.verifier is not None:
            self._add_group(
                harness,
                "client",
                "verify the running server or a live deployment",
                [
                    SubAction("verify", "run the automated verification checks against the running server", self._client_verify),
                    SubAction("verify-deployment", "verify the live deployment status and version", self._client_verify_deployment),
                ],
                configure=self._configure_client,
                default="verify",
                example="client verify-deployment",
            )

    def _add_group(
        self,
        harness: ToolHarness,
        name: str,
        summary: str,
        sub_actions: Sequence[SubAction],
        *,
        configure: Optional[Callable[[argparse.ArgumentParser], None]] = None,
        default: str = "status",
        example: str = "",
        note: str = "",
    ) -> None:
        by_name = {sub.name: sub for sub in sub_actions}
        default_name = default if default in by_name else None

        def configure_parser(parser: argparse.ArgumentParser) -> None:
            if default_name is None:
                parser.add_argument("subaction", choices=list(by_name))
            else:
                parser.add_argument("subaction", nargs="?", default=default_name, choices=list(by_name))
            if configure is not None:
                configure(parser)

        def handler(args: argparse.Namespace, logger: CliLogger) -> int:
            self._bind(logger)
            sub_action = by_name[args.subaction]
            for dest in {sub.positional for sub in sub_actions if sub.positional and sub is not sub_action}:
                if getattr(args, dest, None) is not None:
                    logger.error(f"Unexpected argument '{getattr(args, dest)}' for `{name} {sub_action.name}`.")
                    return 2
            return sub_action.handler(args, logger)

        width = max(len(sub_name) for sub_name in by_name) + 2
        detail = [f"{summary[0].upper()}{summary[1:]}. Sub-actions:"]
        detail += [f"  {sub.name:<{width}}{sub.summary}" for sub in sub_actions]
        if default_name is not None:
            detail.append(f"Without a sub-action, `{name}` runs `{name} {default_name}`.")
        if note:
            detail.append(note)
        harness.add_action(
            name,
            summary,
            handler,
            detail="\n".join(detail),
            usage_suffix="{" + "|".join(by_name) + "} [options]",
            configure_parser=configure_parser,
        )
        command = f"{harness.name} {example}"
        if example and command not in harness.examples:
            harness.examples.append(command)

    def _bind(self, logger: CliLogger) -> None:
        for manager in (self.docker, self.mysql, self.proxy, self.server, self.mail, self.verifier):
            if manager is not None:
                manager.logger = logger

    # docker

    def _docker_status(self, args: argparse.Namespace, logger: CliLogger) -> int:
        logger.info(f"Docker Engine: {_require(self.docker).get_status().upper()}")
        return 0

    def _docker_start(self, args: argparse.Namespace, logger: CliLogger) -> int:
        return 0 if _require(self.docker).start_desktop() else 1

    # db

    def _configure_db(self, parser: argparse.ArgumentParser) -> None:
        if self.mysql is not None:
            targets = list(self.db_targets)
            parser.add_argument(
                "--source", choices=["cloudsql", "local", "file"], default="cloudsql", help="snapshot source (default: cloudsql)"
            )
            parser.add_argument("--input-file", type=Path, help="path to an existing SQL file to anonymize instead of live DB")
            parser.add_argument("--output-file", type=Path, help="path to write the anonymized SQL snapshot file")
            parser.add_argument(
                "--load-target", choices=targets, help=f"automatically load anonymized snapshot into {' or '.join(targets)}"
            )
            parser.add_argument(
                "--confirm-production-access",
                action="store_true",
                help="confirm authorization to snapshot production Cloud SQL",
            )
            parser.add_argument("snapshot_path", nargs="?", type=Path, help="path to the SQL snapshot file to load")
            parser.add_argument(
                "--snapshot-path", dest="snapshot_path_option", type=Path, help="path to the SQL snapshot file to load"
            )
            parser.add_argument("--target", choices=targets, default="local", help="target database (default: local)")
        if self.proxy is not None:
            proxy = self.proxy
            credentials = (
                str(proxy.credentials_file)
                if proxy.credentials_file
                else "user Application Default Credentials from gcloud auth application-default login"
            )
            parser.add_argument("--address", help=f"local bind address (default: {proxy.address})")
            parser.add_argument("--port", type=int, help=f"local proxy port (default: {proxy.port})")
            parser.add_argument("--instance", help=f"cloud SQL instance connection name (default: {proxy.instance})")
            parser.add_argument(
                "--credentials-file", type=Path, help=f"optional credentials file override (default: {credentials})"
            )

    def _db_status(self, args: argparse.Namespace, logger: CliLogger) -> int:
        mysql = _require(self.mysql)
        status = mysql.get_container_status() or ("listening" if is_port_in_use(mysql.port) else "stopped")
        logger.info(f"MySQL ({mysql.container_name}): {status} on port {mysql.port}")
        return 0

    def _db_start(self, args: argparse.Namespace, logger: CliLogger) -> int:
        return 0 if _require(self.mysql).ensure_running() else 1

    def _db_stop(self, args: argparse.Namespace, logger: CliLogger) -> int:
        return 0 if _require(self.mysql).stop() else 1

    def _db_snapshot(self, args: argparse.Namespace, logger: CliLogger) -> int:
        snapshot = _require(self.mysql).snapshot_and_anonymize(
            source=args.source,
            input_file=args.input_file,
            output_file=args.output_file,
            load_target=args.load_target,
            confirm_production=args.confirm_production_access,
        )
        return 0 if snapshot else 1

    def _db_load_snapshot(self, args: argparse.Namespace, logger: CliLogger) -> int:
        path = args.snapshot_path or args.snapshot_path_option
        if path is None:
            logger.error("Missing the snapshot path: pass it after load-snapshot or with --snapshot-path.")
            return 2
        return 0 if _require(self.mysql).load_snapshot(path, target=args.target) else 1

    def _db_proxy(self, args: argparse.Namespace, logger: CliLogger) -> int:
        proxy = _require(self.proxy)
        for option in ("address", "port", "instance", "credentials_file"):
            value = getattr(args, option)
            if value is not None:
                setattr(proxy, option, value)
        return proxy.start()

    # server

    def _configure_server(self, parser: argparse.ArgumentParser) -> None:
        parser.add_argument("--background", "-d", action="store_true", help="run server in the background and exit immediately")
        parser.add_argument(
            "--build",
            "--force-build",
            dest="build",
            action="store_true",
            help="force rebuild of server distribution package before starting",
        )
        parser.add_argument("--memory-db", action="store_true", help="use in-memory database instead of MySQL")
        if self.verifier is not None:
            parser.add_argument("--verify", action="store_true", help="run automated verification checks after starting server")
        if self.testdb_env_file is not None:
            parser.add_argument(
                "--testdb",
                action="store_true",
                help=f"run server against the Cloud SQL test database via {self.testdb_env_file.name}",
            )

    def _server_status(self, args: argparse.Namespace, logger: CliLogger) -> int:
        server = _require(self.server)
        pid = server.get_running_pid()
        healthy, data = server.poll_health_status(timeout_seconds=2.0)
        if healthy:
            extra = data.get("extraInfo")
            uptime = extra.get("uptime", "unknown") if isinstance(extra, dict) else "unknown"
            logger.info(
                f"Server: RUNNING (PID: {pid or 'unknown'}, port: {server.port}, version: {data.get('version')}, uptime: {uptime})"
            )
        else:
            logger.info(f"Server: STOPPED (port: {server.port})")
        return 0

    def _server_start(self, args: argparse.Namespace, logger: CliLogger) -> int:
        verify = getattr(args, "verify", False)
        server = _require(self.server)
        if getattr(args, "testdb", False):
            env_file = _require(self.testdb_env_file)
            if not env_file.is_file():
                logger.error(f"Test database environment file not found: {env_file}")
                return 1
            server.env_file = env_file
            logger.info(f"Using the Cloud SQL test database via {env_file.name} (--testdb enabled)")
        elif args.memory_db:
            logger.info("Using in-memory database (--memory-db enabled)")
        elif self.mysql is not None and not self.mysql.ensure_running():
            logger.error("Failed to ensure MySQL container is running. (Tip: pass --memory-db to run with in-memory storage)")
            return 1
        started = server.start(background=args.background or verify, force_build=args.build, memory_db=args.memory_db)
        if not started:
            return 1
        if verify and not _require(self.verifier).run_all_checks():
            return 1
        return 0

    def _server_stop(self, args: argparse.Namespace, logger: CliLogger) -> int:
        return 0 if _require(self.server).stop() else 1

    # mail

    def _mail_test_emails(self, args: argparse.Namespace, logger: CliLogger) -> int:
        recipient = args.to or args.recipient
        if not recipient:
            logger.error("Missing the recipient email address: pass it after test-emails or with --to.")
            return 2
        sent = _require(self.mail).test_emails(
            recipient=recipient, env_file=args.env_file, app_name=args.app_name, force_build=args.build
        )
        return 0 if sent else 1

    # client

    def _configure_client(self, parser: argparse.ArgumentParser) -> None:
        url_help = f"(default: {self.service_url})" if self.service_url else "(required for verify-deployment)"
        parser.add_argument("--url", default=self.service_url, help=f"base service URL to check {url_help}")
        parser.add_argument("--expected-version", help="if given, fail unless live version matches exactly")
        parser.add_argument("--attempts", type=int, default=5, help="retry attempts before failing (default: 5)")
        parser.add_argument("--retry-delay", type=float, default=3.0, help="seconds between retries (default: 3.0)")
        parser.add_argument("--timeout", type=float, default=10.0, help="per-request timeout in seconds (default: 10.0)")

    def _client_verify(self, args: argparse.Namespace, logger: CliLogger) -> int:
        return 0 if _require(self.verifier).run_all_checks() else 1

    def _client_verify_deployment(self, args: argparse.Namespace, logger: CliLogger) -> int:
        if not args.url:
            logger.error("Missing the service URL: pass --url.")
            return 2
        verified = _require(self.verifier).verify_deployment(
            url=args.url,
            expected_version=args.expected_version,
            attempts=args.attempts,
            retry_delay=args.retry_delay,
            timeout=args.timeout,
        )
        return 0 if verified else 1


def _configure_mail(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("recipient", nargs="?", help="destination email address to send test emails to")
    parser.add_argument("--to", help="destination email address to send test emails to")
    parser.add_argument("--app-name", help="application name for mail formats test (default: the server's app name)")
    parser.add_argument("--env-file", type=Path, help="application environment file (default: the server's env file)")
    parser.add_argument(
        "--build",
        "--force-build",
        dest="build",
        action="store_true",
        help="force rebuild of server distribution package before sending",
    )


def _require(manager: Optional[Any]) -> Any:
    """Return ``manager``; the groups register a sub-action only when its manager is supplied."""
    assert manager is not None
    return manager


__all__ = ["ServiceActions", "SubAction", "SubActionHandler"]
