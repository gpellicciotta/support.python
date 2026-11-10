from __future__ import annotations

import io
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Any
from unittest import mock

from support_python.devops.cli import DevopsCli
from support_python.devops.projects import PythonProject
from support_python.logging import CliLogger
from support_python.devops.services import (
    CloudSqlProxyManager,
    LocalDockerManager,
    LocalMailManager,
    LocalMySqlManager,
    LocalServerManager,
    LocalVerifier,
)

PYPROJECT = '[project]\nname = "demo"\nversion = "1.2.0-pre"\n'


def run_cli(cli: DevopsCli, *argv: str) -> tuple[int, str]:
    out = io.StringIO()
    with redirect_stdout(out), redirect_stderr(out):
        code = cli.run(list(argv))
    return code, out.getvalue()


def make_managers() -> dict[str, Any]:
    docker = mock.create_autospec(LocalDockerManager, instance=True)
    docker.get_status.return_value = "running"
    docker.start_desktop.return_value = True
    mysql = mock.create_autospec(LocalMySqlManager, instance=True)
    mysql.container_name, mysql.port = "demo-mysql", 3307
    mysql.get_container_status.return_value = "running"
    mysql.ensure_running.return_value = True
    mysql.stop.return_value = True
    mysql.snapshot_and_anonymize.return_value = Path("snapshot.sql")
    mysql.load_snapshot.return_value = True
    proxy = mock.create_autospec(CloudSqlProxyManager, instance=True)
    proxy.instance, proxy.address, proxy.port, proxy.credentials_file = "p:r:i", "0.0.0.0", 3606, None
    proxy.start.return_value = 0
    server = mock.create_autospec(LocalServerManager, instance=True)
    server.port = 8080
    server.get_running_pid.return_value = 4242
    server.poll_health_status.return_value = (True, {"version": "1.2.0", "extraInfo": {"uptime": "5s"}})
    server.start.return_value = True
    server.stop.return_value = True
    mail = mock.create_autospec(LocalMailManager, instance=True)
    mail.test_emails.return_value = True
    verifier = mock.create_autospec(LocalVerifier, instance=True)
    verifier.run_all_checks.return_value = True
    verifier.verify_deployment.return_value = True
    return {"docker": docker, "mysql": mysql, "proxy": proxy, "server": server, "mail": mail, "verifier": verifier}


class ServiceActionsTestCase(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = TemporaryDirectory()
        self.root = Path(self._tmp.name)
        (self.root / "pyproject.toml").write_text(PYPROJECT, encoding="utf-8")
        self.m = make_managers()

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def cli(self, **overrides: Any) -> DevopsCli:
        cli = DevopsCli(PythonProject(self.root))
        cli.add_services(**{**self.m, **overrides})
        return cli


class DockerGroupTests(ServiceActionsTestCase):
    def test_status_logs_the_engine_status(self) -> None:
        code, out = run_cli(self.cli(), "docker", "status")
        self.assertEqual(code, 0)
        self.assertIn("Docker Engine: RUNNING", out)
        self.m["docker"].start_desktop.assert_not_called()

    def test_status_is_the_default_sub_action(self) -> None:
        code, out = run_cli(self.cli(), "docker")
        self.assertEqual(code, 0)
        self.m["docker"].get_status.assert_called_once_with()

    def test_start_launches_docker_desktop(self) -> None:
        self.assertEqual(run_cli(self.cli(), "docker", "start")[0], 0)
        self.m["docker"].start_desktop.assert_called_once_with()

    def test_start_failure_exits_1(self) -> None:
        self.m["docker"].start_desktop.return_value = False
        self.assertEqual(run_cli(self.cli(), "docker", "start")[0], 1)

    def test_handlers_use_the_run_logger(self) -> None:
        run_cli(self.cli(), "docker", "status")
        self.assertIsInstance(self.m["docker"].logger, CliLogger)


class DbGroupTests(ServiceActionsTestCase):
    def test_status_logs_container_and_port(self) -> None:
        code, out = run_cli(self.cli(), "db", "status")
        self.assertEqual(code, 0)
        self.assertIn("MySQL (demo-mysql): running on port 3307", out)

    def test_status_falls_back_to_the_port_probe(self) -> None:
        self.m["mysql"].get_container_status.return_value = None
        with mock.patch("support_python.devops.service_actions.is_port_in_use", return_value=False) as probe:
            code, out = run_cli(self.cli(), "db")
        self.assertEqual(code, 0)
        probe.assert_called_once_with(3307)
        self.assertIn("MySQL (demo-mysql): stopped on port 3307", out)

    def test_start_and_stop(self) -> None:
        self.assertEqual(run_cli(self.cli(), "db", "start")[0], 0)
        self.m["mysql"].ensure_running.assert_called_once_with()
        self.m["mysql"].stop.return_value = False
        self.assertEqual(run_cli(self.cli(), "db", "stop")[0], 1)
        self.m["mysql"].stop.assert_called_once_with()

    def test_snapshot_defaults(self) -> None:
        self.assertEqual(run_cli(self.cli(), "db", "snapshot")[0], 0)
        self.m["mysql"].snapshot_and_anonymize.assert_called_once_with(
            source="cloudsql",
            input_file=None,
            output_file=None,
            load_target=None,
            confirm_production=False,
            custom_password=None,
        )

    def test_snapshot_passes_every_option(self) -> None:
        argv = ["db", "snapshot", "--source", "file", "--input-file", "in.sql", "--output-file", "out.sql"]
        argv += ["--load-target", "testdb", "--confirm-production-access", "--custom-password", "pw"]
        self.assertEqual(run_cli(self.cli(), *argv)[0], 0)
        self.m["mysql"].snapshot_and_anonymize.assert_called_once_with(
            source="file",
            input_file=Path("in.sql"),
            output_file=Path("out.sql"),
            load_target="testdb",
            confirm_production=True,
            custom_password="pw",
        )

    def test_snapshot_failure_exits_1(self) -> None:
        self.m["mysql"].snapshot_and_anonymize.return_value = None
        self.assertEqual(run_cli(self.cli(), "db", "snapshot")[0], 1)

    def test_load_target_choices_come_from_db_targets(self) -> None:
        cli = self.cli(db_targets=("local", "testdb", "todos_test"))
        self.assertEqual(run_cli(cli, "db", "snapshot", "--load-target", "todos_test")[0], 0)
        self.assertEqual(run_cli(cli, "db", "snapshot", "--load-target", "other")[0], 2)
        self.assertEqual(run_cli(self.cli(), "db", "snapshot", "--load-target", "todos_test")[0], 2)

    def test_load_snapshot_takes_a_positional_path(self) -> None:
        self.assertEqual(run_cli(self.cli(), "db", "load-snapshot", "dump.sql")[0], 0)
        self.m["mysql"].load_snapshot.assert_called_once_with(Path("dump.sql"), target="local")

    def test_load_snapshot_takes_the_snapshot_path_option_and_target(self) -> None:
        cli = self.cli(db_targets=("local", "testdb", "counters_test"))
        code, _ = run_cli(cli, "db", "load-snapshot", "--snapshot-path", "dump.sql", "--target", "counters_test")
        self.assertEqual(code, 0)
        self.m["mysql"].load_snapshot.assert_called_once_with(Path("dump.sql"), target="counters_test")

    def test_load_snapshot_without_a_path_exits_2(self) -> None:
        code, out = run_cli(self.cli(), "db", "load-snapshot")
        self.assertEqual(code, 2)
        self.assertIn("snapshot path", out)
        self.m["mysql"].load_snapshot.assert_not_called()

    def test_load_snapshot_failure_exits_1(self) -> None:
        self.m["mysql"].load_snapshot.return_value = False
        self.assertEqual(run_cli(self.cli(), "db", "load-snapshot", "dump.sql")[0], 1)

    def test_a_snapshot_path_on_another_sub_action_exits_2(self) -> None:
        for sub_action in ("snapshot", "status"):
            with self.subTest(sub_action=sub_action):
                code, out = run_cli(self.cli(), "db", sub_action, "stray.sql")
                self.assertEqual(code, 2)
                self.assertIn("stray.sql", out)
        self.m["mysql"].snapshot_and_anonymize.assert_not_called()
        self.m["mysql"].get_container_status.assert_not_called()

    def test_unsupported_db_targets_are_rejected_at_registration(self) -> None:
        for targets in (("local", "staging"), ("prod",)):
            with self.subTest(targets=targets):
                with self.assertRaisesRegex(ValueError, "staging|prod"):
                    self.cli(db_targets=targets)

    def test_test_database_aliases_are_valid_targets(self) -> None:
        for target in ("local", "testdb", "todos_test", "COUNTERS_TEST"):
            self.assertTrue(LocalMySqlManager.is_valid_target(target), target)
        for target in ("staging", "_test", "test", ""):
            self.assertFalse(LocalMySqlManager.is_valid_target(target), target)

    def test_proxy_uses_the_manager_defaults(self) -> None:
        self.assertEqual(run_cli(self.cli(), "db", "proxy")[0], 0)
        proxy = self.m["proxy"]
        proxy.start.assert_called_once_with()
        self.assertEqual((proxy.instance, proxy.address, proxy.port, proxy.credentials_file), ("p:r:i", "0.0.0.0", 3606, None))

    def test_proxy_options_override_the_manager(self) -> None:
        argv = ["db", "proxy", "--address", "127.0.0.1", "--port", "3700", "--instance", "a:b:c"]
        argv += ["--credentials-file", "key.json"]
        self.m["proxy"].start.return_value = 1
        self.assertEqual(run_cli(self.cli(), *argv)[0], 1)
        proxy = self.m["proxy"]
        self.assertEqual((proxy.instance, proxy.address, proxy.port), ("a:b:c", "127.0.0.1", 3700))
        self.assertEqual(proxy.credentials_file, Path("key.json"))

    def test_proxy_only_group_offers_only_proxy(self) -> None:
        cli = self.cli(mysql=None)
        self.assertEqual(run_cli(cli, "db", "status")[0], 2)
        self.assertEqual(run_cli(cli, "db")[0], 2)
        self.assertEqual(run_cli(cli, "db", "proxy")[0], 0)

    def test_mysql_only_group_has_no_proxy(self) -> None:
        cli = self.cli(proxy=None)
        self.assertEqual(run_cli(cli, "db", "proxy")[0], 2)
        self.assertEqual(run_cli(cli, "db", "status")[0], 0)


class ServerGroupTests(ServiceActionsTestCase):
    def test_status_reports_a_running_server(self) -> None:
        code, out = run_cli(self.cli(), "server", "status")
        self.assertEqual(code, 0)
        self.m["server"].poll_health_status.assert_called_once_with(timeout_seconds=2.0)
        self.assertIn("Server: RUNNING (PID: 4242, port: 8080, version: 1.2.0, uptime: 5s)", out)

    def test_status_reports_a_stopped_server(self) -> None:
        self.m["server"].poll_health_status.return_value = (False, {})
        code, out = run_cli(self.cli(), "server")
        self.assertEqual(code, 0)
        self.assertIn("Server: STOPPED (port: 8080)", out)

    def test_start_ensures_mysql_then_starts_in_the_foreground(self) -> None:
        self.assertEqual(run_cli(self.cli(), "server", "start")[0], 0)
        self.m["mysql"].ensure_running.assert_called_once_with()
        self.m["server"].start.assert_called_once_with(background=False, force_build=False, memory_db=False)
        self.m["verifier"].run_all_checks.assert_not_called()

    def test_start_exits_1_when_mysql_does_not_start(self) -> None:
        self.m["mysql"].ensure_running.return_value = False
        code, out = run_cli(self.cli(), "server", "start")
        self.assertEqual(code, 1)
        self.assertIn("--memory-db", out)
        self.m["server"].start.assert_not_called()

    def test_start_options(self) -> None:
        self.assertEqual(run_cli(self.cli(), "server", "start", "-d", "--build", "--memory-db")[0], 0)
        self.m["mysql"].ensure_running.assert_not_called()
        self.m["server"].start.assert_called_once_with(background=True, force_build=True, memory_db=True)

    def test_start_accepts_force_build_and_background(self) -> None:
        self.assertEqual(run_cli(self.cli(mysql=None), "server", "start", "--background", "--force-build")[0], 0)
        self.m["server"].start.assert_called_once_with(background=True, force_build=True, memory_db=False)

    def test_start_verify_runs_in_the_background_and_checks(self) -> None:
        self.m["verifier"].run_all_checks.return_value = False
        self.assertEqual(run_cli(self.cli(), "server", "start", "--verify")[0], 1)
        self.m["server"].start.assert_called_once_with(background=True, force_build=False, memory_db=False)
        self.m["verifier"].run_all_checks.assert_called_once_with()

    def test_start_failure_exits_1(self) -> None:
        self.m["server"].start.return_value = False
        self.assertEqual(run_cli(self.cli(), "server", "start", "--verify")[0], 1)
        self.m["verifier"].run_all_checks.assert_not_called()

    def test_start_testdb_uses_the_test_database_env_file_without_mysql(self) -> None:
        env_file = self.root / "demo-testdb.env"
        env_file.write_text("DB_USER=demo_test\n", encoding="utf-8")
        self.assertEqual(run_cli(self.cli(testdb_env_file=env_file), "server", "start", "--testdb")[0], 0)
        self.assertEqual(self.m["server"].env_file, env_file)
        self.m["mysql"].ensure_running.assert_not_called()
        self.m["server"].start.assert_called_once_with(background=False, force_build=False, memory_db=False)

    def test_start_testdb_exits_1_when_the_env_file_is_missing(self) -> None:
        code, out = run_cli(self.cli(testdb_env_file=self.root / "missing.env"), "server", "start", "--testdb")
        self.assertEqual(code, 1)
        self.assertIn("missing.env", out)
        self.m["server"].start.assert_not_called()

    def test_testdb_option_needs_a_testdb_env_file(self) -> None:
        self.assertEqual(run_cli(self.cli(), "server", "start", "--testdb")[0], 2)

    def test_verify_option_needs_a_verifier(self) -> None:
        self.assertEqual(run_cli(self.cli(verifier=None), "server", "start", "--verify")[0], 2)

    def test_stop(self) -> None:
        self.assertEqual(run_cli(self.cli(), "server", "stop")[0], 0)
        self.m["server"].stop.assert_called_once_with()
        self.m["server"].stop.return_value = False
        self.assertEqual(run_cli(self.cli(), "server", "stop")[0], 1)


class MailGroupTests(ServiceActionsTestCase):
    def test_test_emails_takes_a_positional_recipient(self) -> None:
        self.assertEqual(run_cli(self.cli(), "mail", "test-emails", "me@example.com")[0], 0)
        self.m["mail"].test_emails.assert_called_once_with(
            recipient="me@example.com", env_file=None, app_name=None, force_build=False
        )

    def test_test_emails_options(self) -> None:
        argv = ["mail", "test-emails", "--to", "me@example.com", "--app-name", "Todos", "--env-file", "app.env", "--build"]
        self.assertEqual(run_cli(self.cli(), *argv)[0], 0)
        self.m["mail"].test_emails.assert_called_once_with(
            recipient="me@example.com", env_file=Path("app.env"), app_name="Todos", force_build=True
        )

    def test_test_emails_is_the_default_sub_action(self) -> None:
        self.assertEqual(run_cli(self.cli(), "mail", "--to", "me@example.com")[0], 0)
        self.m["mail"].test_emails.assert_called_once()

    def test_missing_recipient_exits_2(self) -> None:
        code, out = run_cli(self.cli(), "mail", "test-emails")
        self.assertEqual(code, 2)
        self.assertIn("recipient", out)
        self.m["mail"].test_emails.assert_not_called()

    def test_failure_exits_1(self) -> None:
        self.m["mail"].test_emails.return_value = False
        self.assertEqual(run_cli(self.cli(), "mail", "test-emails", "me@example.com")[0], 1)


class ClientGroupTests(ServiceActionsTestCase):
    def test_verify_runs_all_checks(self) -> None:
        self.assertEqual(run_cli(self.cli(), "client", "verify")[0], 0)
        self.m["verifier"].run_all_checks.assert_called_once_with()
        self.m["verifier"].run_all_checks.return_value = False
        self.assertEqual(run_cli(self.cli(), "client")[0], 1)

    def test_verify_deployment_defaults(self) -> None:
        cli = self.cli(service_url="https://demo.example.com")
        self.assertEqual(run_cli(cli, "client", "verify-deployment")[0], 0)
        self.m["verifier"].verify_deployment.assert_called_once_with(
            url="https://demo.example.com", expected_version=None, attempts=5, retry_delay=3.0, timeout=10.0
        )

    def test_verify_deployment_options(self) -> None:
        argv = ["client", "verify-deployment", "--url", "https://x.example.com", "--expected-version", "1.2.0"]
        argv += ["--attempts", "2", "--retry-delay", "0.5", "--timeout", "4"]
        self.m["verifier"].verify_deployment.return_value = False
        self.assertEqual(run_cli(self.cli(), *argv)[0], 1)
        self.m["verifier"].verify_deployment.assert_called_once_with(
            url="https://x.example.com", expected_version="1.2.0", attempts=2, retry_delay=0.5, timeout=4.0
        )

    def test_verify_deployment_without_a_url_exits_2(self) -> None:
        code, out = run_cli(self.cli(), "client", "verify-deployment")
        self.assertEqual(code, 2)
        self.assertIn("--url", out)
        self.m["verifier"].verify_deployment.assert_not_called()


class RegistrationTests(ServiceActionsTestCase):
    def test_groups_are_absent_without_their_manager(self) -> None:
        cli = DevopsCli(PythonProject(self.root))
        cli.add_services(docker=self.m["docker"])
        for group in ("db", "server", "mail", "client"):
            with self.subTest(group=group):
                self.assertEqual(run_cli(cli, group, "status")[0], 2)
        self.assertEqual(run_cli(cli, "docker", "status")[0], 0)

    def test_no_managers_adds_no_actions(self) -> None:
        cli = DevopsCli(PythonProject(self.root))
        cli.add_services()
        _, out = run_cli(cli, "help")
        for group in ("docker", "db", "server", "mail", "client"):
            self.assertNotIn(f"devops {group} ", out)

    def test_unknown_sub_action_exits_2(self) -> None:
        cli = self.cli()
        for group in ("docker", "db", "server", "mail", "client"):
            with self.subTest(group=group):
                code, out = run_cli(cli, group, "bogus")
                self.assertEqual(code, 2)
                self.assertIn("invalid choice", out)

    def test_help_lists_the_groups_and_sub_actions(self) -> None:
        _, out = run_cli(self.cli(), "help")
        self.assertIn("devops docker {status|start}", out)
        self.assertIn("devops db {status|start|stop|snapshot|load-snapshot|proxy}", out)
        self.assertIn("devops server {status|start|stop}", out)
        self.assertIn("devops mail {test-emails}", out)
        self.assertIn("devops client {verify|verify-deployment}", out)

    def test_group_help_lists_the_options(self) -> None:
        _, out = run_cli(self.cli(), "help", "db")
        for option in ("load-snapshot", "--source", "--load-target", "--snapshot-path", "--target", "--instance"):
            self.assertIn(option, out)


class LocalVerifierRunAllChecksTests(unittest.TestCase):
    def verifier(self, *, port_open: bool = True, results: tuple[bool, bool, bool] = (True, True, True)) -> LocalVerifier:
        verifier = LocalVerifier(logger=mock.Mock(), port=8123)
        verifier.verify_health_status = mock.Mock(return_value=results[0])  # type: ignore[method-assign]
        verifier.verify_static_index = mock.Mock(return_value=results[1])  # type: ignore[method-assign]
        verifier.verify_static_assets = mock.Mock(return_value=results[2])  # type: ignore[method-assign]
        self._probe = mock.patch("support_python.devops.services.is_port_in_use", return_value=port_open)
        self._probe.start()
        self.addCleanup(self._probe.stop)
        return verifier

    def test_runs_every_check(self) -> None:
        verifier = self.verifier(results=(True, False, True))
        self.assertFalse(verifier.run_all_checks())
        verifier.verify_health_status.assert_called_once_with()
        verifier.verify_static_index.assert_called_once_with()
        verifier.verify_static_assets.assert_called_once_with()

    def test_passes_when_every_check_passes(self) -> None:
        self.assertTrue(self.verifier().run_all_checks())

    def test_fails_fast_when_nothing_listens(self) -> None:
        verifier = self.verifier(port_open=False)
        self.assertFalse(verifier.run_all_checks())
        verifier.verify_health_status.assert_not_called()


class LocalVerifierDeploymentTimeoutTests(unittest.TestCase):
    def test_verify_deployment_passes_the_timeout_to_each_request(self) -> None:
        verifier = LocalVerifier(logger=mock.Mock())
        with mock.patch("support_python.devops.services.urllib.request.urlopen", side_effect=OSError("down")) as urlopen:
            self.assertFalse(verifier.verify_deployment("https://x.example.com", attempts=2, retry_delay=0.0, timeout=7.5))
        self.assertEqual([call.kwargs["timeout"] for call in urlopen.call_args_list], [7.5, 7.5])


class RealMySqlLoadSnapshotTests(unittest.TestCase):
    """Runs ``db load-snapshot`` through a real :class:`LocalMySqlManager`, faking only the proxy probe and docker."""

    def setUp(self) -> None:
        self._tmp = TemporaryDirectory()
        self.root = Path(self._tmp.name)
        (self.root / "pyproject.toml").write_text(PYPROJECT, encoding="utf-8")
        self.snapshot = self.root / "s.sql"
        self.snapshot.write_text("SELECT 1;\n", encoding="utf-8")

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def load(self, db_name: str, target: str, jdbc_database: str) -> tuple[int, str, list[list[str]]]:
        env = f"DB_USER={jdbc_database}\nDB_PASSWORD=pw\nDB_JDBC_URL=jdbc:mysql://127.0.0.1:3606/{jdbc_database}\n"
        (self.root / f"{db_name}-testdb-devserver.env").write_text(env, encoding="utf-8")
        cli = DevopsCli(PythonProject(self.root))
        cli.add_services(mysql=LocalMySqlManager(db_name=db_name, env_dir=self.root), db_targets=("local", "testdb", target))
        with (
            mock.patch("support_python.devops.services.is_port_in_use", return_value=True),
            mock.patch("support_python.devops.services.subprocess.run") as run,
        ):
            run.return_value = mock.Mock(returncode=0, stderr=b"")
            code, out = run_cli(cli, "db", "load-snapshot", str(self.snapshot), "--target", target)
        return code, out, [call.args[0] for call in run.call_args_list if call.args[0][0] == "docker"]

    def test_todos_test_target_loads_into_todos_test(self) -> None:
        code, out, docker = self.load("todos", "todos_test", "todos_test")
        self.assertEqual(code, 0, out)
        self.assertNotIn("Invalid target", out)
        self.assertEqual([command[-1] for command in docker], ["todos_test"])

    def test_alias_target_names_the_test_database(self) -> None:
        code, out, docker = self.load("app", "counters_test", "counters_test")
        self.assertEqual(code, 0, out)
        self.assertEqual([command[-1] for command in docker], ["counters_test"])

    def test_safety_check_still_rejects_a_mismatched_database(self) -> None:
        code, out, docker = self.load("todos", "todos_test", "todos_prod")
        self.assertEqual(code, 1)
        self.assertIn("Target safety validation failed", out)
        self.assertEqual(docker, [])


class DockerStatusIntegrationTests(unittest.TestCase):
    def test_real_docker_status_reports_without_starting_anything(self) -> None:
        with TemporaryDirectory() as tmp:
            Path(tmp, "pyproject.toml").write_text(PYPROJECT, encoding="utf-8")
            cli = DevopsCli(PythonProject(Path(tmp)))
            docker = LocalDockerManager()
            cli.add_services(docker=docker)
            with mock.patch.object(LocalDockerManager, "start_desktop") as start:
                code, out = run_cli(cli, "docker", "status")
        self.assertIn(code, (0, 1))
        self.assertRegex(out, r"Docker Engine: (RUNNING|STOPPED|NOT-INSTALLED)")
        start.assert_not_called()


if __name__ == "__main__":
    unittest.main()
