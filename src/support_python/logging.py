"""CLI logging utilities compliant with general-guidelines.md's Logging section."""

from __future__ import annotations

import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional, Union


class LogLevel:
    """Standard log levels, where each level indicates an importance.

    More important log levels have higher numeric values.
    """

    #: Disables all logging output.
    NONE: float = float("inf")

    #: Error severity for critical failures and unhandled exceptions (numeric value: 1000).
    ERROR: int = 1000

    #: Warning severity for recoverable issues and potential faults (numeric value: 900).
    WARNING: int = 900

    #: Informational severity for standard operational notifications (numeric value: 800).
    INFO: int = 800

    #: Diagnostic debug severity for internal tracing and troubleshooting (numeric value: 500).
    DEBUG: int = 500

    #: Enables all log levels without filtering.
    ALL: float = float("-inf")

    _NAMES = (
        (NONE, "NONE"),
        (ERROR, "ERROR"),
        (WARNING, "WARNING"),
        (INFO, "INFO"),
        (DEBUG, "DEBUG"),
        (ALL, "ALL"),
    )

    @staticmethod
    def to_string(level: Union[int, float]) -> str:
        """Format a level value as its predefined name, or its number if it has none.

        Args:
            level: Numeric log level value.

        Returns:
            Predefined level name string (e.g. ``"INFO"``) or string representation of the number.
        """
        for value, name in LogLevel._NAMES:
            if level == value:
                return name
        return str(level)

    @staticmethod
    def parse(level_str: str) -> Union[int, float]:
        """Parse a level name (case-insensitive) or integer string into a level value.

        Args:
            level_str: String representation of a log level (e.g. ``"DEBUG"`` or ``"800"``).

        Returns:
            Numeric log level value.

        Raises:
            ValueError: If the string cannot be parsed as a valid level.
        """
        cleaned = level_str.strip().upper()
        if cleaned == "WARN":
            return LogLevel.WARNING
        for value, name in LogLevel._NAMES:
            if name == cleaned:
                return value
        try:
            return int(cleaned)
        except ValueError as exc:
            raise ValueError(f"Value '{level_str}' cannot be parsed as a valid level") from exc


#: Mapping of standard level names to padded 11-character severity tags.
SEVERITY_INDICATORS: dict[str, str] = {
    "ERROR": "**[ERROR]**",
    "WARN": "**[WARN]** ",
    "WARNING": "**[WARN]** ",
    "INFO": "**[INFO]** ",
    "DEBUG": "**[DEBUG]**",
}

#: Mapping of standard level names to numeric threshold values.
LOG_LEVELS: dict[str, int] = {
    "DEBUG": LogLevel.DEBUG,
    "INFO": LogLevel.INFO,
    "WARN": LogLevel.WARNING,
    "WARNING": LogLevel.WARNING,
    "ERROR": LogLevel.ERROR,
}


def format_severity_indicator(level: Optional[str]) -> str:
    """Format severity tag with 5-character uppercase padding per developer guidelines.

    Args:
        level: Raw severity level name string (e.g. ``"INFO"``, ``"WARN"``).

    Returns:
        Formatted severity indicator string (e.g. ``"**[INFO]** "``, ``"**[ERROR]**"``),
        or empty string if level is None or empty.
    """
    if not level:
        return ""
    clean = level.strip().upper()
    if clean in SEVERITY_INDICATORS:
        return SEVERITY_INDICATORS[clean]
    tag = f"**[{clean:<5}]**"
    return f"{tag:<11}"


def format_origin(origin: Optional[str]) -> str:
    """Format optional origin tag as ``<origin>`` per logging guidelines."""
    if not origin or not origin.strip():
        return ""
    orig_clean = origin.strip()
    if not ((orig_clean.startswith("<") and orig_clean.endswith(">")) or (orig_clean.startswith("[") and orig_clean.endswith("]"))):
        orig_clean = f"<{orig_clean}>"
    return orig_clean


def format_utc_timestamp(ts: Optional[datetime] = None) -> str:
    """Format UTC timestamp as ``[YYYY-MM-DD HH:MM:SS]`` per logging guidelines."""
    if ts is None:
        ts = datetime.now(timezone.utc)
    elif ts.tzinfo is None:
        ts = ts.replace(tzinfo=timezone.utc)
    else:
        ts = ts.astimezone(timezone.utc)
    return f"[{ts.strftime('%Y-%m-%d %H:%M:%S')}]"


def format_log_message(
    message: str,
    level: Optional[str] = None,
    origin: Optional[str] = None,
    timestamp: Optional[datetime] = None,
    for_file: bool = True,
    *,
    retain_debug_on_console: bool = False,
) -> str:
    """Format a single or multi-line log message adhering to project logging guidelines.

    In file mode:
        ``[YYYY-MM-DD HH:MM:SS] **[LEVEL]** <origin> First line``
        ``                      Subsequent lines aligned vertically``
    In stdout/stderr mode:
        ``**[LEVEL]** <origin> First line``
        ``Subsequent lines aligned vertically``

    Args:
        message: Log message text (single or multi-line).
        level: Optional severity level name (e.g. ``"INFO"``, ``"ERROR"``).
        origin: Optional component or logger origin identifier (enclosed in angle brackets).
        timestamp: Optional datetime timestamp. Defaults to current local time.
        for_file: Whether to format for log file (includes timestamp and full severity tags).
        retain_debug_on_console: If True, retain ``**[DEBUG]**`` on console streams when ``for_file=False``.

    Returns:
        Formatted log line ending with a newline, or empty string if message is empty.
    """
    if not message and not level and not origin:
        return ""

    ts = timestamp or datetime.now()
    parts: list[str] = []
    if for_file:
        parts.append(f"[{ts.strftime('%Y-%m-%d %H:%M:%S')}]")

    if level:
        lvl_clean = level.strip().upper()
        if for_file:
            parts.append(format_severity_indicator(lvl_clean))
        else:
            # On stdout/stderr, only emit ERROR and WARN indicators; strip other severity indicators
            if lvl_clean in ("WARN", "WARNING", "ERROR") or (retain_debug_on_console and lvl_clean == "DEBUG"):
                parts.append(format_severity_indicator(lvl_clean))

    if origin:
        orig_clean = origin.strip()
        if not (
            (orig_clean.startswith("<") and orig_clean.endswith(">")) or (orig_clean.startswith("[") and orig_clean.endswith("]"))
        ):
            orig_clean = f"<{orig_clean}>"
        parts.append(orig_clean)

    prefix = (" ".join(parts) + " ") if parts else ""
    prefix_len = len(prefix)

    raw_lines = message.splitlines()
    if not raw_lines and message == "":
        return (prefix.rstrip() + "\n") if for_file else "\n"
    if not raw_lines or not any(line.strip() for line in raw_lines):
        return ""

    formatted_lines = [prefix + raw_lines[0]]
    indent = " " * prefix_len
    for line in raw_lines[1:]:
        formatted_lines.append(indent + line if line else "")

    return "\n".join(formatted_lines) + "\n"


def resolve_log_level(explicit_level: Optional[str], debug: bool = False, default: str = "INFO") -> str:
    """Resolve effective log level threshold, where explicit ``--log-level`` overrides ``--debug``."""
    if explicit_level is not None and explicit_level.strip():
        return explicit_level.strip().upper()
    return "DEBUG" if debug else default.strip().upper()


def normalize_log_level(level_str: Optional[str]) -> Optional[str]:
    """Validate and normalize a log level string to its canonical :class:`LogLevel` name."""
    if level_str is None:
        return None
    try:
        return LogLevel.to_string(LogLevel.parse(level_str))
    except ValueError:
        return None


def format_invocation_start(
    tool_name: str,
    version: str,
    action: str,
    details: Optional[Union[str, dict[str, Any]]] = None,
) -> str:
    """Format standard invocation log header containing tool name, version, and requested action."""
    header = f"Starting {tool_name} v{version} (action: {action})"
    if not details:
        return header
    if isinstance(details, dict):
        items = [f"{k}: {v}" for k, v in details.items() if v is not None and v != "" and v != []]
        return f"Starting {tool_name} v{version} (action: {action}, {', '.join(items)})" if items else header
    return f"Starting {tool_name} v{version} (action: {action}, {details})"


def configure_safe_console_encoding() -> None:
    """Configure stdout and stderr stream encoding to UTF-8 and replace unencodable characters if supported."""
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            try:
                stream.reconfigure(encoding="utf-8", errors="replace")
            except Exception:
                pass


def safe_stdout_write(text: str) -> None:
    """Write text to ``sys.stdout``, replacing characters that cannot be encoded by the console encoding."""
    try:
        sys.stdout.write(text)
    except UnicodeEncodeError:
        enc = getattr(sys.stdout, "encoding", None) or "ascii"
        try:
            sys.stdout.write(text.encode(enc, errors="replace").decode(enc))
        except Exception:
            sys.stdout.write(text.encode("ascii", errors="replace").decode("ascii"))


class CliLogger:
    """Logger handling file output, stdout/stderr, verbose progress, and debug filtering.

    Attributes:
        log_path: Path to the log file on disk, if configured.
        verbose: Flag controlling whether informational progress messages print to stdout.
        debug_enabled: Flag controlling whether debug messages are captured to the log file.
        origin: Default origin string prefix for messages emitted by this logger.
        start_time: Monotonic start timestamp used for total duration tracking.
    """

    def __init__(
        self,
        log_path: Optional[Union[Path, str]] = None,
        verbose: bool = False,
        debug: bool = False,
        origin: Optional[str] = None,
        *,
        log_file: Optional[Union[Path, str]] = None,
        log_level: Optional[Union[int, float, str]] = None,
    ) -> None:
        """Initialize the CLI logger.

        Args:
            log_path: Optional path to append log entries to.
            verbose: If True, progress messages are written to stdout in addition to the file.
            debug: If True, debug messages are written to the log file.
            origin: Optional default origin tag for messages.
        """
        chosen_path = log_path if log_path is not None else log_file
        self.log_path = Path(chosen_path) if chosen_path else None
        self.log_file = self.log_path
        self.verbose = verbose
        self.debug_enabled = debug
        self.origin = origin
        self.start_time = time.monotonic()
        self._explicit_level_set = log_level is not None

        if isinstance(log_level, (int, float)):
            self.min_severity: Union[int, float] = log_level
            self.effective_level = LogLevel.to_string(log_level)
        else:
            self.effective_level = resolve_log_level(
                explicit_level=str(log_level) if log_level is not None else None,
                debug=debug,
                default="INFO",
            )
            try:
                self.min_severity = LogLevel.parse(self.effective_level)
            except ValueError:
                self.min_severity = LogLevel.INFO

        self.threshold_val = self.min_severity
        self.debug_enabled = self.min_severity <= LogLevel.DEBUG
        self.debug_flag = debug
        if self.log_path:
            self.log_path.parent.mkdir(parents=True, exist_ok=True)

    def _write_file(self, text: str) -> None:
        if self.log_path and text:
            try:
                with open(self.log_path, "a", encoding="utf-8") as f:
                    f.write(text)
            except OSError:
                pass

    def log(
        self,
        message: str = "",
        level: Optional[str] = None,
        origin: Optional[str] = None,
        timestamp: Optional[datetime] = None,
        to_stdout: bool = True,
        to_stderr: bool = False,
        to_file: bool = True,
    ) -> None:
        """Emit a log message to the log file and to stdout/stderr based on configuration.

        Args:
            message: Message payload text.
            level: Optional severity level name (e.g. ``"INFO"``, ``"DEBUG"``).
            origin: Optional origin override. Defaults to :attr:`origin`.
            timestamp: Optional datetime timestamp. Defaults to current local time.
            to_stdout: Whether to emit on standard output. Defaults to True.
            to_stderr: Whether to emit on standard error. Defaults to False.
        """
        ts = timestamp or datetime.now()
        effective_origin = origin if origin is not None else self.origin
        if not message and not level and not effective_origin:
            return

        lvl_clean = level.strip().upper() if level else ""
        if lvl_clean:
            if lvl_clean == "DEBUG" and not self._explicit_level_set:
                if not self.debug_enabled:
                    return
            else:
                try:
                    msg_severity: Union[int, float] = LogLevel.parse(lvl_clean)
                except ValueError:
                    msg_severity = LogLevel.INFO
                if msg_severity < self.min_severity:
                    return

        # Write to log file if configured
        if to_file:
            file_text = format_log_message(message, level=level, origin=effective_origin, timestamp=ts, for_file=True)
            self._write_file(file_text)

        # Output to stdout/stderr
        stdout_text = format_log_message(
            message,
            level=level,
            origin=effective_origin,
            timestamp=ts,
            for_file=False,
            retain_debug_on_console=(lvl_clean == "DEBUG"),
        )
        if to_stderr:
            sys.stderr.write(stdout_text)
            sys.stderr.flush()
        elif to_stdout:
            safe_stdout_write(stdout_text)
            sys.stdout.flush()

    def emit(self, message: str) -> None:
        """Emit machine-parseable command output directly to stdout and append a timestamped entry to the log file."""
        self.log(message, level=None, origin=None, to_stdout=True, to_file=True)

    def write(self, text: str) -> None:
        """Write raw text string through standard logging."""
        cleaned = text.rstrip("\r\n")
        if cleaned.strip():
            self.log(cleaned, level="INFO")

    def info(self, message: str, origin: Optional[str] = None, to_stdout: bool = True) -> None:
        """Log an informational message.

        Args:
            message: Informational message text.
            origin: Optional origin override.
            to_stdout: Whether to print to stdout. Defaults to True.
        """
        self.log(message, level="INFO", origin=origin, to_stdout=to_stdout)

    def progress(self, message: str, origin: Optional[str] = None) -> None:
        """Log operational progress to file, and to stdout only when verbose is True.

        Args:
            message: Progress description message text.
            origin: Optional origin override.
        """
        self.log(message, level="INFO", origin=origin, to_stdout=self.verbose)

    def warning(self, message: str, origin: Optional[str] = None) -> None:
        """Log a warning message to the log file and to standard error.

        Args:
            message: Warning message text.
            origin: Optional origin override.
        """
        self.log(message, level="WARN", origin=origin, to_stdout=False, to_stderr=True)

    #: Alias of :meth:`warning` matching common client naming conventions.
    warn = warning

    def error(self, message: str, origin: Optional[str] = None) -> None:
        """Log an error message to the log file and to standard error.

        Args:
            message: Error message text.
            origin: Optional origin override.
        """
        self.log(message, level="ERROR", origin=origin, to_stdout=False, to_stderr=True)

    def debug(self, message: str, origin: Optional[str] = None) -> None:
        """Log a diagnostic debug message to the log file when debug logging is enabled.

        Args:
            message: Debug diagnostic message text.
            origin: Optional origin override.
        """
        self.log(message, level="DEBUG", origin=origin, to_stdout=False)

    def debug_msg(self, message: str, origin: Optional[str] = None) -> None:
        """Log a diagnostic debug message to both console and log file when threshold permits."""
        self.log(message, level="DEBUG", origin=origin, to_stdout=True)

    def log_invocation(
        self,
        tool_name: str,
        version: str,
        action: str,
        details: Optional[Union[str, dict[str, Any]]] = None,
    ) -> None:
        """Log standard tool invocation header to the log file."""
        self.log(format_invocation_start(tool_name, version, action, details), level="INFO", to_stdout=False, to_file=True)

    def log_start(
        self,
        name: str,
        version: str,
        argv: list[str],
        config: dict[str, Any],
        origin: Optional[str] = None,
    ) -> None:
        """Log the required start-of-software multi-line message per developer logging guidelines.

        Args:
            name: Application or tool name.
            version: Application version string.
            argv: Full command-line argument list.
            config: Key-value mapping of resolved configuration options.
            origin: Optional origin tag override.
        """
        config_lines = [f"- {k:<24}: {v}" for k, v in config.items()]
        cmd_line = " ".join(argv)
        msg_parts = [
            f"Starting {name} v{version}",
            "with following configuration:",
            f"- Full command line given : {cmd_line}",
            *config_lines,
        ]
        start_msg = "\n".join(msg_parts)
        # Log to file unconditionally; emit on stdout only if verbose
        self.log(start_msg, level="INFO", origin=origin, to_stdout=self.verbose)

    def log_end(
        self,
        summary: Optional[str] = None,
        origin: Optional[str] = None,
    ) -> None:
        """Log the required end-of-software conclusion message with duration per guidelines.

        Args:
            summary: Optional summary text or exit message to append.
            origin: Optional origin tag override.
        """
        duration = time.monotonic() - self.start_time
        duration_str = f"{duration:.2f}s"
        if duration >= 60:
            mins = int(duration // 60)
            secs = duration % 60
            duration_str = f"{mins}m {secs:.1f}s ({duration:.2f}s)"

        summary_text = f" - {summary}" if summary else ""
        end_msg = f"Completed execution in {duration_str}{summary_text}"
        self.log(end_msg, level="INFO", origin=origin, to_stdout=self.verbose)

    def close(self) -> None:
        """Compatibility hook for callers that close logger instances."""


#: Alias for compatibility with ``dev-guidelines`` tool scripts.
ToolLogger = CliLogger

#: Alias for compatibility with ``plan`` CLI logging utilities.
TeeLogger = CliLogger


def log_message(
    msg: str,
    level: str = "INFO",
    log_file: Optional[Union[Path, str]] = None,
    log_level: Optional[str] = None,
    debug: bool = False,
    verbose: bool = False,
    origin: Optional[str] = None,
) -> None:
    """Convenience helper to log a single message matching CLI and logging conventions."""
    logger = CliLogger(log_file=log_file, log_level=log_level, debug=debug, verbose=verbose, origin=origin)
    is_err = level.strip().upper() in ("WARN", "WARNING", "ERROR")
    logger.log(msg, level=level, origin=origin, to_stdout=not is_err, to_stderr=is_err)


def init_cli_logger(
    log_file: Optional[Union[Path, str]],
    log_level: Optional[str] = None,
    debug: bool = False,
) -> Optional[CliLogger]:
    """Initialize a :class:`CliLogger` instance for CLI tool logging if ``log_file`` is specified."""
    configure_safe_console_encoding()
    return CliLogger(log_path=Path(log_file), debug=debug, log_level=log_level) if log_file is not None else None


__all__ = [
    "CliLogger",
    "LOG_LEVELS",
    "LogLevel",
    "SEVERITY_INDICATORS",
    "TeeLogger",
    "ToolLogger",
    "configure_safe_console_encoding",
    "format_invocation_start",
    "format_log_message",
    "format_origin",
    "format_severity_indicator",
    "format_utc_timestamp",
    "init_cli_logger",
    "log_message",
    "normalize_log_level",
    "resolve_log_level",
    "safe_stdout_write",
]
