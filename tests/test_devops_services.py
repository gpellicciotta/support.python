from __future__ import annotations

import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Any
from unittest import mock

from support_python.devops.services import LocalMailManager, LocalMySqlManager, LocalServerManager, LocalVerifier
from support_python.httpd import EmbeddedStaticServer, StaticServerManager

SERVICES = "support_python.devops.services"


def start_command(manager: LocalServerManager, **start_kwargs: Any) -> tuple[list[str], dict[str, str]]:
    """Run ``manager.start`` in the background with every side effect faked; return the command and environment."""
    with (
        mock.patch(f"{SERVICES}.is_port_in_use", return_value=False),
        mock.patch.object(manager, "is_java_available", return_value=True),
        mock.patch.object(manager, "build_server_if_needed", return_value=True),
        mock.patch.object(manager, "poll_health_status", return_value=(True, {})),
        mock.patch(f"{SERVICES}.subprocess.Popen") as popen,
    ):
        popen.return_value.pid = 4242
        manager.start(background=True, **start_kwargs)
    return popen.call_args.args[0], popen.call_args.kwargs["env"]


class ServerManagerOptionTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.env_file = self.root / "dev.env"
        self.env_file.write_text("A=1\n", encoding="utf-8")
        (self.root / "logs").mkdir()

    def manager(self, **kwargs: Any) -> LocalServerManager:
        return LocalServerManager(
            logger=mock.Mock(),
            env_file=self.env_file,
            server_jar=self.root / "server.jar",
            config_file=self.root / "app.conf",
            log_file=self.root / "logs" / "app.log",
            app_static_dir=self.root / "static",
            app_name="Todos",
            **kwargs,
        )

    def test_defaults_build_the_support_java_command(self) -> None:
        cmd, env = start_command(self.manager(), memory_db=True)
        self.assertEqual(
            cmd,
            [
                "java",
                f"-Denvironment-properties-file={self.env_file}",
                "-jar",
                str(self.root / "server.jar"),
                f"--config-file={self.root / 'app.conf'}",
                "--mail.back-end-type=com.pellicciotta.support.mail.DummyBackEnd",
                f"--logging.file-path={self.root / 'logs' / 'app.log'}",
                "--db.jdbc-url=memory",
                "start",
            ],
        )
        self.assertEqual(env["TODOS_STATIC_DIR"], str(self.root / "static"))

    def test_every_override_replaces_its_argument(self) -> None:
        manager = self.manager(
            environment_file_option="-Dapp.properties",
            config_file_option="--cfg",
            log_file_option="--log",
            mail_backend_args=["--mail=null"],
            memory_db_args=["--db=mem", "--fast"],
            start_args=["serve", "--now"],
            static_dir_env_var="WEB_ROOT",
        )
        cmd, env = start_command(manager, memory_db=True)
        self.assertEqual(
            cmd,
            [
                "java",
                f"-Dapp.properties={self.env_file}",
                "-jar",
                str(self.root / "server.jar"),
                f"--cfg={self.root / 'app.conf'}",
                "--mail=null",
                f"--log={self.root / 'logs' / 'app.log'}",
                "--db=mem",
                "--fast",
                "serve",
                "--now",
            ],
        )
        self.assertEqual(env["WEB_ROOT"], str(self.root / "static"))
        self.assertNotIn("TODOS_STATIC_DIR", env)

    def test_none_options_and_empty_args_drop_their_arguments(self) -> None:
        manager = self.manager(environment_file_option=None, config_file_option=None, log_file_option=None, mail_backend_args=())
        cmd, _ = start_command(manager)
        self.assertEqual(cmd, ["java", "-jar", str(self.root / "server.jar"), "start"])


class MailManagerOptionTests(unittest.TestCase):
    def run_test_emails(self, mail_kwargs: Any = None, **server_kwargs: Any) -> list[str]:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "dev.env").write_text("A=1\n", encoding="utf-8")
            server = LocalServerManager(
                logger=mock.Mock(),
                env_file=root / "dev.env",
                server_jar=root / "s.jar",
                config_file=root / "c.conf",
                app_name="Todos",
                **server_kwargs,
            )
            mail = LocalMailManager(logger=mock.Mock(), server_manager=server, **(mail_kwargs or {}))
            with (
                mock.patch.object(server, "is_java_available", return_value=True),
                mock.patch.object(server, "build_server_if_needed", return_value=True),
                mock.patch(f"{SERVICES}.subprocess.run") as run,
            ):
                run.return_value.returncode = 0
                self.assertTrue(mail.test_emails("me@example.com"))
            self.root = root
            return run.call_args.args[0]

    def test_defaults(self) -> None:
        cmd = self.run_test_emails()
        self.assertEqual(
            cmd,
            [
                "java",
                f"-Denvironment-properties-file={self.root / 'dev.env'}",
                "-jar",
                str(self.root / "s.jar"),
                f"--config-file={self.root / 'c.conf'}",
                "test-mail-formats",
                "me@example.com",
                "Todos",
            ],
        )

    def test_overrides_and_server_manager_options_apply(self) -> None:
        cmd = self.run_test_emails(
            {"test_mail_args": ["mail", "--check"]}, environment_file_option="-Dapp.properties", config_file_option="--cfg"
        )
        self.assertEqual(cmd[1], f"-Dapp.properties={self.root / 'dev.env'}")
        self.assertEqual(cmd[4], f"--cfg={self.root / 'c.conf'}")
        self.assertEqual(cmd[5:], ["mail", "--check", "me@example.com", "Todos"])


class VerifierOptionTests(unittest.TestCase):
    def test_default_health_endpoint_and_assets(self) -> None:
        verifier = LocalVerifier(logger=mock.Mock(), port=9000)
        self.assertEqual(verifier.health_endpoint, "/api/status")
        self.assertEqual(verifier.running_status, "running")
        self.assertEqual(tuple(verifier.default_assets), ("/css/main.css", "/js/main.mjs"))

    def test_verify_health_status_defaults_to_the_configured_endpoint(self) -> None:
        verifier = LocalVerifier(logger=mock.Mock(), port=9000, health_endpoint="/health")
        with mock.patch(f"{SERVICES}.urllib.request.urlopen", side_effect=OSError("down")) as urlopen:
            verifier.verify_health_status()
            verifier.verify_health_status("/other")
        self.assertEqual(
            [call.args[0].full_url for call in urlopen.call_args_list],
            ["http://localhost:9000/health", "http://localhost:9000/other"],
        )

    def test_default_assets_are_the_asset_check_default(self) -> None:
        verifier = LocalVerifier(logger=mock.Mock(), port=9000, default_assets=["/app.css"])
        with mock.patch(f"{SERVICES}.urllib.request.urlopen", side_effect=OSError("down")) as urlopen:
            verifier.verify_static_assets()
        self.assertEqual(urlopen.call_args_list[0].args[0], "http://localhost:9000/app.css")


class MySqlEnvFileNameTests(unittest.TestCase):
    def manager(self, **kwargs: Any) -> LocalMySqlManager:
        return LocalMySqlManager(logger=mock.Mock(), docker_mgr=mock.Mock(), db_name="todos", **kwargs)

    def test_default_names(self) -> None:
        manager = self.manager()
        self.assertEqual(manager.render_env_file_name(manager.test_env_file_name), "todos-testdb-devserver.env")
        self.assertEqual(manager.render_env_file_name(manager.prod_env_file_name, app="todos"), "todos-proddb-cloudrun.env")

    def test_custom_names_accept_both_placeholder_spellings(self) -> None:
        manager = self.manager(test_env_file_name="{{db_name}}-test.env", prod_env_file_name="{{app}}-{{db-name}}-prod.env")
        self.assertEqual(manager.render_env_file_name(manager.test_env_file_name), "todos-test.env")
        self.assertEqual(manager.render_env_file_name(manager.prod_env_file_name, app="shop"), "shop-todos-prod.env")
        dashed = self.manager(test_env_file_name="{{db-name}}-test.env")
        self.assertEqual(dashed.render_env_file_name(dashed.test_env_file_name), "todos-test.env")


class CustomHealthEndpointIntegrationTests(unittest.TestCase):
    def test_verify_deployment_against_a_custom_health_path(self) -> None:
        def mock_api(path: str, query: str, handler: EmbeddedStaticServer) -> bool:
            if path == "/healthz":
                handler.send_json_response({"status": "ok", "version": "1.2.3"})
                return True
            return False

        with StaticServerManager(mock_api_handler=mock_api, port=0) as server:
            url = f"http://127.0.0.1:{server.port}"
            custom = LocalVerifier(logger=mock.Mock(), health_endpoint="/healthz", running_status="ok")
            self.assertTrue(custom.verify_deployment(url, "1.2.3", attempts=1, retry_delay=0.0))
            self.assertFalse(LocalVerifier(logger=mock.Mock()).verify_deployment(url, "1.2.3", attempts=1, retry_delay=0.0))


if __name__ == "__main__":
    unittest.main()
