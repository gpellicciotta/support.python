"""DevOps and local developer environment orchestration utilities.

Provides reusable managers for Docker, MySQL, Cloud SQL proxy, Java application server processes,
email template testing, and endpoint verification. Consumed by devops scripts.
"""

from __future__ import annotations

import json
import os
import shutil
import signal
import subprocess
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime
from pathlib import Path
from typing import Any, Optional, Sequence, Union

from .sql import anonymize_sql_stream
from .env import read_env_file
from .logging import CliLogger
from .net import is_port_in_use


def run_step(
    description: str,
    args: Sequence[str],
    cwd: Optional[Union[Path, str]] = None,
    logger: Optional[CliLogger] = None,
) -> bool:
    """Run one step of a multi-step ops script (e.g. bootstrap, deploy), printing its outcome.

    Prints a banner and the step's own output unconditionally, so progress stays visible during a
    long-running script even without `--verbose`. When given, `logger` additionally records the step
    (and any failure) through the caller's own `CliLogger` (file output, verbose stdout, etc.).

    Args:
        description: Human-readable description of the operation being executed.
        args: Command-line arguments list to execute.
        cwd: Optional working directory for the subprocess. Defaults to current directory.
        logger: Optional :class:`~support_python.logging.CliLogger` for recording progress.

    Returns:
        True if the subprocess exited with return code 0, False otherwise.
    """
    print(f"\n[*] {description}", flush=True)
    print("=" * 60, flush=True)
    if logger:
        logger.progress(description)

    result = subprocess.run(list(args), cwd=str(cwd) if cwd else None, check=False)

    if result.returncode != 0:
        failure_msg = f"{description} failed (exit code {result.returncode})"
        print(f"[!] {failure_msg}", flush=True)
        if logger:
            logger.warning(failure_msg)
        return False

    return True


def resolve_cloud_sql_proxy_bin(repo_root: Optional[Union[Path, str]] = None) -> Optional[str]:
    """Resolve the Cloud SQL Auth Proxy executable path from PATH or the repository root.

    Args:
        repo_root: Optional repository root path to check for local proxy executables.

    Returns:
        String path to the executable if found, or None.
    """
    for name in ("cloud-sql-proxy", "cloud-sql-proxy.exe", "cloud-sql-proxy.x64.exe"):
        found = shutil.which(name)
        if found:
            return found

    if repo_root:
        root = Path(repo_root)
        for name in ("cloud-sql-proxy.x64.exe", "cloud-sql-proxy.exe", "cloud-sql-proxy"):
            local_exe = root / name
            if local_exe.exists():
                return str(local_exe)

    return None


class CloudSqlProxyManager:
    """Manages the lifecycle of Cloud SQL Auth Proxy instances."""

    def __init__(
        self,
        instance: str,
        logger: Optional[Any] = None,
        address: str = "0.0.0.0",
        port: int = 3606,
        credentials_file: Optional[Union[Path, str]] = None,
        repo_root: Optional[Union[Path, str]] = None,
    ) -> None:
        """Initialize the Cloud SQL Auth Proxy manager.

        Args:
            instance: Google Cloud SQL instance connection string (``project:region:instance``).
            logger: Optional logger instance.
            address: TCP address to bind the proxy listener to. Defaults to ``"0.0.0.0"``.
            port: Local TCP port to forward to Cloud SQL. Defaults to 3606.
            credentials_file: Optional path to Google service account key JSON file.
            repo_root: Optional path to repository root for local binary discovery.
        """
        self.logger = logger or CliLogger(origin="devops")
        self.address = address
        self.port = port
        self.instance = instance
        self.credentials_file = Path(credentials_file) if credentials_file else None
        self.repo_root = Path(repo_root) if repo_root else None

    def resolve_proxy_bin(self) -> Optional[str]:
        """Resolve the proxy executable binary on PATH or in the repository root.

        Returns:
            String path to the executable, or None if not found.
        """
        return resolve_cloud_sql_proxy_bin(self.repo_root)

    def start(self) -> int:
        """Start the Cloud SQL Auth Proxy via native binary if available, falling back to Docker.

        Returns:
            Exit code from the proxy process (0 on success).
        """
        if self.credentials_file and not self.credentials_file.exists():
            self.logger.error(f"Credentials file not found: {self.credentials_file}")
            return 1

        proxy_bin = self.resolve_proxy_bin()
        if proxy_bin:
            cmd = [
                proxy_bin,
                "--address",
                self.address,
                "--port",
                str(self.port),
                self.instance,
            ]
            if self.credentials_file:
                cmd.extend(["--credentials-file", str(self.credentials_file)])
        else:
            self.logger.info("Local cloud-sql-proxy binary not found on PATH; falling back to Docker image...")
            cmd = [
                "docker",
                "run",
                "--rm",
                "-p",
                f"{self.port}:{self.port}",
            ]
            if self.credentials_file:
                cmd.extend(["-v", f"{self.credentials_file.resolve()}:/config/key.json:ro"])
            cmd.extend(
                [
                    "gcr.io/cloud-sql-connectors/cloud-sql-proxy:latest",
                    "--address",
                    "0.0.0.0",
                    "--port",
                    str(self.port),
                    self.instance,
                ]
            )
            if self.credentials_file:
                cmd.extend(["--credentials-file", "/config/key.json"])

        self.logger.info(f"Starting Cloud SQL Auth Proxy on {self.address}:{self.port} -> {self.instance} ...")
        result = subprocess.run(cmd, cwd=str(self.repo_root) if self.repo_root else None)
        return result.returncode


class LocalDockerManager:
    """Manages Docker engine inspection and desktop launching."""

    def __init__(self, logger: Optional[Any] = None) -> None:
        """Initialize the local Docker manager.

        Args:
            logger: Optional logger instance.
        """
        self.logger = logger or CliLogger(origin="devops")

    def is_docker_installed(self) -> bool:
        """Check if the docker CLI is present on PATH.

        Returns:
            True if ``docker`` executable is found on PATH, False otherwise.
        """
        return shutil.which("docker") is not None

    def is_engine_running(self) -> bool:
        """Check if the Docker daemon/engine is responding to CLI requests.

        Returns:
            True if ``docker info`` succeeds, False otherwise.
        """
        if not self.is_docker_installed():
            return False
        try:
            res = subprocess.run(
                ["docker", "info"],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                timeout=5,
            )
            return res.returncode == 0
        except Exception:
            return False

    def get_status(self) -> str:
        """Return the Docker engine status string.

        Returns:
            ``"running"`` if daemon responds, ``"stopped"`` if CLI exists but daemon is down,
            or ``"not-installed"`` if CLI is not on PATH.
        """
        if not self.is_docker_installed():
            return "not-installed"
        if self.is_engine_running():
            return "running"
        return "stopped"

    def start_desktop(self, timeout_seconds: float = 60.0) -> bool:
        """Attempt to launch Docker Desktop and poll for engine readiness.

        Args:
            timeout_seconds: Maximum seconds to wait for the engine to become responsive.

        Returns:
            True if the Docker engine becomes ready within the timeout, False otherwise.
        """
        if self.is_engine_running():
            self.logger.info("Docker engine is already running")
            return True

        if os.name == "nt":
            candidates = [
                Path(os.environ.get("ProgramFiles", r"C:\Program Files")) / "Docker" / "Docker" / "Docker Desktop.exe",
                Path(os.environ.get("LOCALAPPDATA", "")) / "Programs" / "Docker" / "Docker Desktop.exe",
                Path(os.environ.get("ProgramFiles(x86)", r"C:\Program Files (x86)")) / "Docker" / "Docker" / "Docker Desktop.exe",
            ]
            exe = next((p for p in candidates if p.exists()), None)
            if not exe:
                self.logger.error("Docker Desktop installation executable not found on Windows")
                return False

            self.logger.info("Docker is not running. Launching Docker Desktop and waiting for engine readiness...")
            try:
                subprocess.Popen([str(exe)], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            except Exception as e:
                self.logger.error(f"Failed to launch Docker Desktop: {e}")
                return False

            start = time.time()
            while time.time() - start < timeout_seconds:
                if self.is_engine_running():
                    self.logger.info("Docker engine is now ready")
                    return True
                time.sleep(2.0)
            self.logger.error(f"Docker engine failed to start within {timeout_seconds} seconds")
            return False

        elif sys.platform == "darwin":
            app = Path("/Applications/Docker.app")
            if app.exists():
                self.logger.info("Docker is not running. Launching Docker.app and waiting for engine readiness...")
                try:
                    subprocess.Popen(["open", "-a", "Docker"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                except Exception as e:
                    self.logger.error(f"Failed to open Docker.app: {e}")
                    return False

                start = time.time()
                while time.time() - start < timeout_seconds:
                    if self.is_engine_running():
                        self.logger.info("Docker engine is now ready")
                        return True
                    time.sleep(2.0)
                self.logger.error(f"Docker engine failed to start within {timeout_seconds} seconds")
                return False

        self.logger.error("Automatic Docker Desktop start is not supported on this platform. Please start Docker manually.")
        return False


class LocalMySqlManager:
    """Manages an isolated local MySQL Docker container and SQL snapshot loading/anonymization."""

    def __init__(
        self,
        logger: Optional[Any] = None,
        container_name: str = "local-mysql",
        port: int = 3306,
        mysql_env_file: Optional[Union[Path, str]] = None,
        image: str = "mysql:8.0",
        setup_sql_file: Optional[Union[Path, str]] = None,
        db_name: Optional[str] = None,
        db_user: Optional[str] = None,
        db_password: Optional[str] = None,
        db_root_password: Optional[str] = None,
        repo_root: Optional[Union[Path, str]] = None,
        env_dir: Optional[Union[Path, str]] = None,
        docker_mgr: Optional[LocalDockerManager] = None,
    ) -> None:
        """Initialize the local MySQL container manager.

        Args:
            logger: Optional logger instance.
            container_name: Name of the local Docker container. Defaults to ``"local-mysql"``.
            port: Local TCP port forwarding to MySQL. Defaults to 3306.
            mysql_env_file: Optional path to environment file defining MySQL database and credentials.
            image: Docker image tag for MySQL. Defaults to ``"mysql:8.0"``.
            setup_sql_file: Optional path to initial schema setup SQL file.
            db_name: Target database name override.
            db_user: MySQL database user override.
            db_password: Password for the database user. Falls back to ``MYSQL_PASSWORD`` in the env file; no default.
            db_root_password: Password for the MySQL root user. Falls back to ``MYSQL_ROOT_PASSWORD``; no default.
            repo_root: Optional path to repository root.
            env_dir: Optional path to configuration environments directory.
            docker_mgr: Optional :class:`LocalDockerManager` instance.
        """
        self.logger = logger or CliLogger(origin="devops")
        self.docker_mgr = docker_mgr or LocalDockerManager(logger=self.logger)
        self.container_name = container_name
        self.port = port
        self.mysql_env_file = Path(mysql_env_file) if mysql_env_file else None
        self.image = image
        self.setup_sql_file = Path(setup_sql_file) if setup_sql_file else None
        self.repo_root = Path(repo_root) if repo_root else None
        self.env_dir = Path(env_dir) if env_dir else None

        self.env_vars: dict[str, str] = {}
        if self.mysql_env_file and self.mysql_env_file.exists():
            self.env_vars = read_env_file(self.mysql_env_file)

        self.db_name = db_name or self.env_vars.get("MYSQL_DATABASE", "app")
        self.db_user = db_user or self.env_vars.get("MYSQL_USER", "app")
        self.db_password: Optional[str] = db_password or self.env_vars.get("MYSQL_PASSWORD")
        self.db_root_password: Optional[str] = db_root_password or self.env_vars.get("MYSQL_ROOT_PASSWORD")

    def _require_db_password(self) -> str:
        """Return the database user password, raising :class:`ValueError` when none was supplied."""
        if not self.db_password:
            raise ValueError("No MySQL user password: pass db_password or set MYSQL_PASSWORD in the MySQL env file.")
        return self.db_password

    def _require_db_root_password(self) -> str:
        """Return the MySQL root password, raising :class:`ValueError` when none was supplied."""
        if not self.db_root_password:
            raise ValueError("No MySQL root password: pass db_root_password or set MYSQL_ROOT_PASSWORD in the MySQL env file.")
        return self.db_root_password

    def is_docker_available(self) -> bool:
        """Check if the Docker engine is running.

        Returns:
            True if the Docker daemon is accessible and responding, False otherwise.
        """
        return self.docker_mgr.is_engine_running()

    def get_container_status(self) -> Optional[str]:
        """Return the Docker container status string, or None if the container does not exist.

        Returns:
            Status string (e.g. ``"running"``, ``"exited"``) or None.
        """
        try:
            res = subprocess.run(
                ["docker", "inspect", "-f", "{{.State.Status}}", self.container_name],
                stdout=subprocess.PIPE,
                stderr=subprocess.DEVNULL,
                text=True,
                timeout=5,
            )
            if res.returncode == 0:
                return res.stdout.strip()
        except Exception:
            pass
        return None

    def wait_for_mysql_ready(self, timeout_seconds: float = 30.0) -> bool:
        """Poll MySQL container readiness via mysqladmin ping.

        Args:
            timeout_seconds: Maximum seconds to poll before timing out. Defaults to 30.0.

        Returns:
            True if MySQL is responding and accepting connections, False on timeout.
        """
        root_password = self._require_db_root_password()
        start_time = time.time()
        while time.time() - start_time < timeout_seconds:
            if is_port_in_use(self.port):
                try:
                    res = subprocess.run(
                        [
                            "docker",
                            "exec",
                            self.container_name,
                            "mysqladmin",
                            "ping",
                            "-u",
                            "root",
                            f"-p{root_password}",
                            "--silent",
                        ],
                        stdout=subprocess.DEVNULL,
                        stderr=subprocess.DEVNULL,
                        timeout=3,
                    )
                    if res.returncode == 0:
                        return True
                except Exception:
                    pass
            time.sleep(1.0)
        return False

    def are_tables_initialized(self) -> bool:
        """Check whether tables already exist in the target database.

        Returns:
            True if one or more tables exist in the target database, False otherwise.
        """
        try:
            res = subprocess.run(
                [
                    "docker",
                    "exec",
                    self.container_name,
                    "mysql",
                    "-u",
                    "root",
                    f"-p{self._require_db_root_password()}",
                    "-N",
                    "-e",
                    "SHOW TABLES;",
                    self.db_name,
                ],
                capture_output=True,
                text=True,
                timeout=5,
            )
            return res.returncode == 0 and len(res.stdout.strip()) > 0
        except Exception:
            return False

    def initialize_schema(self, setup_sql_file: Optional[Union[Path, str]] = None) -> bool:
        """Execute the setup SQL schema file against the local MySQL container.

        Args:
            setup_sql_file: Optional path to schema file. Defaults to :attr:`setup_sql_file`.

        Returns:
            True if schema executed successfully, False on error or if file is missing.
        """
        sql_file = Path(setup_sql_file) if setup_sql_file else self.setup_sql_file
        if not sql_file or not sql_file.exists():
            self.logger.warning(f"Schema setup file not found at {sql_file}")
            return False

        self.logger.info(f"Initializing database schema from {sql_file.name}")
        try:
            sql_content = sql_file.read_bytes()
            res = subprocess.run(
                [
                    "docker",
                    "exec",
                    "-i",
                    self.container_name,
                    "mysql",
                    "-u",
                    "root",
                    f"-p{self._require_db_root_password()}",
                    self.db_name,
                ],
                input=sql_content,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                timeout=20,
            )
            if res.returncode == 0:
                self.logger.info("Database schema initialized successfully")
                return True
            else:
                self.logger.error(f"Database schema initialization failed: {res.stderr.decode('utf-8', errors='replace')}")
                return False
        except Exception as e:
            self.logger.error(f"Failed to execute schema setup: {e}")
            return False

    def ensure_running(self) -> bool:
        """Ensure the MySQL container is created, running, and initialized.

        Returns:
            True if MySQL is running and accepting connections, False otherwise.

        Raises:
            ValueError: If the root or user password was neither passed nor defined in the MySQL env file.
        """
        self._require_db_root_password()
        self._require_db_password()
        if not self.is_docker_available():
            if is_port_in_use(self.port):
                self.logger.info(f"MySQL is already listening on port {self.port}")
                return True
            if not self.docker_mgr.start_desktop():
                self.logger.error(
                    "Docker is not available or Docker Desktop engine is not running. "
                    f"Please start Docker Desktop to enable the isolated MySQL container ({self.container_name}) on port {self.port} "
                    "(or use --memory-db to run without Docker)."
                )
                return False

        status = self.get_container_status()
        fresh_container = False

        if status == "running":
            if not is_port_in_use(self.port):
                self.logger.warning(
                    f"Container '{self.container_name}' is running but port {self.port} is not accessible. Restarting..."
                )
                subprocess.run(["docker", "restart", self.container_name], check=True, stdout=subprocess.DEVNULL)
            else:
                self.logger.info(f"MySQL container '{self.container_name}' is already running on port {self.port}")
                if not self.are_tables_initialized():
                    self.initialize_schema()
                return True
        elif status in ("exited", "created", "paused", "stopped"):
            self.logger.info(f"Starting existing container '{self.container_name}'...")
            res = subprocess.run(["docker", "start", self.container_name], capture_output=True, text=True)
            if res.returncode != 0:
                self.logger.error(f"Failed to start container: {res.stderr.strip()}")
                return False
        else:
            fresh_container = True
            self.logger.info(f"Creating and starting MySQL container '{self.container_name}' on port {self.port}...")
            cmd = [
                "docker",
                "run",
                "-d",
                "--name",
                self.container_name,
                "-p",
                f"{self.port}:3306",
                "-e",
                f"MYSQL_ROOT_PASSWORD={self._require_db_root_password()}",
                "-e",
                f"MYSQL_DATABASE={self.db_name}",
                "-e",
                f"MYSQL_USER={self.db_user}",
                "-e",
                f"MYSQL_PASSWORD={self._require_db_password()}",
                "-v",
                f"{self.container_name}-data:/var/lib/mysql",
                self.image,
                "--default-authentication-plugin=mysql_native_password",
            ]
            self.logger.debug(f"Running command: {' '.join(cmd)}")
            res = subprocess.run(cmd, capture_output=True, text=True)
            if res.returncode != 0:
                self.logger.error(f"Failed to create container: {res.stderr.strip()}")
                return False

        self.logger.info(f"Waiting for MySQL to become ready on port {self.port}...")
        if not self.wait_for_mysql_ready(timeout_seconds=45.0 if fresh_container else 20.0):
            self.logger.error(f"MySQL container failed to respond on port {self.port} within timeout")
            return False

        self.logger.info("MySQL container is healthy and accepting connections")
        if fresh_container:
            self.initialize_schema()

        return True

    def stop(self) -> bool:
        """Stop the MySQL Docker container.

        Returns:
            True if container stopped or was not running, False if docker stop failed.
        """
        status = self.get_container_status()
        if not status or status != "running":
            self.logger.info(f"MySQL container '{self.container_name}' is not running")
            return True

        self.logger.info(f"Stopping MySQL container '{self.container_name}'...")
        res = subprocess.run(["docker", "stop", self.container_name], capture_output=True, text=True)
        if res.returncode == 0:
            self.logger.info(f"MySQL container '{self.container_name}' stopped")
            return True
        else:
            self.logger.error(f"Failed to stop MySQL container: {res.stderr.strip()}")
            return False

    def load_snapshot(
        self,
        snapshot_path: Union[Path, str],
        target: str = "local",
        testdb_env_file: Optional[Union[Path, str]] = None,
        proxy_port: int = 3606,
        expected_test_db: Optional[str] = None,
    ) -> bool:
        """Load a SQL snapshot file into a target database (local or testdb via Cloud SQL proxy).

        Args:
            snapshot_path: Local path to the SQL snapshot dump file.
            target: Target database environment, either ``"local"`` or ``"testdb"``. Defaults to ``"local"``.
            testdb_env_file: Optional path to test database environment properties file.
            proxy_port: TCP port where Cloud SQL Auth Proxy is listening. Defaults to 3606.
            expected_test_db: Expected test database name for safety validation.

        Returns:
            True if snapshot imported successfully, False on failure.
        """
        snapshot = Path(snapshot_path)
        if not snapshot.exists():
            self.logger.error(f"Snapshot file not found at {snapshot}")
            return False

        target_lower = target.lower()
        if target_lower == "local":
            if not self.ensure_running():
                return False
            self.logger.info(f"Loading snapshot from {snapshot.name} into local MySQL container ('{self.db_name}')...")
            try:
                sql_content = snapshot.read_bytes()
                res = subprocess.run(
                    [
                        "docker",
                        "exec",
                        "-i",
                        self.container_name,
                        "mysql",
                        "-u",
                        "root",
                        f"-p{self._require_db_root_password()}",
                        self.db_name,
                    ],
                    input=sql_content,
                    capture_output=True,
                    timeout=120,
                )
                if res.returncode == 0:
                    self.logger.info(f"Snapshot loaded successfully into local database '{self.db_name}'")
                    return True
                else:
                    self.logger.error(f"Failed to load snapshot: {res.stderr.decode('utf-8', errors='replace')}")
                    return False
            except Exception as e:
                self.logger.error(f"Error loading snapshot: {e}")
                return False

        elif target_lower in ("testdb", "auth_test", "counters_test"):
            env_file = Path(testdb_env_file) if testdb_env_file else None
            if not env_file and self.env_dir:
                candidate = self.env_dir / f"{self.db_name}-testdb-devserver.env"
                if candidate.exists():
                    env_file = candidate

            if not env_file or not env_file.exists():
                self.logger.error(f"Test database environment file not found at {env_file}")
                return False

            testdb_vars = read_env_file(env_file)
            db_user = testdb_vars.get(f"{self.db_name.upper()}_DB_USER", testdb_vars.get("DB_USER", ""))
            db_pass = testdb_vars.get(f"{self.db_name.upper()}_DB_PASSWORD", testdb_vars.get("DB_PASSWORD", ""))
            jdbc_url = testdb_vars.get(f"{self.db_name.upper()}_DB_JDBC_URL", testdb_vars.get("DB_JDBC_URL", ""))

            if db_pass.startswith("plain:"):
                db_pass = db_pass[len("plain:") :]

            target_db_name = expected_test_db or f"{self.db_name}_test"
            if target_db_name not in jdbc_url and db_user != target_db_name:
                self.logger.error(f"Target safety validation failed! Expected target '{target_db_name}', got: {jdbc_url}")
                return False

            if not is_port_in_use(proxy_port):
                self.logger.error(
                    f"Cloud SQL Auth Proxy is not running on port {proxy_port}. Please launch Cloud SQL Auth Proxy first."
                )
                return False

            self.logger.info(f"Loading snapshot from {snapshot.name} into Cloud SQL '{target_db_name}' via proxy...")
            try:
                sql_content = snapshot.read_bytes()
                cmd = [
                    "docker",
                    "run",
                    "--rm",
                    "-i",
                    "--add-host",
                    "host.docker.internal:host-gateway",
                    self.image,
                    "mysql",
                    "-h",
                    "host.docker.internal",
                    "-P",
                    str(proxy_port),
                    "-u",
                    db_user,
                    f"-p{db_pass}",
                    target_db_name,
                ]
                res = subprocess.run(cmd, input=sql_content, capture_output=True, timeout=120)
                if res.returncode == 0:
                    self.logger.info(f"Snapshot loaded successfully into Cloud SQL '{target_db_name}'")
                    return True
                else:
                    self.logger.error(f"Failed to load snapshot into Cloud SQL: {res.stderr.decode('utf-8', errors='replace')}")
                    return False
            except Exception as e:
                self.logger.error(f"Error loading snapshot into Cloud SQL: {e}")
                return False
        else:
            self.logger.error(f"Invalid target '{target}'. Allowed targets are 'local' and 'testdb'.")
            return False

    def snapshot_and_anonymize(
        self,
        source: str = "cloudsql",
        input_file: Optional[Union[Path, str]] = None,
        output_file: Optional[Union[Path, str]] = None,
        load_target: Optional[str] = None,
        confirm_production: bool = False,
        custom_password: Optional[str] = None,
        app_name: Optional[str] = None,
        proddb_env_file: Optional[Union[Path, str]] = None,
        proxy_port: int = 3606,
        snapshots_dir: Optional[Union[Path, str]] = None,
    ) -> Optional[Path]:
        """Create an anonymized SQL snapshot from a live database or existing SQL dump file.

        Args:
            source: Source of database data, either ``"cloudsql"`` or ``"local"``. Defaults to ``"cloudsql"``.
            input_file: Optional existing SQL dump file path to anonymize instead of live database.
            output_file: Optional destination path for the anonymized SQL snapshot file.
            load_target: Optional target environment to immediately import the snapshot into (``"local"`` or ``"testdb"``).
            confirm_production: If True, skips interactive confirmation prompt when dumping from production Cloud SQL.
            custom_password: Optional plaintext password to hash into credentials table rows.
            app_name: Application schema profile (e.g. ``"auth"``, ``"counters"``). Defaults to database name.
            proddb_env_file: Optional path to production database environment file.
            proxy_port: TCP port for Cloud SQL Auth Proxy. Defaults to 3606.
            snapshots_dir: Directory where default snapshot output files are placed.

        Returns:
            Resolved :class:`pathlib.Path` of the created anonymized snapshot, or None on failure.
        """
        app = app_name or self.db_name
        snap_dir = (
            Path(snapshots_dir)
            if snapshots_dir
            else (self.repo_root / "output" / "snapshots" if self.repo_root else Path("output/snapshots"))
        )
        snap_dir.mkdir(parents=True, exist_ok=True)

        out_file = (
            Path(output_file) if output_file else snap_dir / f"{app}-anonymized-{datetime.now().strftime('%Y%m%d-%H%M%S')}.sql"
        )

        stats: dict[str, int] = {}
        if input_file:
            in_path = Path(input_file)
            if not in_path.exists():
                self.logger.error(f"Input file not found: {in_path}")
                return None
            self.logger.info(f"Anonymizing existing SQL dump from {in_path.name}...")
            with open(in_path, "r", encoding="utf-8", errors="replace") as in_f:
                with open(out_file, "w", encoding="utf-8") as out_f:
                    stats = anonymize_sql_stream(in_f, out_f, app=app, custom_password=custom_password)
        else:
            if source == "cloudsql":
                if not confirm_production:
                    self.logger.warning("Accessing live production database on Cloud SQL.")
                    confirm = input("Confirm reading production database for incident diagnosis? [y/N]: ").strip().lower()
                    if confirm not in ("y", "yes"):
                        self.logger.error("Production access cancelled by user. Aborting.")
                        return None

                env_file = Path(proddb_env_file) if proddb_env_file else None
                if not env_file and self.env_dir:
                    candidate = self.env_dir / f"{app}-proddb-cloudrun.env"
                    if candidate.exists():
                        env_file = candidate

                if not env_file or not env_file.exists():
                    self.logger.error(f"Production environment file not found at {env_file}")
                    return None

                prod_vars = read_env_file(env_file)
                db_user = prod_vars.get(f"{app.upper()}_DB_USER", prod_vars.get("DB_USER", app))
                db_pass = prod_vars.get(f"{app.upper()}_DB_PASSWORD", prod_vars.get("DB_PASSWORD", ""))
                if db_pass.startswith("plain:"):
                    db_pass = db_pass[len("plain:") :]

                if not is_port_in_use(proxy_port):
                    self.logger.error(
                        f"Cloud SQL Auth Proxy is not running on port {proxy_port}. Please launch Cloud SQL Auth Proxy first."
                    )
                    return None

                self.logger.info(f"Dumping database '{app}' from Cloud SQL via proxy on port {proxy_port}...")
                dump_cmd = [
                    "docker",
                    "run",
                    "--rm",
                    "--add-host",
                    "host.docker.internal:host-gateway",
                    self.image,
                    "mysqldump",
                    "-h",
                    "host.docker.internal",
                    "-P",
                    str(proxy_port),
                    "-u",
                    db_user,
                    f"-p{db_pass}",
                    "--no-tablespaces",
                    "--skip-add-locks",
                    "--set-gtid-purged=OFF",
                    app,
                ]

                proc = subprocess.Popen(
                    dump_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, encoding="utf-8", errors="replace"
                )
                with open(out_file, "w", encoding="utf-8") as out_f:
                    stats = anonymize_sql_stream(proc.stdout, out_f, app=app, custom_password=custom_password)
                proc.wait()
                if proc.returncode != 0:
                    self.logger.error(f"mysqldump failed: {proc.stderr.read() if proc.stderr else ''}")
                    return None

            elif source == "local":
                if not self.ensure_running():
                    return None
                self.logger.info(f"Dumping database '{self.db_name}' from local MySQL container...")
                dump_cmd = [
                    "docker",
                    "exec",
                    self.container_name,
                    "mysqldump",
                    "-u",
                    "root",
                    f"-p{self._require_db_root_password()}",
                    "--no-tablespaces",
                    "--skip-add-locks",
                    self.db_name,
                ]
                proc = subprocess.Popen(
                    dump_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, encoding="utf-8", errors="replace"
                )
                with open(out_file, "w", encoding="utf-8") as out_f:
                    stats = anonymize_sql_stream(proc.stdout, out_f, app=app, custom_password=custom_password)
                proc.wait()
                if proc.returncode != 0:
                    self.logger.error(f"mysqldump failed: {proc.stderr.read() if proc.stderr else ''}")
                    return None
            else:
                self.logger.error(f"Unsupported source: {source}")
                return None

        self.logger.info(f"Anonymized snapshot written to: {out_file}")
        for table, count in stats.items():
            self.logger.info(f"  - Table '{table}': {count} row(s) anonymized")

        if load_target:
            self.load_snapshot(out_file, target=load_target)

        return out_file


class LocalServerManager:
    """Manages the lifecycle of a local Java application server process.

    Handles building distribution packages, foreground/background execution,
    PID tracking, and polling health status endpoints.
    """

    def __init__(
        self,
        logger: Optional[Any] = None,
        port: int = 8080,
        env_file: Optional[Union[Path, str]] = None,
        pid_file: Optional[Union[Path, str]] = None,
        log_file: Optional[Union[Path, str]] = None,
        server_jar: Optional[Union[Path, str]] = None,
        config_file: Optional[Union[Path, str]] = None,
        repo_root: Optional[Union[Path, str]] = None,
        app_static_dir: Optional[Union[Path, str]] = None,
        app_name: Optional[str] = None,
        extra_env: Optional[dict[str, str]] = None,
        extra_jvm_args: Optional[Sequence[str]] = None,
        gradle_task: str = ":server:installDist",
        health_endpoint: str = "/api/status",
        cloud_sql_credentials: Optional[Union[Path, str]] = None,
    ) -> None:
        """Initialize the local server manager.

        Args:
            logger: Logger instance. Defaults to CliLogger.
            port: Local TCP port for the server to bind. Defaults to 8080.
            env_file: Path to environment properties file passed to the server.
            pid_file: Path to file tracking the background process ID.
            log_file: Path to log file where server logs will be written.
            server_jar: Path to executable server JAR artifact.
            config_file: Path to application configuration file.
            repo_root: Root repository path containing Gradle wrapper.
            app_static_dir: Path to directory serving frontend static assets.
            app_name: Application name used for environment variables and logs. Defaults to ``"App"``.
            extra_env: Dictionary of additional environment variables passed to server.
            extra_jvm_args: Sequence of extra JVM arguments (e.g. ``["-Xmx512m"]``).
            gradle_task: Gradle task to run when building the distribution JAR. Defaults to ``":server:installDist"``.
            health_endpoint: HTTP health check endpoint path. Defaults to ``"/api/status"``.
            cloud_sql_credentials: Path to Google Application Credentials JSON file.
        """
        self.logger = logger or CliLogger(origin="devops")
        self.port = port
        self.env_file = Path(env_file) if env_file else None
        self.pid_file = Path(pid_file) if pid_file else None
        self.log_file = Path(log_file) if log_file else None
        self.server_jar = Path(server_jar) if server_jar else None
        self.config_file = Path(config_file) if config_file else None
        self.repo_root = Path(repo_root) if repo_root else None
        self.app_static_dir = Path(app_static_dir) if app_static_dir else None
        self.app_name = app_name or "App"
        self.extra_env = extra_env or {}
        self.extra_jvm_args = list(extra_jvm_args) if extra_jvm_args else []
        self.gradle_task = gradle_task
        self.health_endpoint = health_endpoint
        self.cloud_sql_credentials = Path(cloud_sql_credentials) if cloud_sql_credentials else None

    def is_java_available(self) -> bool:
        """Check if the Java runtime executable is available on PATH.

        Returns:
            True if ``java`` binary is found on system PATH, False otherwise.
        """
        return shutil.which("java") is not None

    def build_server_if_needed(self, force_build: bool = False) -> bool:
        """Build the server distribution package via Gradle if missing or forced.

        Args:
            force_build: If True, triggers Gradle build even if distribution JAR exists. Defaults to False.

        Returns:
            True if build succeeded or existing JAR was verified, False on build failure.
        """
        if not force_build and self.server_jar and self.server_jar.exists():
            self.logger.debug(f"Server distribution JAR exists at {self.server_jar}")
            return True

        self.logger.info(f"Building server distribution package via Gradle ({self.gradle_task})...")
        gradle_cmd = "gradlew.bat" if os.name == "nt" else "./gradlew"
        root = self.repo_root or Path.cwd()
        gradle_exe = root / gradle_cmd

        if not gradle_exe.exists():
            gradle_cmd = "gradle"

        try:
            res = subprocess.run(
                [str(gradle_exe if gradle_exe.exists() else gradle_cmd), self.gradle_task, "-x", "test"],
                cwd=str(root),
                capture_output=True,
                text=True,
                timeout=180,
            )
            if res.returncode != 0:
                self.logger.error(f"Gradle build failed:\n{res.stderr}\n{res.stdout}")
                return False
        except Exception as e:
            self.logger.error(f"Failed to execute Gradle build: {e}")
            return False

        if self.server_jar and not self.server_jar.exists():
            self.logger.error(f"Expected server JAR not found after build: {self.server_jar}")
            return False

        self.logger.info("Server distribution built successfully")
        return True

    def get_running_pid(self) -> Optional[int]:
        """Read the PID file and verify if the process is currently running.

        Returns:
            Running process PID if alive, or None if PID file is absent, unreadable, or stale.
        """
        if self.pid_file and self.pid_file.exists():
            try:
                pid = int(self.pid_file.read_text(encoding="utf-8").strip())
                if os.name == "nt":
                    import ctypes

                    kernel32 = ctypes.windll.kernel32
                    handle = kernel32.OpenProcess(0x1000, False, pid)
                    if handle != 0:
                        kernel32.CloseHandle(handle)
                        return pid
                else:
                    os.kill(pid, 0)
                    return pid
            except Exception:
                pass
        return None

    def poll_health_status(self, timeout_seconds: float = 30.0) -> tuple[bool, dict[str, Any]]:
        """Poll the server's health status endpoint until healthy or timeout.

        Args:
            timeout_seconds: Maximum duration in seconds to wait for a successful HTTP 200. Defaults to 30.0.

        Returns:
            Tuple of ``(is_healthy, status_data)`` where ``status_data`` is parsed JSON response dict.
        """
        status_url = f"http://localhost:{self.port}{self.health_endpoint}"
        start = time.time()
        while time.time() - start < timeout_seconds:
            try:
                req = urllib.request.Request(status_url, headers={"Accept": "application/json"})
                with urllib.request.urlopen(req, timeout=2.0) as resp:
                    if resp.status == 200:
                        data = json.loads(resp.read().decode("utf-8"))
                        return True, data
            except Exception:
                pass
            time.sleep(1.0)
        return False, {}

    def find_pid_by_port(self, port: Optional[int] = None) -> Optional[int]:
        """Find the PID of the process listening on the specified TCP port.

        Args:
            port: Port to inspect. Defaults to :attr:`port`.

        Returns:
            Listening process PID if found, or None.
        """
        target_port = port or self.port
        if os.name == "nt":
            try:
                res = subprocess.run(["netstat", "-ano", "-p", "tcp"], capture_output=True, text=True, timeout=5)
                for line in res.stdout.splitlines():
                    if f":{target_port}" in line and "LISTENING" in line:
                        parts = line.strip().split()
                        return int(parts[-1])
            except Exception:
                pass
        else:
            try:
                res = subprocess.run(["lsof", "-t", f"-i:{target_port}"], capture_output=True, text=True, timeout=5)
                if res.stdout.strip():
                    return int(res.stdout.strip().split()[0])
            except Exception:
                pass
        return None

    def start(self, background: bool = False, force_build: bool = False, memory_db: bool = False) -> bool:
        """Start the server in either background or foreground mode.

        Args:
            background: If True, launches server detached in background and writes PID file. Defaults to False.
            force_build: If True, forces rebuild of distribution JAR before starting. Defaults to False.
            memory_db: If True, configures server to use in-memory SQLite/H2 database. Defaults to False.

        Returns:
            True if server launched and passed health check, False otherwise.
        """
        if is_port_in_use(self.port):
            ok, data = self.poll_health_status(timeout_seconds=2.0)
            if ok:
                self.logger.info(
                    f"Local application server is already running on http://localhost:{self.port} (version={data.get('version')})"
                )
                return True
            self.logger.error(f"Port {self.port} is already in use by another process")
            return False

        if not self.is_java_available():
            self.logger.error("Java runtime is not found on PATH. Please ensure JDK is installed and on PATH.")
            return False

        if not self.build_server_if_needed(force_build=force_build):
            return False

        if self.env_file and not self.env_file.exists():
            self.logger.error(f"Environment properties file not found: {self.env_file}")
            return False

        env_name = self.env_file.name if self.env_file else "default"
        self.logger.info(f"Starting server with properties from {env_name} on port {self.port}...")

        env = os.environ.copy()
        if self.app_static_dir:
            env[f"{self.app_name.upper()}_STATIC_DIR"] = str(self.app_static_dir)
        env["PORT"] = str(self.port)
        env["BASE_URL"] = f"http://localhost:{self.port}"
        if self.cloud_sql_credentials and self.cloud_sql_credentials.exists():
            env["GOOGLE_APPLICATION_CREDENTIALS"] = str(self.cloud_sql_credentials)
        env.update(self.extra_env)

        cmd: list[str] = ["java"]
        if self.env_file:
            cmd.append(f"-Denvironment-properties-file={self.env_file}")
        cmd.extend(self.extra_jvm_args)

        if self.server_jar:
            cmd.extend(["-jar", str(self.server_jar)])
        if self.config_file:
            cmd.append(f"--config-file={self.config_file}")
        cmd.append("--mail.back-end-type=com.pellicciotta.support.mail.DummyBackEnd")
        if self.log_file:
            cmd.append(f"--logging.file-path={self.log_file}")
        if memory_db:
            cmd.append("--db.jdbc-url=memory")
        cmd.append("start")

        self.logger.debug(f"Executing: {' '.join(cmd)}")
        if self.pid_file:
            self.pid_file.parent.mkdir(parents=True, exist_ok=True)

        cwd_str = str(self.repo_root) if self.repo_root else None

        if background:
            stdout_file = None
            stderr_file = None
            if self.log_file:
                stdout_log = self.log_file.with_suffix(".stdout.log")
                stderr_log = self.log_file.with_suffix(".stderr.log")
                stdout_file = open(stdout_log, "a", encoding="utf-8")
                stderr_file = open(stderr_log, "a", encoding="utf-8")

            extra_kwargs: dict[str, Any] = {}
            if os.name == "nt":
                extra_kwargs["creationflags"] = subprocess.CREATE_NEW_PROCESS_GROUP | subprocess.DETACHED_PROCESS
            else:
                extra_kwargs["start_new_session"] = True

            proc = subprocess.Popen(
                cmd,
                cwd=cwd_str,
                env=env,
                stdout=stdout_file or subprocess.DEVNULL,
                stderr=stderr_file or subprocess.DEVNULL,
                stdin=subprocess.DEVNULL,
                **extra_kwargs,
            )
            if stdout_file:
                stdout_file.close()
            if stderr_file:
                stderr_file.close()

            if self.pid_file:
                self.pid_file.write_text(str(proc.pid), encoding="utf-8")
            self.logger.info(f"Server launched in background (PID: {proc.pid})")
            self.logger.info(f"Waiting for server health check at http://localhost:{self.port}{self.health_endpoint}...")
            ok, data = self.poll_health_status(timeout_seconds=30.0)
            if ok:
                self.logger.info(f"Server is ready! Serving webapp and API on http://localhost:{self.port}")
                return True
            else:
                self.logger.error(f"Server failed to start or health check timed out. Check logs at {self.log_file}")
                return False
        else:
            proc = subprocess.Popen(cmd, cwd=cwd_str, env=env)
            if self.pid_file:
                self.pid_file.write_text(str(proc.pid), encoding="utf-8")
            self.logger.info(f"Server started (PID: {proc.pid})")

            def handle_sigint(signum: Any, frame: Any) -> None:
                self.logger.info("Received stop signal, shutting down server...")
                self.stop()
                sys.exit(0)

            signal.signal(signal.SIGINT, handle_sigint)
            signal.signal(signal.SIGTERM, handle_sigint)

            self.logger.info(f"Waiting for server health check at http://localhost:{self.port}{self.health_endpoint}...")
            ok, data = self.poll_health_status(timeout_seconds=30.0)
            if ok:
                self.logger.info(f"Server is ready! Serving webapp and API on http://localhost:{self.port}")
                self.logger.info("Press Ctrl+C to stop the server.")
            try:
                proc.wait()
            except KeyboardInterrupt:
                handle_sigint(None, None)
            return True

    def stop(self) -> bool:
        """Stop the running server process.

        Terminates the process by PID (from PID file or listening port), and removes PID file.

        Returns:
            True if process terminated successfully or was already stopped, False on error.
        """
        pid = self.get_running_pid() or self.find_pid_by_port(self.port)
        if not is_port_in_use(self.port) and not pid:
            self.logger.info("Server is already stopped")
            if self.pid_file and self.pid_file.exists():
                self.pid_file.unlink()
            return True

        self.logger.info(f"Stopping server on port {self.port}...")

        if pid:
            try:
                if os.name == "nt":
                    subprocess.run(["taskkill", "/F", "/T", "/PID", str(pid)], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                else:
                    os.kill(pid, signal.SIGTERM)
            except Exception as e:
                self.logger.debug(f"Could not kill process {pid}: {e}")

        if self.pid_file and self.pid_file.exists():
            try:
                self.pid_file.unlink()
            except Exception:
                pass

        time.sleep(1.0)
        self.logger.info("Server stopped")
        return True


class LocalMailManager:
    """Manages email template test dispatching through the application server CLI."""

    def __init__(self, logger: Optional[Any] = None, server_manager: Optional[LocalServerManager] = None) -> None:
        """Initialize the local mail manager.

        Args:
            logger: Logger instance. Defaults to CliLogger.
            server_manager: Server manager providing runtime and JAR context.
        """
        self.logger = logger or CliLogger(origin="devops")
        self.server_manager = server_manager or LocalServerManager(logger=self.logger)

    def test_emails(
        self,
        recipient: str,
        env_file: Optional[Union[Path, str]] = None,
        app_name: Optional[str] = None,
        force_build: bool = False,
    ) -> bool:
        """Dispatch sample test emails for template validation via server CLI.

        Args:
            recipient: Destination email address to receive sample template dispatches.
            env_file: Optional path to environment properties file.
            app_name: Application name profile. Defaults to server manager's app name.
            force_build: If True, forces Gradle rebuild of server JAR before dispatching. Defaults to False.

        Returns:
            True if all test emails sent successfully, False otherwise.
        """
        if not self.server_manager.is_java_available():
            self.logger.error("Java runtime is not found on PATH. Please ensure JDK is installed and on PATH.")
            return False

        if not self.server_manager.build_server_if_needed(force_build=force_build):
            return False

        target_env = Path(env_file) if env_file else self.server_manager.env_file
        if not target_env or not target_env.exists():
            self.logger.error(f"Environment properties file not found: {target_env}")
            return False

        target_app = app_name or self.server_manager.app_name
        self.logger.info(f"Dispatching test emails for templates ({target_app}) to '{recipient}' using {target_env.name}...")

        cmd = [
            "java",
            f"-Denvironment-properties-file={target_env}",
            "-jar",
            str(self.server_manager.server_jar),
        ]
        if self.server_manager.config_file:
            cmd.append(f"--config-file={self.server_manager.config_file}")
        cmd.extend(["test-mail-formats", recipient, target_app])

        self.logger.debug(f"Executing: {' '.join(cmd)}")
        try:
            res = subprocess.run(cmd, cwd=str(self.server_manager.repo_root) if self.server_manager.repo_root else None, text=True)
            if res.returncode == 0:
                self.logger.info(f"All test emails successfully sent to '{recipient}'")
                return True
            else:
                self.logger.error(f"test-mail-formats exited with error code {res.returncode}")
                return False
        except Exception as e:
            self.logger.error(f"Failed to execute test-mail-formats: {e}")
            return False


class LocalVerifier:
    """Verifies local running server endpoints, webapp static assets, and remote deployments."""

    def __init__(self, logger: Optional[Any] = None, port: int = 8080) -> None:
        """Initialize the local verifier.

        Args:
            logger: Logger instance. Defaults to CliLogger.
            port: Local TCP port where server is listening. Defaults to 8080.
        """
        self.logger = logger or CliLogger(origin="devops")
        self.port = port
        self.base_url = f"http://localhost:{port}"

    def verify_health_status(self, endpoint: str = "/api/status") -> bool:
        """Verify that the server returns HTTP 200 and a valid JSON status response.

        Args:
            endpoint: Health check endpoint URI path. Defaults to ``"/api/status"``.

        Returns:
            True if health check returned HTTP 200 with valid JSON body, False otherwise.
        """
        url = f"{self.base_url}{endpoint}"
        try:
            req = urllib.request.Request(url, headers={"Accept": "application/json"})
            with urllib.request.urlopen(req, timeout=5.0) as resp:
                if resp.status != 200:
                    self.logger.error(f"Health check failed: GET {url} returned HTTP {resp.status}")
                    return False
                data = json.loads(resp.read().decode("utf-8"))
                status_val = data.get("status")
                version_val = data.get("version")
                self.logger.info(f"Health Check: OK (status={status_val!r}, version={version_val!r})")
                return True
        except Exception as e:
            self.logger.error(f"Health check failed: {e}")
            return False

    def verify_static_index(self, path: str = "/") -> bool:
        """Verify that the static index route serves a valid HTML document.

        Args:
            path: Static index URL path. Defaults to ``"/"``.

        Returns:
            True if endpoint returns HTTP 200 and contains HTML tags, False otherwise.
        """
        url = f"{self.base_url}{path}"
        try:
            with urllib.request.urlopen(url, timeout=5.0) as resp:
                if resp.status != 200:
                    self.logger.error(f"Static index check failed: GET {url} returned HTTP {resp.status}")
                    return False
                html = resp.read().decode("utf-8", errors="replace")
                if "<!DOCTYPE html>" not in html and "<html" not in html:
                    self.logger.error("Static index check failed: response did not contain HTML document")
                    return False
                self.logger.info("Static Index Serving: OK (HTTP 200, valid HTML)")
                return True
        except Exception as e:
            self.logger.error(f"Static index request failed: {e}")
            return False

    def verify_static_assets(self, assets: Optional[Sequence[str]] = None) -> bool:
        """Verify that key static assets are served with HTTP 200.

        Args:
            assets: Sequence of asset URL paths to check. Defaults to ``["/css/main.css", "/js/main.mjs"]``.

        Returns:
            True if all specified assets return HTTP 200, False if any asset fails.
        """
        check_assets = list(assets) if assets else ["/css/main.css", "/js/main.mjs"]
        for asset in check_assets:
            url = f"{self.base_url}{asset}"
            try:
                with urllib.request.urlopen(url, timeout=5.0) as resp:
                    if resp.status != 200:
                        self.logger.error(f"Asset check failed: GET {url} returned HTTP {resp.status}")
                        return False
            except Exception as e:
                self.logger.error(f"Asset request failed for {url}: {e}")
                return False
        self.logger.info(f"Static Asset Serving: OK ({len(check_assets)} assets verified)")
        return True

    def verify_deployment(
        self,
        url: str,
        expected_version: Optional[str] = None,
        attempts: int = 10,
        retry_delay: float = 3.0,
    ) -> bool:
        """Verify remote service health and version match with retry polling.

        Args:
            url: Base URL of remote deployment to verify.
            expected_version: Optional expected version string to validate against returned version.
            attempts: Maximum number of polling attempts before failing. Defaults to 10.
            retry_delay: Delay in seconds between polling attempts. Defaults to 3.0.

        Returns:
            True if deployment responds with healthy status and matching version, False on failure.
        """
        status_url = f"{url.rstrip('/')}/api/status"
        self.logger.info(f"Verifying live deployment at {status_url} (expected version: {expected_version or 'any'})...")

        for attempt in range(1, attempts + 1):
            try:
                req = urllib.request.Request(status_url, headers={"Accept": "application/json"})
                with urllib.request.urlopen(req, timeout=5.0) as resp:
                    if resp.status == 200:
                        data = json.loads(resp.read().decode("utf-8"))
                        status_val = data.get("status")
                        actual_version = data.get("version")
                        if status_val == "running":
                            if expected_version and actual_version != expected_version:
                                self.logger.warning(
                                    f"[Attempt {attempt}/{attempts}] Server is running but version is '{actual_version}' (expected '{expected_version}')"
                                )
                            else:
                                self.logger.info(f"Live deployment verified: status='{status_val}', version='{actual_version}'")
                                return True
            except Exception as e:
                self.logger.debug(f"[Attempt {attempt}/{attempts}] Health check failed: {e}")

            if attempt < attempts:
                time.sleep(retry_delay)

        self.logger.error(f"Deployment verification failed after {attempts} attempts")
        return False


__all__ = [
    "run_step",
    "resolve_cloud_sql_proxy_bin",
    "CloudSqlProxyManager",
    "LocalDockerManager",
    "LocalMySqlManager",
    "LocalServerManager",
    "LocalMailManager",
    "LocalVerifier",
]
