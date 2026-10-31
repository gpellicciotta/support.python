#!/usr/bin/env python3
"""Shared tool metadata and logging utilities for the scripts in this directory.

Single source of truth for PROJECT_VERSION and COPYRIGHT so every script stays in sync;
import this instead of redeclaring TOOL_VERSION/COPYRIGHT locally in each script.
Provides standardized operational logging with UTC timestamps, 11-character severity padding,
stream routing (stdout for INFO/DEBUG, stderr for WARN/ERROR), and optional file emission.
"""

from __future__ import annotations

from datetime import datetime, timezone
from functools import lru_cache
from pathlib import Path
import re
import subprocess
import sys
from typing import TextIO


def _read_project_version() -> str:
    """Read the version from the pyproject.toml above this directory, the single source of truth."""
    try:
        text = (Path(__file__).resolve().parent.parent / "pyproject.toml").read_text(encoding="utf-8")
    except OSError:
        return "0.0.0+unknown"
    match = re.search(r'^version\s*=\s*"([^"]+)"', text, re.MULTILINE)
    return match.group(1) if match else "0.0.0+unknown"


PROJECT_VERSION = _read_project_version()
COPYRIGHT = "Copyright (c) Giovanni Pellicciotta"

LOG_LEVELS: dict[str, int] = {
    "DEBUG": 10,
    "INFO": 20,
    "WARN": 30,
    "WARNING": 30,
    "ERROR": 40,
}

SEVERITY_INDICATORS: dict[str, str] = {
    "ERROR": "**[ERROR]**",
    "WARN": "**[WARN]** ",
    "WARNING": "**[WARN]** ",
    "INFO": "**[INFO]** ",
    "DEBUG": "**[DEBUG]**",
}


@lru_cache(maxsize=1)
def resolve_build_metadata() -> str:
    """Resolve the short commit hash of this checkout as SemVer build metadata, per
    general-guidelines.md's Pre-release Version Suffix While In Development convention. Falls back to
    'unknown' outside a git checkout or when git is unavailable."""
    try:
        result = subprocess.run(
            ["git", "rev-parse", "--short", "HEAD"],
            cwd=Path(__file__).resolve().parent,
            capture_output=True,
            text=True,
            timeout=5,
        )
        short_hash = result.stdout.strip()
        if result.returncode == 0 and short_hash:
            return short_hash
    except Exception:
        pass
    return "unknown"


def get_full_version(tool_version: str = PROJECT_VERSION) -> str:
    """Return tool_version decorated with build metadata (short commit hash), e.g. '1.10.0-pre+af31b0d'.
    Omits the build metadata entirely (returning bare tool_version) when the hash can't be resolved."""
    metadata = resolve_build_metadata()
    if metadata == "unknown":
        return tool_version
    return f"{tool_version}+{metadata}"


def format_severity_indicator(level: str | None) -> str:
    """Format severity tag with 11-character padding per logging-guidelines.md."""
    if not level:
        return ""
    clean = level.strip().upper()
    if clean in SEVERITY_INDICATORS:
        return SEVERITY_INDICATORS[clean]
    tag = f"**[{clean}]**"
    return f"{tag:<11}"


def format_origin(origin: str | None) -> str:
    """Format optional origin tag as <origin> per logging-guidelines.md."""
    if not origin:
        return ""
    orig_clean = origin.strip()
    if not (orig_clean.startswith("<") and orig_clean.endswith(">")):
        orig_clean = f"<{orig_clean}>"
    return orig_clean


def format_utc_timestamp(ts: datetime | None = None) -> str:
    """Format UTC timestamp as [YYYY-MM-DD HH:MM:SS] per logging-guidelines.md."""
    if ts is None:
        ts = datetime.now(timezone.utc)
    elif ts.tzinfo is None:
        ts = ts.replace(tzinfo=timezone.utc)
    else:
        ts = ts.astimezone(timezone.utc)
    return f"[{ts.strftime('%Y-%m-%d %H:%M:%S')}]"


def format_log_message(
    message: str,
    level: str | None = "INFO",
    origin: str | None = None,
    timestamp: datetime | None = None,
    for_file: bool = True,
) -> str:
    """Format single or multi-line log message per logging guidelines.

    In file mode:
        [YYYY-MM-DD HH:MM:SS] **[LEVEL]**  <origin> First line
                              Subsequent lines aligned vertically
    In stdout/stderr mode:
        **[LEVEL]** <origin> First line
        Subsequent lines aligned vertically
    (INFO omits the severity indicator on stdout).
    """
    if not message and not level and not origin:
        return ""

    parts: list[str] = []
    if for_file:
        parts.append(format_utc_timestamp(timestamp))
        if level:
            parts.append(format_severity_indicator(level))
    else:
        clean_lvl = (level or "").strip().upper()
        if clean_lvl == "DEBUG":
            parts.append(format_severity_indicator("DEBUG"))
        elif clean_lvl in ("WARN", "WARNING"):
            parts.append(format_severity_indicator("WARN"))
        elif clean_lvl == "ERROR":
            parts.append(format_severity_indicator("ERROR"))

    if origin:
        parts.append(format_origin(origin))

    prefix = (" ".join(parts) + " ") if parts else ""
    prefix_len = len(prefix)

    raw_lines = message.splitlines()
    if not raw_lines and message == "":
        return (prefix.rstrip() + "\n") if for_file else "\n"
    if not raw_lines:
        return ""

    formatted_lines = [prefix + raw_lines[0]]
    indent = " " * prefix_len
    for line in raw_lines[1:]:
        formatted_lines.append(indent + line if line else "")

    return "\n".join(formatted_lines) + "\n"


def resolve_log_level(explicit_level: str | None, debug: bool = False, default: str = "INFO") -> str:
    """Resolve effective log level threshold, where explicit --log-level overrides --debug."""
    if explicit_level is not None:
        return explicit_level.strip().upper()
    if debug:
        return "DEBUG"
    return default.strip().upper()


class ToolLogger:
    """Standard operational logger implementing the dev-guidelines logging rules."""

    def __init__(
        self,
        log_file: Path | None = None,
        log_level: str | None = None,
        debug: bool = False,
        verbose: bool = False,
    ) -> None:
        self.log_file = log_file.resolve() if log_file is not None else None
        self.effective_level = resolve_log_level(
            explicit_level=log_level,
            debug=debug,
            default="INFO",
        )
        self.threshold_val = LOG_LEVELS.get(self.effective_level, 20)
        self.verbose = verbose
        self.debug = debug
        self._file: TextIO | None = None

    def log(
        self,
        message: str = "",
        level: str | None = "INFO",
        origin: str | None = None,
        timestamp: datetime | None = None,
        to_console: bool = True,
        to_file: bool = True,
        to_stdout: bool | None = None,
    ) -> None:
        """Write formatted message to console stream and operational log file if threshold met."""
        if not message and not level and not origin:
            return

        if to_stdout is not None:
            to_console = to_stdout

        lvl_clean = (level or "INFO").strip().upper()
        msg_val = LOG_LEVELS.get(lvl_clean, 20)

        # Threshold filtering applies identically to console and log file
        if msg_val < self.threshold_val:
            return

        ts = timestamp or datetime.now(timezone.utc)

        if to_console:
            dest_stream = sys.stderr if lvl_clean in ("WARN", "WARNING", "ERROR") else sys.stdout
            console_text = format_log_message(message, level=level, origin=origin, timestamp=ts, for_file=False)
            if console_text:
                dest_stream.write(console_text)
                dest_stream.flush()

        if to_file and self.log_file is not None:
            if self._file is None:
                self.log_file.parent.mkdir(parents=True, exist_ok=True)
                self._file = self.log_file.open("a", encoding="utf-8", buffering=1)
            file_text = format_log_message(message, level=level, origin=origin, timestamp=ts, for_file=True)
            if file_text:
                self._file.write(file_text)
                self._file.flush()

    def emit(self, message: str) -> None:
        """Emit machine-parseable command output directly to stdout, appending timestamped entry to log file."""
        self.log(message, level=None, origin=None)

    def info(self, message: str, origin: str | None = None) -> None:
        self.log(message, level="INFO", origin=origin)

    def warn(self, message: str, origin: str | None = None) -> None:
        self.log(message, level="WARN", origin=origin)

    def error(self, message: str, origin: str | None = None) -> None:
        self.log(message, level="ERROR", origin=origin)

    def debug_msg(self, message: str, origin: str | None = None) -> None:
        self.log(message, level="DEBUG", origin=origin)

    def close(self) -> None:
        if self._file is not None:
            self._file.close()
            self._file = None


def log_message(
    msg: str,
    level: str = "INFO",
    log_file: Path | None = None,
    log_level: str | None = None,
    debug: bool = False,
    verbose: bool = False,
    origin: str | None = None,
) -> None:
    """Convenience helper to log a single message matching CLI and logging conventions."""
    logger = ToolLogger(log_file=log_file, log_level=log_level, debug=debug, verbose=verbose)
    try:
        logger.log(msg, level=level, origin=origin)
    finally:
        logger.close()


# Alias for backward compatibility
TeeLogger = ToolLogger

from _harness import Action, ToolHarness  # noqa: E402, F401
