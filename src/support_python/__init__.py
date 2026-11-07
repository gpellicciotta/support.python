"""Support library and developer toolkit for Python services and CLI tools."""

from __future__ import annotations

from .capture import (
    DEFAULT_DELAY_SECONDS,
    DEFAULT_DESKTOP_VIEWPORT,
    DEFAULT_MOBILE_VIEWPORT,
    DEFAULT_TIMEOUT_SECONDS,
    MINIMUM_SCREENSHOT_BYTES,
    STANDARD_CAPTURE_EXIT_CODES,
    CaptureAppConfig,
    CaptureResult,
    EmbeddedStaticServer,
    PresetConfig,
    StaticServerManager,
    TourStep,
    ViewCaptureEngine,
    ViewCaptureManager,
    ViewPreset,
    parse_viewport,
    resolve_chrome_path,
    run_capture,
    run_capture_cli,
    run_tour,
)
from .cli import (
    APP_AUTHOR,
    STANDARD_EXIT_CODES,
    build_action_parser,
    format_support_message,
    format_version,
    print_help,
    print_version,
)
from .crypto import (
    DEFAULT_AES_KEY_HEX,
    DEFAULT_TEST_PASSWORD,
    STANDARD_SALT,
    decrypt_property_value,
    get_standard_password_hash,
)
from .dates import (
    DATE_FORMAT,
    format_datetime,
    from_wire_date,
    parse_datetime,
    to_wire_date,
)
from .devops import (
    CloudSqlProxyManager,
    LocalDockerManager,
    LocalMailManager,
    LocalMySqlManager,
    LocalServerManager,
    LocalVerifier,
    resolve_cloud_sql_proxy_bin,
    run_step,
)
from .durations import (
    format_duration,
    format_epoch,
    format_past_epoch,
    format_short_duration,
    parse_date_or_datetime,
    parse_duration_to_seconds,
    parse_iso8601,
)
from .git import (
    DEFAULT_GIT_ENV,
    DEFAULT_GIT_TIMEOUT,
    run_git_command,
    get_repo_root,
    get_head_commit,
    get_current_branch,
    branch_exists,
    parse_worktree_porcelain,
    list_worktrees,
    parse_status_porcelain,
    get_working_tree_status,
    is_git_clean,
    has_remote,
)
from .env import read_env_file
from .errors import (
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
    ValidationError,
    error_for_status,
    is_not_found_message,
    map_error,
)
from .files import (
    atomic_replace,
    atomic_write_text,
    read_text_retrying,
)
from .httpd import (
    EmbeddedStaticServer as HttpServer,
    StaticServerManager as HttpServerManager,
)
from .locking import (
    FileLock,
    Lock,
    LockTimeoutError,
    MySQLLock,
    NullLock,
    RedisLock,
    create_lock,
)
from .logging import (
    CliLogger,
    LogLevel,
    format_log_message,
    format_severity_indicator,
)
from .markdown import (
    TableAlignmentIssue,
    check_table_alignment,
    find_delimiter_pipes,
    format_markdown_table,
    format_markdown_table_block,
    is_table_delimiter_row,
    split_table_row,
    strip_ansi,
    visible_width,
)
from .models import (
    ApiInfo,
    ApiRoute,
    LogEntry,
    ServerStatus,
    Status,
    WireEnum,
)
from .net import (
    RawResponse,
    Transport,
    TransportError,
    UrllibTransport,
    build_query_string,
    is_port_in_use,
)
from .processes import (
    get_process_hierarchy,
    get_process_start_time,
    is_process_alive,
    safe_kill,
    terminate_process,
    terminate_process_tree,
    windows_parent_map,
)
from .ratelimit import TaskRateLimiter
from .sql import (
    TableTransformer,
    anonymize_sql_stream,
    anonymize_sql_string,
    format_sql_row_tuples,
    get_anonymized_user_info,
    parse_sql_row_tuples,
    transform_auth_applications,
    transform_auth_credentials,
    transform_auth_tokens,
    transform_auth_users,
    transform_counters_users,
    transform_counters_webhooks,
)
from .tables import (
    format_table,
    json_serial,
    render_output,
)
from .terminal import configure_utf8_output
from .tokens import (
    FileTokenStore,
    TokenStore,
)
from .version import get_package_version, get_project_version

__version__ = get_package_version("support-python")

__all__ = [
    "__version__",
    # Git
    "DEFAULT_GIT_ENV",
    "DEFAULT_GIT_TIMEOUT",
    "run_git_command",
    "get_repo_root",
    "get_head_commit",
    "get_current_branch",
    "branch_exists",
    "parse_worktree_porcelain",
    "list_worktrees",
    "parse_status_porcelain",
    "get_working_tree_status",
    "is_git_clean",
    "has_remote",
    # Dates
    "DATE_FORMAT",
    "format_datetime",
    "from_wire_date",
    "parse_datetime",
    "to_wire_date",
    # Durations
    "format_duration",
    "format_epoch",
    "format_past_epoch",
    "format_short_duration",
    "parse_date_or_datetime",
    "parse_duration_to_seconds",
    "parse_iso8601",
    # CLI
    "APP_AUTHOR",
    "STANDARD_EXIT_CODES",
    "build_action_parser",
    "format_support_message",
    "format_version",
    "print_help",
    "print_version",
    # Tables
    "format_table",
    "json_serial",
    "render_output",
    # Markdown
    "TableAlignmentIssue",
    "check_table_alignment",
    "find_delimiter_pipes",
    "format_markdown_table",
    "format_markdown_table_block",
    "is_table_delimiter_row",
    "split_table_row",
    "strip_ansi",
    "visible_width",
    # Tokens
    "FileTokenStore",
    "TokenStore",
    # Terminal
    "configure_utf8_output",
    # Logging
    "CliLogger",
    "LogLevel",
    "format_log_message",
    "format_severity_indicator",
    # Net
    "RawResponse",
    "Transport",
    "TransportError",
    "UrllibTransport",
    "build_query_string",
    "is_port_in_use",
    # Processes
    "get_process_hierarchy",
    "get_process_start_time",
    "is_process_alive",
    "safe_kill",
    "terminate_process",
    "terminate_process_tree",
    "windows_parent_map",
    # Rate Limiting
    "TaskRateLimiter",
    # Crypto
    "DEFAULT_AES_KEY_HEX",
    "DEFAULT_TEST_PASSWORD",
    "STANDARD_SALT",
    "decrypt_property_value",
    "get_standard_password_hash",
    # Env
    "read_env_file",
    # Files
    "atomic_replace",
    "atomic_write_text",
    "read_text_retrying",
    # Errors
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
    "ValidationError",
    "error_for_status",
    "is_not_found_message",
    "map_error",
    # Models
    "ApiInfo",
    "ApiRoute",
    "LogEntry",
    "ServerStatus",
    "Status",
    "WireEnum",
    # SQL
    "TableTransformer",
    "anonymize_sql_stream",
    "anonymize_sql_string",
    "format_sql_row_tuples",
    "get_anonymized_user_info",
    "parse_sql_row_tuples",
    "transform_auth_applications",
    "transform_auth_credentials",
    "transform_auth_tokens",
    "transform_auth_users",
    "transform_counters_users",
    "transform_counters_webhooks",
    # Locking
    "FileLock",
    "Lock",
    "LockTimeoutError",
    "MySQLLock",
    "NullLock",
    "RedisLock",
    "create_lock",
    # Httpd
    "EmbeddedStaticServer",
    "HttpServer",
    "HttpServerManager",
    "StaticServerManager",
    # Capture
    "CaptureAppConfig",
    "CaptureResult",
    "DEFAULT_DELAY_SECONDS",
    "DEFAULT_DESKTOP_VIEWPORT",
    "DEFAULT_MOBILE_VIEWPORT",
    "DEFAULT_TIMEOUT_SECONDS",
    "MINIMUM_SCREENSHOT_BYTES",
    "PresetConfig",
    "STANDARD_CAPTURE_EXIT_CODES",
    "TourStep",
    "ViewCaptureEngine",
    "ViewCaptureManager",
    "ViewPreset",
    "parse_viewport",
    "resolve_chrome_path",
    "run_capture",
    "run_capture_cli",
    "run_tour",
    # DevOps
    "CloudSqlProxyManager",
    "LocalDockerManager",
    "LocalMailManager",
    "LocalMySqlManager",
    "LocalServerManager",
    "LocalVerifier",
    "resolve_cloud_sql_proxy_bin",
    "run_step",
    # Version
    "get_package_version",
    "get_project_version",
]
