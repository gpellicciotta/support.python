"""Tests for support_python.models module."""

from datetime import datetime, timezone
import unittest

from support_python.models import (
    ApiInfo,
    ApiRoute,
    LogEntry,
    ServerStatus,
    Status,
    WireEnum,
)


class SampleItemType(WireEnum):
    SIMPLE_INTEGER = "simple-integer"
    ONE_TIME_CODE = "one-time-code"
    ACCOUNT = "account"


class WireEnumTests(unittest.TestCase):
    def test_from_wire_exact_match(self) -> None:
        self.assertEqual(SampleItemType.from_wire("simple-integer"), SampleItemType.SIMPLE_INTEGER)
        self.assertEqual(SampleItemType.from_wire("one-time-code"), SampleItemType.ONE_TIME_CODE)

    def test_from_wire_case_and_underscore_insensitive(self) -> None:
        self.assertEqual(SampleItemType.from_wire("SIMPLE_INTEGER"), SampleItemType.SIMPLE_INTEGER)
        self.assertEqual(SampleItemType.from_wire("One_Time_Code"), SampleItemType.ONE_TIME_CODE)
        self.assertEqual(SampleItemType.from_wire("account"), SampleItemType.ACCOUNT)
        self.assertEqual(SampleItemType.from_wire("ACCOUNT"), SampleItemType.ACCOUNT)

    def test_from_wire_instance_passthrough(self) -> None:
        self.assertEqual(SampleItemType.from_wire(SampleItemType.ACCOUNT), SampleItemType.ACCOUNT)

    def test_from_wire_none(self) -> None:
        self.assertIsNone(SampleItemType.from_wire(None))

    def test_from_wire_unknown_value_raises(self) -> None:
        with self.assertRaises(ValueError):
            SampleItemType.from_wire("unknown-item")

    def test_to_wire(self) -> None:
        self.assertEqual(SampleItemType.SIMPLE_INTEGER.to_wire(), "simple-integer")
        self.assertEqual(SampleItemType.ONE_TIME_CODE.to_wire(), "one-time-code")


class ApiRouteTests(unittest.TestCase):
    def test_api_route_creation_and_sync(self) -> None:
        route = ApiRoute(method="GET", uri_pattern="/api/items", description="List items", realms=("admin",))
        self.assertEqual(route.method, "GET")
        self.assertEqual(route.uri_pattern, "/api/items")
        self.assertEqual(route.path, "/api/items")
        self.assertEqual(route.description, "List items")
        self.assertEqual(route.realms, ("admin",))

    def test_api_route_path_init_syncs_uri_pattern(self) -> None:
        route = ApiRoute(method="POST", path="/api/items", description="Create item")
        self.assertEqual(route.path, "/api/items")
        self.assertEqual(route.uri_pattern, "/api/items")

    def test_api_route_from_wire_and_to_wire(self) -> None:
        data = {
            "method": "GET",
            "uri-pattern": "/api/users",
            "description": "Get users",
            "realms": ["owner", "admin"],
        }
        route = ApiRoute.from_wire(data)
        self.assertEqual(route.method, "GET")
        self.assertEqual(route.uri_pattern, "/api/users")
        self.assertEqual(route.path, "/api/users")
        self.assertEqual(route.realms, ("owner", "admin"))

        wire_out = route.to_wire()
        self.assertEqual(wire_out["method"], "GET")
        self.assertEqual(wire_out["uri-pattern"], "/api/users")
        self.assertEqual(wire_out["description"], "Get users")
        self.assertEqual(wire_out["realms"], ["owner", "admin"])

    def test_api_route_from_wire_camel_case(self) -> None:
        data = {
            "method": "DELETE",
            "uriPattern": "/api/users/{id}",
            "description": "Delete user",
        }
        route = ApiRoute.from_wire(data)
        self.assertEqual(route.uri_pattern, "/api/users/{id}")
        self.assertEqual(route.path, "/api/users/{id}")


class ApiInfoTests(unittest.TestCase):
    def test_api_info_from_wire_kebab_case(self) -> None:
        data = {
            "version": "1.0.0",
            "api-end-points": [
                {"method": "GET", "uri-pattern": "/api/status", "description": "Status"},
                {"method": "GET", "uri-pattern": "/api/info", "description": "Info"},
            ],
        }
        info = ApiInfo.from_wire(data)
        self.assertEqual(info.version, "1.0.0")
        self.assertEqual(len(info.api_end_points), 2)
        self.assertEqual(info.api_end_points[0].method, "GET")
        self.assertEqual(info.api_end_points[0].uri_pattern, "/api/status")
        self.assertEqual(info.api_endpoints, info.api_end_points)

    def test_api_info_from_wire_camel_case(self) -> None:
        data = {
            "version": "2.0.0",
            "apiEndPoints": [
                {"method": "POST", "uriPattern": "/api/login", "description": "Login"},
            ],
        }
        info = ApiInfo.from_wire(data)
        self.assertEqual(info.version, "2.0.0")
        self.assertEqual(len(info.api_endpoints or ()), 1)

    def test_api_info_to_wire(self) -> None:
        route = ApiRoute(method="GET", uri_pattern="/api/status", description="Status")
        info = ApiInfo(version="1.0.0", api_end_points=(route,))
        wire = info.to_wire()
        self.assertEqual(wire["version"], "1.0.0")
        self.assertEqual(len(wire["api-end-points"]), 1)
        self.assertEqual(wire["api-end-points"][0]["method"], "GET")


class ServerStatusTests(unittest.TestCase):
    def test_server_status_from_wire_and_to_wire(self) -> None:
        data = {
            "name": "example-counters",
            "version": "0.4.0",
            "build-time": "2026-09-01T10:00:00Z",
            "description": "Counter service",
            "copyright": "Copyright (C) 2026",
            "environment": "production",
            "base-url": "https://counters.example.test",
            "status": "OK",
            "repository-status": "clean",
            "repository-version": "abc1234",
            "uptime-millis": 3600000,
            "uptime": "1 hour",
            "logged-in-session-count": 5,
            "extra-info": {"custom": "value"},
        }
        status = ServerStatus.from_wire(data)
        self.assertEqual(status.name, "example-counters")
        self.assertEqual(status.version, "0.4.0")
        self.assertEqual(status.build_time, "2026-09-01T10:00:00Z")
        self.assertEqual(status.base_url, "https://counters.example.test")
        self.assertEqual(status.uptime_millis, 3600000)
        self.assertEqual(status.logged_in_session_count, 5)
        self.assertEqual(status.extra_info, {"custom": "value"})

        wire_out = status.to_wire()
        self.assertEqual(wire_out["name"], "example-counters")
        self.assertEqual(wire_out["base-url"], "https://counters.example.test")
        self.assertEqual(wire_out["uptime-millis"], 3600000)
        self.assertEqual(wire_out["extra-info"], {"custom": "value"})

    def test_server_status_from_wire_camel_case(self) -> None:
        data = {
            "name": "example-auth",
            "version": "0.5.0",
            "buildTime": "2026-09-01T10:00:00Z",
            "baseUrl": "https://auth.example.test",
            "repositoryStatus": "clean",
            "repositoryVersion": "def5678",
            "uptimeMillis": 120000,
            "loggedInSessionCount": 10,
            "extraInfo": {"region": "eu-west-1"},
        }
        status = ServerStatus.from_wire(data)
        self.assertEqual(status.build_time, "2026-09-01T10:00:00Z")
        self.assertEqual(status.base_url, "https://auth.example.test")
        self.assertEqual(status.repository_status, "clean")
        self.assertEqual(status.repository_version, "def5678")
        self.assertEqual(status.uptime_millis, 120000)
        self.assertEqual(status.logged_in_session_count, 10)
        self.assertEqual(status.extra_info, {"region": "eu-west-1"})

    def test_status_alias(self) -> None:
        self.assertIs(Status, ServerStatus)


class LogEntryTests(unittest.TestCase):
    def test_log_entry_from_wire_timestamp_string(self) -> None:
        data = {
            "message": "User logged in",
            "level": "INFO",
            "timestamp": "2026-09-18T14:00:00Z",
            "name": "auth-service",
        }
        entry = LogEntry.from_wire(data)
        self.assertEqual(entry.message, "User logged in")
        self.assertEqual(entry.level, "INFO")
        self.assertEqual(entry.name, "auth-service")
        self.assertEqual(entry.timestamp, datetime(2026, 9, 18, 14, 0, 0, tzinfo=timezone.utc))
        self.assertEqual(entry.time, "2026-09-18T14:00:00Z")

        wire_out = entry.to_wire()
        self.assertEqual(wire_out["message"], "User logged in")
        self.assertEqual(wire_out["timestamp"], "2026-09-18T14:00:00Z")

    def test_log_entry_from_wire_time_string(self) -> None:
        data = {
            "name": "com.example.auth",
            "level": "WARN",
            "message": "Rate limit reached",
            "time": "2026-09-18T14:05:00Z",
        }
        entry = LogEntry.from_wire(data)
        self.assertEqual(entry.name, "com.example.auth")
        self.assertEqual(entry.level, "WARN")
        self.assertEqual(entry.message, "Rate limit reached")
        self.assertEqual(entry.timestamp, datetime(2026, 9, 18, 14, 5, 0, tzinfo=timezone.utc))

    def test_log_entry_from_wire_arbitrary_time_string(self) -> None:
        data = {
            "message": "Custom time format",
            "level": "DEBUG",
            "time": "14:05:00.123",
        }
        entry = LogEntry.from_wire(data)
        self.assertEqual(entry.message, "Custom time format")
        self.assertEqual(entry.time, "14:05:00.123")


if __name__ == "__main__":
    unittest.main()
