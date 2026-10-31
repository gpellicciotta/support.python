"""Embedded static HTTP server and manager with SPA routing and mock API support.

Provides thread-based static asset hosting for testing, previewing, and headless browser
captures without external web server dependencies.
"""

from __future__ import annotations

from http.server import HTTPServer, SimpleHTTPRequestHandler
import json
import mimetypes
from pathlib import Path
import threading
from typing import Any, Callable, Optional
from urllib.parse import urlparse

from .logging import CliLogger


class EmbeddedStaticServer(SimpleHTTPRequestHandler):
    """Static HTTP request handler serving webapp assets, mapped routes, and mock API endpoints.

    Attributes:
        webapp_dir: Optional root directory of static frontend assets.
        route_mounts: Mapping of URL prefixes to local directories for mounted assets.
        changelog_path: Optional path to CHANGELOG.md served at ``/CHANGELOG.md``.
        mock_api_handler: Optional custom callback ``(path, query, handler) -> bool``
            for simulating backend REST API responses.
    """

    webapp_dir: Optional[Path] = None
    route_mounts: dict[str, Path] = {}
    changelog_path: Optional[Path] = None
    mock_api_handler: Optional[Callable[[str, str, EmbeddedStaticServer], Optional[bool]]] = None

    def log_message(self, format: str, *args: Any) -> None:
        """Suppress default standard error request logging to keep CLI output clean.

        Args:
            format: Format string template.
            *args: Arguments to interpolate into format string.
        """
        pass

    def send_cors_headers(self) -> None:
        """Emit permissive Cross-Origin Resource Sharing (CORS) headers on the response."""
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, PUT, DELETE, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "*")

    def do_OPTIONS(self) -> None:
        """Handle HTTP OPTIONS requests for CORS pre-flight checks."""
        self.send_response(200)
        self.send_cors_headers()
        self.end_headers()

    def send_json_response(self, data: Any, status_code: int = 200) -> None:
        """Send a JSON-formatted HTTP response with CORS headers.

        Args:
            data: Object to serialize as JSON.
            status_code: HTTP status code to return. Defaults to 200.
        """
        content = json.dumps(data).encode("utf-8")
        self.send_response(status_code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(content)))
        self.send_cors_headers()
        self.end_headers()
        self.wfile.write(content)

    def serve_file(self, file_path: Path, content_type: Optional[str] = None) -> None:
        """Read and transmit a file payload with MIME-type headers and CORS support.

        Args:
            file_path: Local path to the file to serve.
            content_type: Optional MIME content type override string.
        """
        try:
            content = file_path.read_bytes()
            mime = content_type or mimetypes.guess_type(str(file_path))[0] or "application/octet-stream"
            if mime.startswith("text/") or mime in ("application/javascript", "text/javascript"):
                mime += "; charset=utf-8"
            self.send_response(200)
            self.send_header("Content-Type", mime)
            self.send_header("Content-Length", str(len(content)))
            self.send_cors_headers()
            self.end_headers()
            self.wfile.write(content)
        except Exception as exc:
            self.send_error(500, f"Server error: {exc}")

    def do_GET(self) -> None:
        """Handle HTTP GET requests with mock API dispatch, mounted routes, and SPA fallback."""
        parsed = urlparse(self.path)
        path = parsed.path

        if self.mock_api_handler:
            try:
                handled = self.mock_api_handler(path, parsed.query, self)
                if handled:
                    return
            except Exception as exc:
                self.send_error(500, f"Mock API error: {exc}")
                return

        if self.changelog_path and path == "/CHANGELOG.md":
            if self.changelog_path.exists():
                self.serve_file(self.changelog_path, "text/markdown; charset=utf-8")
                return
            self.send_error(404, "CHANGELOG.md not found")
            return

        if self.route_mounts:
            for prefix, mount_dir in self.route_mounts.items():
                clean_prefix = "/" + prefix.strip("/")
                if path.startswith(clean_prefix):
                    sub_path = path[len(clean_prefix) :].lstrip("/")
                    target = (mount_dir / sub_path).resolve()
                    if target.exists() and target.is_file():
                        self.serve_file(target)
                        return
                    self.send_error(404, f"Mounted file not found: {path}")
                    return

        if self.webapp_dir:
            rel_path = path.lstrip("/")
            target = (self.webapp_dir / rel_path).resolve()
            if target.is_dir():
                target = target / "index.html"

            if target.exists() and target.is_file():
                self.serve_file(target)
                return

            if "." not in Path(path).name:
                spa_index = self.webapp_dir / "index.html"
                if spa_index.exists():
                    self.serve_file(spa_index, "text/html; charset=utf-8")
                    return

        self.send_error(404, f"Path not found: {path}")


class StaticServerManager:
    """Manages an embedded HTTP server running on a daemon background thread.

    Provides context-manager lifecycle management and thread coordination.
    """

    def __init__(
        self,
        webapp_dir: Optional[Path] = None,
        route_mounts: Optional[dict[str, Path]] = None,
        changelog_path: Optional[Path] = None,
        mock_api_handler: Optional[Callable[[str, str, EmbeddedStaticServer], Optional[bool]]] = None,
        port: int = 0,
        logger: Optional[CliLogger] = None,
    ) -> None:
        """Initialize the static server manager.

        Args:
            webapp_dir: Root directory of static web assets.
            route_mounts: Mapping of URL prefix to local directory paths.
            changelog_path: Path to CHANGELOG.md to serve at ``/CHANGELOG.md``.
            mock_api_handler: Optional callback for custom mock API responses.
            port: Port to bind to (0 for automatic ephemeral port allocation).
            logger: Optional :class:`~support_python.logging.CliLogger` for operational logging.
        """
        self.webapp_dir = webapp_dir
        self.route_mounts = route_mounts or {}
        self.changelog_path = changelog_path
        self.mock_api_handler = mock_api_handler
        self.port = port
        self.logger = logger
        self.server: Optional[HTTPServer] = None
        self.server_thread: Optional[threading.Thread] = None

    def start(self) -> int:
        """Start the embedded HTTP server on a daemon thread.

        Returns:
            The bound port number allocated to the server.
        """
        handler_cls = type(
            "ConfiguredStaticServer",
            (EmbeddedStaticServer,),
            {
                "webapp_dir": self.webapp_dir,
                "route_mounts": self.route_mounts,
                "changelog_path": self.changelog_path,
                "mock_api_handler": staticmethod(self.mock_api_handler) if self.mock_api_handler else None,
            },
        )

        self.server = HTTPServer(("127.0.0.1", self.port), handler_cls)
        self.port = self.server.server_address[1]
        msg = f"Embedded static server listening on http://127.0.0.1:{self.port}"
        if self.logger:
            self.logger.info(msg)

        self.server_thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.server_thread.start()
        return self.port

    def shutdown(self) -> None:
        """Gracefully stop and close the embedded HTTP server."""
        if self.server:
            if self.logger:
                self.logger.debug("Shutting down embedded static server...")
            self.server.shutdown()
            self.server.server_close()
            self.server = None

    def __enter__(self) -> StaticServerManager:
        """Enter context manager, starting the embedded server.

        Returns:
            Self instance with started server.
        """
        self.start()
        return self

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """Exit context manager, stopping the embedded server.

        Args:
            exc_type: Exception type if an exception occurred.
            exc_val: Exception instance.
            exc_tb: Exception traceback.
        """
        self.shutdown()


__all__ = ["EmbeddedStaticServer", "StaticServerManager"]
