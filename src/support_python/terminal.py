"""Terminal and console configuration utilities."""

from __future__ import annotations

import sys


def configure_utf8_output() -> None:
    """Ensure UTF-8 encoding on standard output and standard error streams across platforms.

    Reconfigures ``sys.stdout`` and ``sys.stderr`` using UTF-8 encoding with character
    replacement error handling when running under environments where the default encoding
    is not UTF-8 (such as legacy Windows console environments).

    Returns:
        None.
    """
    for stream_name in ("stdout", "stderr"):
        stream = getattr(sys, stream_name, None)
        if stream is not None and hasattr(stream, "reconfigure"):
            try:
                stream.reconfigure(encoding="utf-8", errors="replace")
            except Exception:
                pass


__all__ = ["configure_utf8_output"]
