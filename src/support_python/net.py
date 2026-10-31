"""Network, socket, and HTTP transport utility functions and protocols.

Provides TCP port connectivity inspection alongside a stdlib-only HTTP transport
abstraction for REST clients.
"""

from __future__ import annotations

import json as _json
import socket
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass
from typing import Any, Dict, Optional, Protocol


def is_port_in_use(port: int, host: str = "127.0.0.1", timeout: float = 1.0) -> bool:
    """Check whether a local or remote TCP port is currently open and listening.

    Attempts a TCP connection to the specified host and port using a socket.

    Args:
        port: TCP port number to probe.
        host: Hostname or IP address to connect to. Defaults to ``"127.0.0.1"``.
        timeout: Socket connection timeout in seconds. Defaults to ``1.0``.

    Returns:
        True if the connection succeeded (port is listening), False otherwise.
    """
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.settimeout(timeout)
        try:
            return sock.connect_ex((host, port)) == 0
        except (socket.error, OSError):
            return False


class TransportError(Exception):
    """Raised only for a genuine connectivity failure (unreachable host, timeout, DNS failure, etc.).

    A non-2xx HTTP response is NOT a TransportError -- the server was reached and answered, so
    that is still a successful round trip, returned as a :class:`RawResponse` for the caller to map
    into its own domain-specific error hierarchy.
    """


@dataclass(frozen=True)
class RawResponse:
    """A completed HTTP round trip, decoupled from any particular error-hierarchy mapping.

    Attributes:
        status_code: HTTP response status code (e.g. 200, 404, 500).
        headers: Case-preserving mapping of HTTP response header names to values.
        body: Raw bytes of the HTTP response payload.
    """

    status_code: int
    headers: Dict[str, str]
    body: bytes

    def text(self) -> str:
        """Decode the response body as a UTF-8 string.

        Returns:
            Decoded body string, or empty string if body is empty.
        """
        return self.body.decode("utf-8") if self.body else ""

    def json(self) -> Any:
        """Parse the response body as JSON.

        Returns:
            Parsed JSON object/structure, or None if body is empty or invalid JSON.
        """
        text = self.text()
        if not text:
            return None
        try:
            return _json.loads(text)
        except ValueError:
            return None


class Transport(Protocol):
    """The minimal interface a REST client needs from an HTTP layer.

    A response is *always* returned here, even for non-2xx statuses -- error-status mapping into a
    consumer's own typed exception hierarchy happens one layer up, so it applies uniformly
    regardless of which transport produced the response.
    """

    def request(
        self,
        method: str,
        url: str,
        *,
        headers: Optional[Dict[str, str]] = None,
        body: Optional[bytes] = None,
        timeout: Optional[float] = None,
    ) -> RawResponse:
        """Execute an HTTP request and return the raw response.

        Args:
            method: HTTP method (e.g. ``"GET"``, ``"POST"``, ``"DELETE"``).
            url: Fully-qualified request URL.
            headers: Optional dictionary of HTTP request headers.
            body: Optional raw bytes payload to send with the request.
            timeout: Optional request timeout in seconds.

        Returns:
            :class:`RawResponse` containing status code, headers, and body.

        Raises:
            TransportError: If a connection error, DNS failure, or timeout occurs.
        """
        ...


def build_query_string(params: Optional[Dict[str, Any]]) -> str:
    """Build a URL query string, omitting None-valued parameters and stringifying values.

    Args:
        params: Mapping of query parameter names to their values.

    Returns:
        Formatted query string prefixed with ``?`` (e.g. ``"?a=b&c=d"``), or empty string
        if params is None or contains only None values.
    """
    if not params:
        return ""
    pairs = {str(k): str(v) for k, v in params.items() if v is not None}
    if not pairs:
        return ""
    return "?" + urllib.parse.urlencode(pairs)


class UrllibTransport:
    """Default :class:`Transport` implementation built on standard library ``urllib.request``.

    Provides zero-dependency HTTP client transport execution.
    """

    def request(
        self,
        method: str,
        url: str,
        *,
        headers: Optional[Dict[str, str]] = None,
        body: Optional[bytes] = None,
        timeout: Optional[float] = None,
    ) -> RawResponse:
        """Execute an HTTP request using ``urllib.request``.

        Args:
            method: HTTP method (e.g. ``"GET"``, ``"POST"``, ``"PUT"``).
            url: Fully-qualified request URL.
            headers: Optional dictionary of HTTP request headers.
            body: Optional raw bytes payload to send with the request.
            timeout: Optional request timeout in seconds.

        Returns:
            :class:`RawResponse` with response status code, headers, and body bytes.

        Raises:
            TransportError: If a network or connectivity error occurs.
        """
        req = urllib.request.Request(url, data=body, method=method, headers=dict(headers or {}))
        try:
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                resp_headers = {k: v for k, v in resp.getheaders()}
                return RawResponse(status_code=resp.status, headers=resp_headers, body=resp.read())
        except urllib.error.HTTPError as e:
            resp_headers = {k: v for k, v in e.headers.items()} if e.headers else {}
            body = e.read() or b""
            return RawResponse(status_code=e.code, headers=resp_headers, body=body)
        except urllib.error.URLError as e:
            raise TransportError(f"Failed to reach {url}: {e.reason}") from e
        except OSError as e:
            raise TransportError(f"Failed to reach {url}: {e}") from e


__all__ = [
    "RawResponse",
    "Transport",
    "TransportError",
    "UrllibTransport",
    "build_query_string",
    "is_port_in_use",
]
