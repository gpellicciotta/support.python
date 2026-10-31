"""Tests for unified support_python.net module."""

from __future__ import annotations

import socket
import unittest
import urllib.error
from unittest.mock import MagicMock, patch

from support_python.net import (
    RawResponse,
    TransportError,
    UrllibTransport,
    build_query_string,
    is_port_in_use,
)


class TestNetSocketUtils(unittest.TestCase):
    def test_is_port_in_use_with_active_server(self) -> None:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.bind(("127.0.0.1", 0))
            s.listen(1)
            port = s.getsockname()[1]
            self.assertTrue(is_port_in_use(port, "127.0.0.1"))

    def test_is_port_in_use_with_closed_port(self) -> None:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.bind(("127.0.0.1", 0))
            port = s.getsockname()[1]
        self.assertFalse(is_port_in_use(port, "127.0.0.1", timeout=0.1))

    @patch("socket.socket")
    def test_is_port_in_use_socket_error(self, mock_socket_cls: unittest.mock.MagicMock) -> None:
        mock_sock = mock_socket_cls.return_value.__enter__.return_value
        mock_sock.connect_ex.side_effect = OSError("Network error")
        self.assertFalse(is_port_in_use(9999))


class RawResponseTests(unittest.TestCase):
    def test_text_decodes_body(self) -> None:
        response = RawResponse(status_code=200, headers={}, body=b"hello")
        self.assertEqual(response.text(), "hello")

    def test_text_empty_body(self) -> None:
        response = RawResponse(status_code=204, headers={}, body=b"")
        self.assertEqual(response.text(), "")

    def test_json_parses_valid_body(self) -> None:
        response = RawResponse(status_code=200, headers={}, body=b'{"a": 1}')
        self.assertEqual(response.json(), {"a": 1})

    def test_json_returns_none_for_empty_body(self) -> None:
        response = RawResponse(status_code=204, headers={}, body=b"")
        self.assertIsNone(response.json())

    def test_json_returns_none_for_invalid_json(self) -> None:
        response = RawResponse(status_code=200, headers={}, body=b"not json")
        self.assertIsNone(response.json())


class BuildQueryStringTests(unittest.TestCase):
    def test_no_params(self) -> None:
        self.assertEqual(build_query_string(None), "")
        self.assertEqual(build_query_string({}), "")

    def test_drops_none_values(self) -> None:
        self.assertEqual(build_query_string({"a": "1", "b": None}), "?a=1")

    def test_all_none_values(self) -> None:
        self.assertEqual(build_query_string({"a": None}), "")

    def test_stringifies_values(self) -> None:
        self.assertEqual(build_query_string({"a": 1}), "?a=1")


class UrllibTransportTests(unittest.TestCase):
    def setUp(self) -> None:
        self.transport = UrllibTransport()

    @patch("urllib.request.urlopen")
    def test_successful_request_returns_raw_response(self, mock_urlopen: MagicMock) -> None:
        mock_resp = MagicMock()
        mock_resp.status = 200
        mock_resp.getheaders.return_value = [("Content-Type", "application/json")]
        mock_resp.read.return_value = b'{"ok": true}'
        mock_urlopen.return_value.__enter__.return_value = mock_resp

        response = self.transport.request("GET", "https://example.test/api")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.headers, {"Content-Type": "application/json"})
        self.assertEqual(response.json(), {"ok": True})

    @patch("urllib.request.urlopen")
    def test_http_error_returns_raw_response_not_exception(self, mock_urlopen: MagicMock) -> None:
        error = urllib.error.HTTPError(
            url="https://example.test/api",
            code=404,
            msg="Not Found",
            hdrs={"Content-Type": "text/plain"},
            fp=None,
        )
        error.read = MagicMock(return_value=b"not found")
        mock_urlopen.side_effect = error

        response = self.transport.request("GET", "https://example.test/api")

        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.text(), "not found")

    @patch("urllib.request.urlopen")
    def test_url_error_raises_transport_error(self, mock_urlopen: MagicMock) -> None:
        mock_urlopen.side_effect = urllib.error.URLError("connection refused")

        with self.assertRaises(TransportError):
            self.transport.request("GET", "https://example.test/api")

    @patch("urllib.request.urlopen")
    def test_os_error_raises_transport_error(self, mock_urlopen: MagicMock) -> None:
        mock_urlopen.side_effect = OSError("timed out")

        with self.assertRaises(TransportError):
            self.transport.request("GET", "https://example.test/api")


if __name__ == "__main__":
    unittest.main()
