# REST Clients

These modules provide the shared plumbing for REST API client libraries, all re-exported from `support_python`:
- [net.py](../../src/support_python/net.py): a stdlib-only HTTP transport.
- [errors.py](../../src/support_python/errors.py): a unified exception hierarchy and status-code mapping.
- [dates.py](../../src/support_python/dates.py): wire datetime serialization and parsing.
- [models.py](../../src/support_python/models.py): kebab-case enum converters and server metadata models.

## HTTP transport
`support_python.net` provides a stdlib-only HTTP transport for building REST API clients:
- `Transport` is a protocol, so tests can inject a stub instead of hitting a real server.
- `UrllibTransport` is the default `urllib.request`-based implementation.
- `RawResponse` carries status, headers, and body, plus `.text()`/`.json()` helpers.
- `build_query_string` builds a URL query string.

A non-2xx response is still a normal `RawResponse`.
Only a genuine connectivity failure (unreachable host, timeout, DNS failure, ...) raises `TransportError`.
Callers can map response status codes onto the shared REST error hierarchy:

```python
from support_python import TransportError, UrllibTransport, build_query_string, map_error

transport = UrllibTransport()
try:
    response = transport.request("GET", f"https://api.example.com/things{build_query_string({'q': 'abc'})}")
except TransportError as e:
    ...  # unreachable host, timeout, DNS failure, ...
if response.status_code >= 400:
    raise map_error(response.status_code, response.text(), response.text())
```

## Error hierarchy and status mapping
`support_python.errors` provides a unified exception hierarchy and status-code mapping helper for REST clients:

```python
from support_python import (
    ApiError,
    AuthenticationError,
    ConflictError,
    ForbiddenError,
    NotFoundError,
    RateLimitError,
    ServerError,
    ValidationError,
    map_error,
)

try:
    raise map_error(404, "Target resource not found")
except NotFoundError as e:
    print(f"Not found: {e.message}")
except ApiError as e:
    print(f"API error: {e.status_code} - {e.message}")
```

## Models and wire helpers
`support_python.dates` provides wire datetime serialization and parsing.
`support_python.models` provides kebab-case enum converters and metadata models for REST client libraries:

```python
from support_python import ApiInfo, ApiRoute, ServerStatus, WireEnum, format_datetime, parse_datetime

# Wire datetime helpers (UTC yyyy-MM-dd'T'HH:mm:ss'Z')
parsed_dt = parse_datetime("2026-09-18T14:00:00Z")
wire_date = format_datetime(parsed_dt)


# Base enum mapping to kebab-case wire strings
class TokenType(WireEnum):
    SESSION = "session"
    ONE_TIME_CODE = "one-time-code"


token = TokenType.from_wire("one-time-code")
assert token == TokenType.ONE_TIME_CODE

# Standard server metadata models
route = ApiRoute.from_wire({"method": "GET", "uri-pattern": "/api/status", "description": "Server health"})
info = ApiInfo.from_wire({"version": "1.0.0", "api-end-points": [route.to_wire()]})
status = ServerStatus.from_wire({"name": "service", "status": "OK", "uptime": "2 hours"})
```
