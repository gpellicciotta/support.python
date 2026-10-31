"""Wire models and enum converters for REST services."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Any, Dict, Optional, Tuple

from .dates import format_datetime, parse_datetime


class WireEnum(Enum):
    """Base enum class whose members map to lower-case-with-dashes wire strings."""

    @classmethod
    def from_wire(cls, value: Any) -> Optional[Any]:
        """Convert a wire string representation or existing enum member to an enum instance.

        Matches wire values ignoring casing and underscores/dashes (e.g. ``"read-only"`` or ``"READ_ONLY"``).

        Args:
            value: The wire string or enum instance to convert, or None.

        Returns:
            The matching enum member instance, or None if value was None.

        Raises:
            ValueError: If the value cannot be matched to any member of this enum.
        """
        if value is None:
            return None
        if isinstance(value, cls):
            return value
        key = str(value).strip().lower().replace("_", "-")
        for member in cls:
            if member.value == key or str(member.value).lower().replace("_", "-") == key:
                return member
        raise ValueError(f"Unknown {cls.__name__} value: {value!r}")

    def to_wire(self) -> str:
        """Convert this enum member to its string wire representation.

        Returns:
            String wire value of this enum member.
        """
        return str(self.value)


@dataclass(frozen=True)
class ApiRoute:
    """Represents an API endpoint route metadata record.

    Attributes:
        method: HTTP method (e.g. ``"GET"``, ``"POST"``).
        uri_pattern: URI template pattern (e.g. ``"/users/{id}"``).
        description: Human-readable description of endpoint purpose.
        realms: Tuple of security realms authorized to access this route.
        path: Alias for uri_pattern for backward compatibility.
    """

    method: Optional[str] = None
    uri_pattern: Optional[str] = None
    description: Optional[str] = None
    realms: Tuple[str, ...] = ()
    path: Optional[str] = None

    def __post_init__(self) -> None:
        if self.uri_pattern is None and self.path is not None:
            object.__setattr__(self, "uri_pattern", self.path)
        elif self.path is None and self.uri_pattern is not None:
            object.__setattr__(self, "path", self.uri_pattern)
        if isinstance(self.realms, (list, set)):
            object.__setattr__(self, "realms", tuple(self.realms))

    @classmethod
    def from_wire(cls, data: Dict[str, Any]) -> ApiRoute:
        """Construct an :class:`ApiRoute` instance from wire dictionary data.

        Args:
            data: Dictionary containing route wire fields.

        Returns:
            An instantiated and normalized :class:`ApiRoute`.
        """
        pattern = data.get("uri-pattern") or data.get("uriPattern") or data.get("path")
        raw_realms = data.get("realms") or ()
        return cls(
            method=data.get("method"),
            uri_pattern=pattern,
            description=data.get("description"),
            realms=tuple(raw_realms),
            path=pattern,
        )

    def to_wire(self) -> Dict[str, Any]:
        """Convert this route metadata into a wire dictionary.

        Returns:
            Dictionary with kebab-case keys representing wire data.
        """
        out: Dict[str, Any] = {}
        if self.method is not None:
            out["method"] = self.method
        if self.uri_pattern is not None:
            out["uri-pattern"] = self.uri_pattern
        if self.description is not None:
            out["description"] = self.description
        if self.realms:
            out["realms"] = list(self.realms)
        return out


@dataclass(frozen=True)
class ApiInfo:
    """API metadata containing server API version and route catalog.

    Attributes:
        version: API version string reported by the server.
        api_end_points: Tuple of :class:`ApiRoute` endpoint specifications.
        api_endpoints: Alias for api_end_points for cross-client compatibility.
    """

    version: Optional[str] = None
    api_end_points: Tuple[ApiRoute, ...] = ()
    api_endpoints: Optional[Tuple[ApiRoute, ...]] = None

    def __post_init__(self) -> None:
        if self.api_end_points and self.api_endpoints is None:
            object.__setattr__(self, "api_endpoints", tuple(self.api_end_points))
        elif self.api_endpoints and not self.api_end_points:
            object.__setattr__(self, "api_end_points", tuple(self.api_endpoints))
        elif self.api_endpoints is None:
            object.__setattr__(self, "api_endpoints", ())
            object.__setattr__(self, "api_end_points", tuple(self.api_end_points))
        if isinstance(self.api_end_points, list):
            object.__setattr__(self, "api_end_points", tuple(self.api_end_points))
        if isinstance(self.api_endpoints, list):
            object.__setattr__(self, "api_endpoints", tuple(self.api_endpoints))

    @classmethod
    def from_wire(cls, data: Dict[str, Any]) -> ApiInfo:
        """Construct an :class:`ApiInfo` instance from wire dictionary data.

        Args:
            data: Dictionary containing API metadata wire fields.

        Returns:
            An instantiated :class:`ApiInfo` with parsed endpoint routes.
        """
        raw_routes = (
            data.get("api-end-points") or data.get("apiEndPoints") or data.get("api_endpoints") or data.get("api_end_points") or []
        )
        routes = tuple(ApiRoute.from_wire(r) if isinstance(r, dict) else r for r in raw_routes)
        return cls(
            version=data.get("version"),
            api_end_points=routes,
            api_endpoints=routes,
        )

    def to_wire(self) -> Dict[str, Any]:
        """Convert this API metadata into a wire dictionary.

        Returns:
            Dictionary with kebab-case keys representing wire data.
        """
        out: Dict[str, Any] = {}
        if self.version is not None:
            out["version"] = self.version
        if self.api_end_points:
            out["api-end-points"] = [r.to_wire() if hasattr(r, "to_wire") else r for r in self.api_end_points]
        return out


@dataclass(frozen=True)
class ServerStatus:
    """Server status information model.

    Attributes:
        name: Name of the running service application.
        version: Version of the running service application.
        build_time: Timestamp when the service was compiled or built.
        description: Description of the service application.
        copyright: Copyright notice text.
        environment: Runtime environment name (e.g. ``"production"``, ``"development"``).
        base_url: Canonical base URL where the service is reached.
        status: High-level status indicator (e.g. ``"ONLINE"``, ``"INITIALIZING"``).
        repository_status: Underlying database connection status.
        repository_version: Schema or database migration version.
        uptime_millis: Uptime in milliseconds since service startup.
        uptime: Human-readable formatted uptime string.
        logged_in_session_count: Number of active authenticated user sessions.
        extra_info: Arbitrary dictionary of additional service-specific properties.
    """

    name: Optional[str] = None
    version: Optional[str] = None
    build_time: Optional[str] = None
    description: Optional[str] = None
    copyright: Optional[str] = None
    environment: Optional[str] = None
    base_url: Optional[str] = None
    status: Optional[str] = None
    repository_status: Optional[str] = None
    repository_version: Optional[str] = None
    uptime_millis: Optional[int] = None
    uptime: Optional[str] = None
    logged_in_session_count: Optional[int] = None
    extra_info: Optional[Dict[str, Any]] = None

    @classmethod
    def from_wire(cls, data: Dict[str, Any]) -> ServerStatus:
        """Construct a :class:`ServerStatus` instance from wire dictionary data.

        Args:
            data: Dictionary containing server status wire fields.

        Returns:
            An instantiated :class:`ServerStatus`.
        """
        return cls(
            name=data.get("name"),
            version=data.get("version"),
            build_time=data.get("build-time") or data.get("buildTime"),
            description=data.get("description"),
            copyright=data.get("copyright"),
            environment=data.get("environment"),
            base_url=data.get("base-url") or data.get("baseUrl"),
            status=data.get("status"),
            repository_status=data.get("repository-status") or data.get("repositoryStatus"),
            repository_version=data.get("repository-version") or data.get("repositoryVersion"),
            uptime_millis=data.get("uptime-millis") or data.get("uptimeMillis"),
            uptime=data.get("uptime"),
            logged_in_session_count=data.get("logged-in-session-count") or data.get("loggedInSessionCount"),
            extra_info=data.get("extra-info") or data.get("extraInfo") or {},
        )

    def to_wire(self) -> Dict[str, Any]:
        """Convert this status object into a wire dictionary.

        Returns:
            Dictionary with kebab-case keys representing wire data.
        """
        out: Dict[str, Any] = {}
        if self.name is not None:
            out["name"] = self.name
        if self.version is not None:
            out["version"] = self.version
        if self.build_time is not None:
            out["build-time"] = self.build_time
        if self.description is not None:
            out["description"] = self.description
        if self.copyright is not None:
            out["copyright"] = self.copyright
        if self.environment is not None:
            out["environment"] = self.environment
        if self.base_url is not None:
            out["base-url"] = self.base_url
        if self.status is not None:
            out["status"] = self.status
        if self.repository_status is not None:
            out["repository-status"] = self.repository_status
        if self.repository_version is not None:
            out["repository-version"] = self.repository_version
        if self.uptime_millis is not None:
            out["uptime-millis"] = self.uptime_millis
        if self.uptime is not None:
            out["uptime"] = self.uptime
        if self.logged_in_session_count is not None:
            out["logged-in-session-count"] = self.logged_in_session_count
        if self.extra_info:
            out["extra-info"] = self.extra_info
        return out


#: Backward-compatible alias for :class:`ServerStatus`.
Status = ServerStatus


@dataclass(frozen=True)
class LogEntry:
    """Log entry metadata model returned by server log queries.

    Attributes:
        message: Log message payload text.
        level: Severity level name (e.g. ``"INFO"``, ``"WARN"``, ``"ERROR"``).
        timestamp: Parsed UTC datetime of the log event, if parseable.
        time: Original raw time string from the server.
        name: Logger name or category.
    """

    message: Optional[str] = None
    level: Optional[str] = None
    timestamp: Optional[datetime] = None
    time: Optional[str] = None
    name: Optional[str] = None

    @classmethod
    def from_wire(cls, data: Dict[str, Any]) -> LogEntry:
        """Construct a :class:`LogEntry` instance from wire dictionary data.

        Args:
            data: Dictionary containing log entry wire fields.

        Returns:
            An instantiated :class:`LogEntry`.
        """
        raw_ts = data.get("timestamp") or data.get("time")
        parsed_ts: Optional[datetime] = None
        if isinstance(raw_ts, str):
            try:
                parsed_ts = parse_datetime(raw_ts)
            except (ValueError, TypeError):
                parsed_ts = None
        elif isinstance(raw_ts, datetime):
            parsed_ts = parse_datetime(raw_ts)
        return cls(
            name=data.get("name"),
            level=data.get("level"),
            message=data.get("message"),
            timestamp=parsed_ts,
            time=raw_ts if isinstance(raw_ts, str) else (format_datetime(parsed_ts) if parsed_ts else None),
        )

    def to_wire(self) -> Dict[str, Any]:
        """Convert this log entry into a wire dictionary.

        Returns:
            Dictionary with kebab-case keys representing wire data.
        """
        out: Dict[str, Any] = {}
        if self.name is not None:
            out["name"] = self.name
        if self.level is not None:
            out["level"] = self.level
        if self.message is not None:
            out["message"] = self.message
        if self.timestamp is not None:
            out["timestamp"] = format_datetime(self.timestamp)
        elif self.time is not None:
            out["time"] = self.time
        return out


__all__ = [
    "ApiInfo",
    "ApiRoute",
    "LogEntry",
    "ServerStatus",
    "Status",
    "WireEnum",
]
