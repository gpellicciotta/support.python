"""Typed REST client error hierarchy and HTTP status code mapping helpers.

Provides a unified exception hierarchy for REST API clients, standardizing error shapes.

Includes:
- :class:`ApiError`: Base exception carrying HTTP status code, message, and optional response body.
- Subclasses: :class:`AuthenticationError` (401), :class:`ForbiddenError` (403),
  :class:`ValidationError` (400), :class:`NotFoundError` (404 or 400 heuristic),
  :class:`ConflictError` (409), :class:`RateLimitError` (429), and :class:`ServerError` (5xx).
- Aliases: ``ServiceError`` and ``HttpApiError`` alias :class:`ApiError` for cross-client compatibility.
- :class:`NetworkError`: Alias for :class:`~support_python.net.TransportError` for genuine network failures.
- :func:`map_error` and :func:`error_for_status`: Map HTTP status codes and response messages to typed exceptions.
"""

from __future__ import annotations

import re
from typing import Iterable, Optional, Pattern, Union

from .net import TransportError

__all__ = [
    "ApiError",
    "AuthenticationError",
    "ConflictError",
    "DEFAULT_NOT_FOUND_PATTERNS",
    "ForbiddenError",
    "HttpApiError",
    "NetworkError",
    "NotFoundError",
    "RateLimitError",
    "ServerError",
    "ServiceError",
    "TransportError",
    "ValidationError",
    "error_for_status",
    "is_not_found_message",
    "map_error",
]

#: Standard regex patterns used across services to identify "not found" errors
#: returned with HTTP 400 (backend convention of returning 400 with a descriptive message).
DEFAULT_NOT_FOUND_PATTERNS: tuple[Pattern[str], ...] = (
    re.compile(r"there is no\b", re.IGNORECASE),
    re.compile(r"no .* with id", re.IGNORECASE),
    re.compile(r"invalid.*id", re.IGNORECASE),
    re.compile(r"not found", re.IGNORECASE),
    re.compile(r"does not exist", re.IGNORECASE),
    re.compile(r"is not valid", re.IGNORECASE),
)


class ApiError(Exception):
    """Base exception for all non-2xx HTTP responses returned by a REST API.

    Supports multiple constructor calling conventions:
    - ``ApiError(status_code, message, body=None)`` (status-first convention)
    - ``ApiError(message, status=status_code)`` (message-first ServiceError convention)

    Attributes:
        status_code: HTTP status code integer (e.g. 404, 500).
        status: Alias for :attr:`status_code`.
        message: Human-readable error description string.
        body: Optional raw or decoded response body text from the server.
    """

    def __init__(
        self,
        arg1: Union[int, str] = 0,
        arg2: Optional[Union[int, str]] = None,
        body: Optional[str] = None,
        *,
        status_code: Optional[int] = None,
        status: Optional[int] = None,
        message: Optional[str] = None,
    ) -> None:
        """Initialize an ApiError instance with status code, message, and optional response body.

        Args:
            arg1: HTTP status code integer, or error message string if positional style.
            arg2: Error message string (if arg1 was integer) or status code (if arg1 was string).
            body: Optional raw text response body returned by the server.
            status_code: Keyword-only HTTP status code override.
            status: Keyword-only alias for status_code.
            message: Keyword-only error message override.
        """
        code = 0
        msg = ""

        if isinstance(arg1, int):
            code = arg1
            msg = str(arg2 or "")
        elif isinstance(arg1, str):
            if isinstance(arg2, int):
                code = arg2
                msg = arg1
            else:
                msg = arg1

        if status_code is not None:
            code = status_code
        elif status is not None:
            code = status

        if message is not None and not msg:
            msg = message

        self.status_code: int = int(code)
        self.status: int = self.status_code
        self.message: str = msg
        self.body: Optional[str] = body

        if self.status_code and self.message:
            display_str = (
                self.message if self.message.startswith(f"HTTP {self.status_code}") else f"HTTP {self.status_code}: {self.message}"
            )
        elif self.status_code:
            display_str = f"HTTP {self.status_code}"
        else:
            display_str = self.message

        super().__init__(display_str)

    def __repr__(self) -> str:
        """Return representation of the error instance.

        Returns:
            String representation showing class name, status code, message, and body.
        """
        return f"{self.__class__.__name__}(status_code={self.status_code!r}, message={self.message!r}, body={self.body!r})"


#: Backward-compatible alias for :class:`ApiError` matching auth client convention.
ServiceError = ApiError

#: Backward-compatible alias for :class:`ApiError`.
HttpApiError = ApiError


class AuthenticationError(ApiError):
    """Raised for HTTP 401 Unauthorized responses (missing, invalid, or expired credentials)."""


class ForbiddenError(ApiError):
    """Raised for HTTP 403 Forbidden responses (insufficient privileges or realms)."""


class ConflictError(ApiError):
    """Raised for HTTP 409 Conflict responses (duplicate unique keys or state collision)."""


class ValidationError(ApiError):
    """Raised for HTTP 400 Bad Request responses caused by invalid client parameters."""


class NotFoundError(ValidationError):
    """Raised for HTTP 404 or HTTP 400 responses matching missing-resource heuristics."""


class RateLimitError(ApiError):
    """Raised for HTTP 429 Too Many Requests responses when rate limits are exceeded."""


class ServerError(ApiError):
    """Raised for HTTP 5xx responses indicating unexpected server-side failures."""


#: Re-export TransportError under NetworkError name for counters client compatibility.
NetworkError = TransportError


def is_not_found_message(
    message: Optional[str],
    patterns: Optional[Iterable[Pattern[str]]] = None,
) -> bool:
    """Check if a response message indicates a missing resource based on regex heuristics.

    Args:
        message: The response message string to check, or None.
        patterns: Optional collection of compiled regular expressions.
            Defaults to :const:`DEFAULT_NOT_FOUND_PATTERNS`.

    Returns:
        True if the message matches any of the not-found patterns, False otherwise.
    """
    if not message:
        return False
    active_patterns = patterns if patterns is not None else DEFAULT_NOT_FOUND_PATTERNS
    return any(p.search(message) for p in active_patterns)


def map_error(
    status_code: Optional[int] = None,
    message: Optional[str] = None,
    body: Optional[str] = None,
    *,
    status: Optional[int] = None,
    not_found_patterns: Optional[Iterable[Pattern[str]]] = None,
) -> ApiError:
    """Map an HTTP status code, message, and optional response body to a typed :class:`ApiError` subclass.

    Handles standard REST status codes (401, 403, 404, 409, 429, 5xx) and classifies 400 responses
    as :class:`NotFoundError` when message text matches not-found heuristics, or :class:`ValidationError`
    otherwise.

    Args:
        status_code: HTTP response status code integer.
        message: Error message string returned by server or client.
        body: Optional raw response body string.
        status: Keyword-only alias for status_code.
        not_found_patterns: Optional collection of regex patterns to identify not-found messages on 400.

    Returns:
        Appropriate :class:`ApiError` subclass instance representing the HTTP response.
    """
    code = status_code if status_code is not None else (status if status is not None else 0)
    text = message or ""

    if code == 401:
        return AuthenticationError(code, text or "authentication failed", body)
    if code == 403:
        return ForbiddenError(code, text or "forbidden", body)
    if code == 404:
        return NotFoundError(code, text or "not found", body)
    if code == 409:
        return ConflictError(code, text or "conflict", body)
    if code == 429:
        return RateLimitError(code, text or "too many requests", body)
    if code == 400:
        if is_not_found_message(text, not_found_patterns):
            return NotFoundError(code, text or "not found", body)
        return ValidationError(code, text or "bad request", body)
    if 500 <= code < 600:
        return ServerError(code, text or f"server error {code}", body)
    return ApiError(code, text or f"request failed with status {code}", body)


#: Backward-compatible alias for :func:`map_error` matching auth client convention.
error_for_status = map_error
