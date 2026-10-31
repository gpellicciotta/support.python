from __future__ import annotations

import contextlib
import io
import json
import os
import sys
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import MagicMock, patch

from support_python import (
    CliLogger,
    CloudSqlProxyManager,
    LocalDockerManager,
    LocalMailManager,
    LocalMySqlManager,
    LocalServerManager,
    LocalVerifier,
    resolve_cloud_sql_proxy_bin,
    run_step,
)


class RunStepTests(unittest.TestCase):
    def test_returns_true_and_prints_banner_on_success(self) -> None:
        buffer = io.StringIO()
        with contextlib.redirect_stdout(buffer):
            result = run_step("Doing a thing", [sys.executable, "-c", "pass"])
        self.assertTrue(result)
        self.assertIn("Doing a thing", buffer.getvalue())

    def test_returns_false_and_prints_failure_on_nonzero_exit(self) -> None:
        buffer = io.StringIO()
        with contextlib.redirect_stdout(buffer):
            result = run_step("Doing a failing thing", [sys.executable, "-c", "import sys; sys.exit(1)"])
        self.assertFalse(result)
        self.assertIn("[!]", buffer.getvalue())
        self.assertIn("failed (exit code 1)", buffer.getvalue())

    def test_runs_in_given_cwd(self) -> None:
        with TemporaryDirectory() as tmp_dir:
            with patch("support_python.devops.subprocess.run") as mock_run:
                mock_run.return_value = MagicMock(returncode=0)
                run_step("List things", ["some-command"], cwd=tmp_dir)
            self.assertEqual(mock_run.call_args.kwargs["cwd"], tmp_dir)

    def test_logs_progress_and_warning_through_given_logger(self) -> None:
        logger = MagicMock(spec=CliLogger)
        with patch("support_python.devops.subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=1)
            run_step("Doing a thing", ["some-command"], logger=logger)
        logger.progress.assert_called_once_with("Doing a thing")
        logger.warning.assert_called_once()
        self.assertIn("Doing a thing", logger.warning.call_args.args[0])

    def test_does_not_touch_logger_when_none_given(self) -> None:
        buffer = io.StringIO()
        with contextlib.redirect_stdout(buffer):
            result = run_step("Doing a thing", [sys.executable, "-c", "pass"], logger=None)
        self.assertTrue(result)


class ResolveCloudSqlProxyBinTests(unittest.TestCase):
    def test_finds_proxy_on_path(self) -> None:
        with patch("shutil.which", return_value="/usr/local/bin/cloud-sql-proxy"):
            found = resolve_cloud_sql_proxy_bin()
            self.assertEqual(found, "/usr/local/bin/cloud-sql-proxy")

    def test_finds_proxy_in_repo_root(self) -> None:
        with TemporaryDirectory() as tmp_dir:
            root = Path(tmp_dir)
            proxy_exe = root / "cloud-sql-proxy.x64.exe"
            proxy_exe.write_text("", encoding="utf-8")
            with patch("shutil.which", return_value=None):
                found = resolve_cloud_sql_proxy_bin(repo_root=root)
                self.assertEqual(found, str(proxy_exe))

    def test_returns_none_when_not_found(self) -> None:
        with TemporaryDirectory() as tmp_dir:
            with patch("shutil.which", return_value=None):
                found = resolve_cloud_sql_proxy_bin(repo_root=Path(tmp_dir))
                self.assertIsNone(found)


INSTANCE = "example-project:example-region:example-instance"


class CloudSqlProxyManagerTests(unittest.TestCase):
    def test_instance_is_mandatory(self) -> None:
        with self.assertRaises(TypeError):
            CloudSqlProxyManager(logger=MagicMock())  # type: ignore[call-arg]

    def test_instance_is_passed_to_proxy(self) -> None:
        logger = MagicMock()
        with TemporaryDirectory() as tmp_dir:
            creds = Path(tmp_dir) / "key.json"
            creds.write_text("{}", encoding="utf-8")
            mgr = CloudSqlProxyManager(INSTANCE, logger=logger, credentials_file=creds)
            with (
                patch.object(mgr, "resolve_proxy_bin", return_value="/fake/cloud-sql-proxy"),
                patch("subprocess.run", return_value=MagicMock(returncode=0)) as mock_run,
            ):
                mgr.start()
                self.assertIn(INSTANCE, mock_run.call_args[0][0])

    def test_start_with_missing_credentials(self) -> None:
        logger = MagicMock()
        mgr = CloudSqlProxyManager(INSTANCE, logger=logger, credentials_file="/nonexistent/path/key.json")
        res = mgr.start()
        self.assertEqual(res, 1)
        logger.error.assert_called_once()

    def test_start_with_native_binary(self) -> None:
        logger = MagicMock()
        with TemporaryDirectory() as tmp_dir:
            creds = Path(tmp_dir) / "key.json"
            creds.write_text("{}", encoding="utf-8")
            mgr = CloudSqlProxyManager(INSTANCE, logger=logger, port=3606, credentials_file=creds)

            with (
                patch.object(mgr, "resolve_proxy_bin", return_value="/fake/cloud-sql-proxy"),
                patch("subprocess.run", return_value=MagicMock(returncode=0)) as mock_run,
            ):
                code = mgr.start()
                self.assertEqual(code, 0)
                mock_run.assert_called_once()
                cmd = mock_run.call_args[0][0]
                self.assertEqual(cmd[0], "/fake/cloud-sql-proxy")
                self.assertIn("--port", cmd)
                self.assertIn("3606", cmd)

    def test_start_fallback_to_docker(self) -> None:
        logger = MagicMock()
        with TemporaryDirectory() as tmp_dir:
            creds = Path(tmp_dir) / "key.json"
            creds.write_text("{}", encoding="utf-8")
            mgr = CloudSqlProxyManager(INSTANCE, logger=logger, port=3607, credentials_file=creds)

            with (
                patch.object(mgr, "resolve_proxy_bin", return_value=None),
                patch("subprocess.run", return_value=MagicMock(returncode=0)) as mock_run,
            ):
                code = mgr.start()
                self.assertEqual(code, 0)
                cmd = mock_run.call_args[0][0]
                self.assertEqual(cmd[0], "docker")
                self.assertIn("gcr.io/cloud-sql-connectors/cloud-sql-proxy:latest", cmd)


class LocalDockerManagerTests(unittest.TestCase):
    def test_docker_installed_detection(self) -> None:
        mgr = LocalDockerManager()
        with patch("shutil.which", return_value="/usr/bin/docker"):
            self.assertTrue(mgr.is_docker_installed())
        with patch("shutil.which", return_value=None):
            self.assertFalse(mgr.is_docker_installed())

    def test_docker_engine_running(self) -> None:
        mgr = LocalDockerManager()
        with (
            patch.object(mgr, "is_docker_installed", return_value=True),
            patch("subprocess.run", return_value=MagicMock(returncode=0)),
        ):
            self.assertTrue(mgr.is_engine_running())

        with (
            patch.object(mgr, "is_docker_installed", return_value=True),
            patch("subprocess.run", return_value=MagicMock(returncode=1)),
        ):
            self.assertFalse(mgr.is_engine_running())

    def test_get_status(self) -> None:
        mgr = LocalDockerManager()
        with patch.object(mgr, "is_docker_installed", return_value=False):
            self.assertEqual(mgr.get_status(), "not-installed")

        with patch.object(mgr, "is_docker_installed", return_value=True), patch.object(mgr, "is_engine_running", return_value=True):
            self.assertEqual(mgr.get_status(), "running")

        with (
            patch.object(mgr, "is_docker_installed", return_value=True),
            patch.object(mgr, "is_engine_running", return_value=False),
        ):
            self.assertEqual(mgr.get_status(), "stopped")

    def test_start_desktop_already_running(self) -> None:
        mgr = LocalDockerManager()
        with patch.object(mgr, "is_engine_running", return_value=True):
            self.assertTrue(mgr.start_desktop())

    def test_start_desktop_not_found(self) -> None:
        mgr = LocalDockerManager()
        with patch.object(mgr, "is_engine_running", return_value=False), patch("pathlib.Path.exists", return_value=False):
            self.assertFalse(mgr.start_desktop(timeout_seconds=0.1))


class LocalMySqlManagerTests(unittest.TestCase):
    def test_no_default_passwords(self) -> None:
        mgr = LocalMySqlManager()
        self.assertIsNone(mgr.db_password)
        self.assertIsNone(mgr.db_root_password)

    def test_passwords_from_env_file_and_arguments(self) -> None:
        with TemporaryDirectory() as tmp_dir:
            env_path = Path(tmp_dir) / "mysql.env"
            env_path.write_text("MYSQL_PASSWORD=from-env\nMYSQL_ROOT_PASSWORD=root-from-env\n", encoding="utf-8")
            mgr = LocalMySqlManager(mysql_env_file=env_path, db_root_password="root-from-arg")
            self.assertEqual(mgr.db_password, "from-env")
            self.assertEqual(mgr.db_root_password, "root-from-arg")

    def test_missing_passwords_raise_when_needed(self) -> None:
        mgr = LocalMySqlManager()
        with patch("subprocess.run") as mock_run:
            with self.assertRaisesRegex(ValueError, "MYSQL_ROOT_PASSWORD"):
                mgr.wait_for_mysql_ready(timeout_seconds=1.0)
            mock_run.assert_not_called()

    def test_missing_user_password_raises_on_container_creation(self) -> None:
        mgr = LocalMySqlManager(db_root_password="root-secret")
        with (
            patch.object(mgr, "get_container_status", return_value=None),
            patch("subprocess.run") as mock_run,
        ):
            with self.assertRaisesRegex(ValueError, "MYSQL_PASSWORD"):
                mgr.ensure_running()
            mock_run.assert_not_called()

    def test_init_with_env_file(self) -> None:
        with TemporaryDirectory() as tmp_dir:
            env_path = Path(tmp_dir) / "mysql.env"
            env_path.write_text("MYSQL_DATABASE=testdb\nMYSQL_USER=testuser\n", encoding="utf-8")
            mgr = LocalMySqlManager(mysql_env_file=env_path)
            self.assertEqual(mgr.db_name, "testdb")
            self.assertEqual(mgr.db_user, "testuser")

    def test_get_container_status(self) -> None:
        mgr = LocalMySqlManager(db_password="test-user", db_root_password="test-root")
        with patch("subprocess.run", return_value=MagicMock(returncode=0, stdout="running\n")):
            self.assertEqual(mgr.get_container_status(), "running")

    def test_wait_for_mysql_ready_success(self) -> None:
        mgr = LocalMySqlManager(db_password="test-user", db_root_password="test-root")
        with (
            patch("support_python.devops.is_port_in_use", return_value=True),
            patch("subprocess.run", return_value=MagicMock(returncode=0)),
        ):
            self.assertTrue(mgr.wait_for_mysql_ready(timeout_seconds=2.0))

    def test_are_tables_initialized(self) -> None:
        mgr = LocalMySqlManager(db_password="test-user", db_root_password="test-root")
        with patch("subprocess.run", return_value=MagicMock(returncode=0, stdout="users\nposts\n")):
            self.assertTrue(mgr.are_tables_initialized())
        with patch("subprocess.run", return_value=MagicMock(returncode=0, stdout="")):
            self.assertFalse(mgr.are_tables_initialized())

    def test_initialize_schema(self) -> None:
        with TemporaryDirectory() as tmp_dir:
            sql_file = Path(tmp_dir) / "setup.sql"
            sql_file.write_text("CREATE TABLE test (id INT);", encoding="utf-8")
            mgr = LocalMySqlManager(setup_sql_file=sql_file, db_password="test-user", db_root_password="test-root")

            with patch("subprocess.run", return_value=MagicMock(returncode=0)):
                self.assertTrue(mgr.initialize_schema())

            with patch("subprocess.run", return_value=MagicMock(returncode=1, stderr=b"syntax error")):
                self.assertFalse(mgr.initialize_schema())

    def test_stop_container(self) -> None:
        mgr = LocalMySqlManager(db_password="test-user", db_root_password="test-root")
        with (
            patch.object(mgr, "get_container_status", return_value="running"),
            patch("subprocess.run", return_value=MagicMock(returncode=0)),
        ):
            self.assertTrue(mgr.stop())

        with patch.object(mgr, "get_container_status", return_value="stopped"):
            self.assertTrue(mgr.stop())

    def test_load_snapshot_local(self) -> None:
        with TemporaryDirectory() as tmp_dir:
            snap = Path(tmp_dir) / "dump.sql"
            snap.write_text("-- sql dump", encoding="utf-8")
            mgr = LocalMySqlManager(db_password="test-user", db_root_password="test-root")

            with (
                patch.object(mgr, "ensure_running", return_value=True),
                patch("subprocess.run", return_value=MagicMock(returncode=0)),
            ):
                self.assertTrue(mgr.load_snapshot(snap, target="local"))


class LocalServerManagerTests(unittest.TestCase):
    def test_is_java_available(self) -> None:
        mgr = LocalServerManager()
        with patch("shutil.which", return_value="/usr/bin/java"):
            self.assertTrue(mgr.is_java_available())
        with patch("shutil.which", return_value=None):
            self.assertFalse(mgr.is_java_available())

    def test_get_running_pid(self) -> None:
        with TemporaryDirectory() as tmp_dir:
            pid_file = Path(tmp_dir) / "server.pid"
            pid_file.write_text("999999", encoding="utf-8")
            mgr = LocalServerManager(pid_file=pid_file)

            if os.name == "nt":
                with patch("ctypes.windll.kernel32.OpenProcess", return_value=0):
                    self.assertIsNone(mgr.get_running_pid())
            else:
                with patch("os.kill", side_effect=ProcessLookupError):
                    self.assertIsNone(mgr.get_running_pid())

    def test_poll_health_status(self) -> None:
        mgr = LocalServerManager(port=8080)
        fake_data = json.dumps({"status": "running", "version": "1.0.0"}).encode("utf-8")
        fake_resp = MagicMock(status=200)
        fake_resp.read.return_value = fake_data
        fake_resp.__enter__.return_value = fake_resp

        with patch("urllib.request.urlopen", return_value=fake_resp):
            ok, data = mgr.poll_health_status(timeout_seconds=1.0)
            self.assertTrue(ok)
            self.assertEqual(data.get("version"), "1.0.0")

    def test_start_memory_db_mode(self) -> None:
        with TemporaryDirectory() as tmp_dir:
            env_file = Path(tmp_dir) / "app.env"
            env_file.write_text("PORT=8080\n", encoding="utf-8")
            mgr = LocalServerManager(port=8080, env_file=env_file)

            with (
                patch.object(mgr, "is_java_available", return_value=True),
                patch.object(mgr, "build_server_if_needed", return_value=True),
                patch.object(mgr, "poll_health_status", return_value=(True, {"status": "running"})),
                patch("subprocess.Popen") as mock_popen,
                patch("support_python.devops.is_port_in_use", return_value=False),
            ):
                mock_proc = MagicMock(pid=1234)
                mock_popen.return_value = mock_proc
                res = mgr.start(background=True, memory_db=True)
                self.assertTrue(res)
                cmd = mock_popen.call_args[0][0]
                self.assertIn("--db.jdbc-url=memory", cmd)

    def test_stop_server(self) -> None:
        with TemporaryDirectory() as tmp_dir:
            pid_file = Path(tmp_dir) / "server.pid"
            pid_file.write_text("1234", encoding="utf-8")
            mgr = LocalServerManager(port=8080, pid_file=pid_file)

            with (
                patch.object(mgr, "get_running_pid", return_value=1234),
                patch("subprocess.run", return_value=MagicMock(returncode=0)),
                patch("time.sleep"),
            ):
                self.assertTrue(mgr.stop())


class LocalMailManagerTests(unittest.TestCase):
    def test_test_emails_dispatch(self) -> None:
        with TemporaryDirectory() as tmp_dir:
            env_file = Path(tmp_dir) / "mail.env"
            env_file.write_text("MAIL_HOST=smtp.example.com\n", encoding="utf-8")
            srv = LocalServerManager(port=8080, env_file=env_file)
            mail_mgr = LocalMailManager(server_manager=srv)

            with (
                patch.object(srv, "is_java_available", return_value=True),
                patch.object(srv, "build_server_if_needed", return_value=True),
                patch("subprocess.run", return_value=MagicMock(returncode=0)) as mock_run,
            ):
                ok = mail_mgr.test_emails(recipient="user@example.com", env_file=env_file, app_name="Auth")
                self.assertTrue(ok)
                mock_run.assert_called_once()
                cmd = mock_run.call_args[0][0]
                self.assertIn("test-mail-formats", cmd)
                self.assertIn("user@example.com", cmd)
                self.assertIn("Auth", cmd)


class LocalVerifierTests(unittest.TestCase):
    def test_verify_health_status(self) -> None:
        verifier = LocalVerifier(port=8080)
        fake_data = json.dumps({"status": "running", "version": "1.0.0"}).encode("utf-8")
        fake_resp = MagicMock(status=200)
        fake_resp.read.return_value = fake_data
        fake_resp.__enter__.return_value = fake_resp

        with patch("urllib.request.urlopen", return_value=fake_resp):
            self.assertTrue(verifier.verify_health_status())

    def test_verify_static_index(self) -> None:
        verifier = LocalVerifier(port=8080)
        fake_resp = MagicMock(status=200)
        fake_resp.read.return_value = b"<!DOCTYPE html><html><head><title>App</title></head></html>"
        fake_resp.__enter__.return_value = fake_resp

        with patch("urllib.request.urlopen", return_value=fake_resp):
            self.assertTrue(verifier.verify_static_index())

    def test_verify_deployment_success(self) -> None:
        verifier = LocalVerifier()
        fake_resp = MagicMock(status=200)
        fake_resp.read.return_value = b'{"status": "running", "version": "1.2.3"}'
        fake_resp.__enter__.return_value = fake_resp

        with patch("urllib.request.urlopen", return_value=fake_resp):
            self.assertTrue(verifier.verify_deployment(url="https://app.example.com", expected_version="1.2.3"))

    def test_verify_deployment_mismatch(self) -> None:
        verifier = LocalVerifier()
        fake_resp = MagicMock(status=200)
        fake_resp.read.return_value = b'{"status": "running", "version": "1.0.0"}'
        fake_resp.__enter__.return_value = fake_resp

        with patch("urllib.request.urlopen", return_value=fake_resp), patch("time.sleep"):
            self.assertFalse(verifier.verify_deployment(url="https://app.example.com", expected_version="2.0.0", attempts=1))


if __name__ == "__main__":
    unittest.main()
