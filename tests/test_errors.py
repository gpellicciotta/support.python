import re

import support_python
import support_python.errors as errors_module
from support_python import (
    DEFAULT_NOT_FOUND_PATTERNS,
    ApiError,
    AuthenticationError,
    ConflictError,
    ForbiddenError,
    HttpApiError,
    NetworkError,
    NotFoundError,
    RateLimitError,
    ServerError,
    ServiceError,
    TransportError,
    ValidationError,
    error_for_status,
    is_not_found_message,
    map_error,
)


def test_api_error_initialization_counters_style():
    err = ApiError(404, "Item not found", body='{"error": "none"}')
    assert err.status_code == 404
    assert err.status == 404
    assert err.message == "Item not found"
    assert err.body == '{"error": "none"}'
    assert str(err) == "HTTP 404: Item not found"
    assert "ApiError(status_code=404, message='Item not found', body='{\"error\": \"none\"}')" in repr(err)


def test_api_error_initialization_auth_service_error_style():
    err = ServiceError("Authentication failed", status=401)
    assert err.status_code == 401
    assert err.status == 401
    assert err.message == "Authentication failed"
    assert str(err) == "HTTP 401: Authentication failed"

    err2 = ServiceError("Authentication failed", 401)
    assert err2.status_code == 401
    assert err2.status == 401
    assert err2.message == "Authentication failed"


def test_api_error_message_formatting_edge_cases():
    err_no_code = ApiError("Something broke")
    assert err_no_code.status_code == 0
    assert err_no_code.message == "Something broke"
    assert str(err_no_code) == "Something broke"

    err_code_only = ApiError(500)
    assert err_code_only.status_code == 500
    assert err_code_only.message == ""
    assert str(err_code_only) == "HTTP 500"

    err_prefixed = ApiError(400, "HTTP 400: already formatted")
    assert str(err_prefixed) == "HTTP 400: already formatted"

    err_empty = ApiError()
    assert err_empty.status_code == 0
    assert err_empty.message == ""
    assert str(err_empty) == ""


def test_error_hierarchy_and_subclasses():
    assert issubclass(ServiceError, ApiError)
    assert issubclass(HttpApiError, ApiError)
    assert issubclass(AuthenticationError, ApiError)
    assert issubclass(ForbiddenError, ApiError)
    assert issubclass(ValidationError, ApiError)
    assert issubclass(NotFoundError, ValidationError)
    assert issubclass(NotFoundError, ApiError)
    assert issubclass(ConflictError, ApiError)
    assert issubclass(RateLimitError, ApiError)
    assert issubclass(ServerError, ApiError)
    assert NetworkError is TransportError or issubclass(NetworkError, TransportError)


def test_is_not_found_message_heuristics():
    assert len(DEFAULT_NOT_FOUND_PATTERNS) >= 5
    assert is_not_found_message("There is no counter with id 123")
    assert is_not_found_message("no user with id 'alice'")
    assert is_not_found_message("Invalid food item ID")
    assert is_not_found_message("Target resource not found")
    assert is_not_found_message("The specified token does not exist")
    assert is_not_found_message("ID is not valid")

    assert not is_not_found_message("Malformed JSON payload")
    assert not is_not_found_message("Field 'title' is required")
    assert not is_not_found_message("")
    assert not is_not_found_message(None)


def test_is_not_found_message_custom_patterns():
    custom = [re.compile(r"missing\s+entity", re.IGNORECASE)]
    assert is_not_found_message("Missing entity in request", patterns=custom)
    assert not is_not_found_message("There is no user with id 123", patterns=custom)


def test_map_error_standard_statuses():
    err_401 = map_error(401, "Bad token", '{"status": "error"}')
    assert isinstance(err_401, AuthenticationError)
    assert err_401.status_code == 401
    assert err_401.message == "Bad token"
    assert err_401.body == '{"status": "error"}'

    err_403 = map_error(403)
    assert isinstance(err_403, ForbiddenError)
    assert err_403.status_code == 403
    assert err_403.message == "forbidden"

    err_404 = map_error(404)
    assert isinstance(err_404, NotFoundError)
    assert err_404.status_code == 404
    assert err_404.message == "not found"

    err_409 = map_error(409, "Name collision")
    assert isinstance(err_409, ConflictError)
    assert err_409.status_code == 409
    assert err_409.message == "Name collision"

    err_429 = map_error(429)
    assert isinstance(err_429, RateLimitError)
    assert err_429.status_code == 429

    err_500 = map_error(500, "Database crashed")
    assert isinstance(err_500, ServerError)
    assert err_500.status_code == 500

    err_503 = map_error(503)
    assert isinstance(err_503, ServerError)
    assert err_503.status_code == 503

    err_other = map_error(418, "I'm a teapot")
    assert type(err_other) is ApiError
    assert err_other.status_code == 418
    assert err_other.message == "I'm a teapot"


def test_map_error_400_heuristics():
    err_not_found_heuristic = map_error(400, "There is no counter with ID '999'")
    assert isinstance(err_not_found_heuristic, NotFoundError)
    assert isinstance(err_not_found_heuristic, ValidationError)
    assert err_not_found_heuristic.status_code == 400

    err_validation = map_error(400, "Field 'count' must be positive")
    assert type(err_validation) is ValidationError
    assert err_validation.status_code == 400


def test_error_for_status_alias():
    err = error_for_status(401, "Authentication failed")
    assert isinstance(err, AuthenticationError)
    assert err.status_code == 401

    err_named_kwarg = map_error(status=409, message="Conflict")
    assert isinstance(err_named_kwarg, ConflictError)
    assert err_named_kwarg.status_code == 409


def test_module_all_exports():
    for name in errors_module.__all__:
        assert hasattr(errors_module, name)
        assert hasattr(support_python, name)
