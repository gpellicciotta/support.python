"""Atomic text file replacement and retry-hardened UTF-8 file reading."""

from __future__ import annotations

import os
from pathlib import Path
import stat
import tempfile
import time


def atomic_replace(
    src: Path | str,
    dst: Path | str,
    max_retries: int = 15,
    base_delay: float = 0.01,
) -> None:
    """Atomically replace ``dst`` with ``src``, retrying on transient Windows locks.

    Args:
        src: Temporary or staging file path to move into place.
        dst: Destination file path to replace atomically.
        max_retries: Maximum number of replace attempts before re-raising.
        base_delay: Initial backoff delay in seconds between retries.

    Raises:
        PermissionError: If replacement still fails with ``PermissionError`` after ``max_retries``.
        OSError: If a non-transient error occurs or a transient Windows lock persists.
    """
    src_path = Path(src)
    dst_path = Path(dst)
    try:
        for attempt in range(max_retries):
            try:
                src_path.replace(dst_path)
                return
            except PermissionError:
                if attempt == max_retries - 1:
                    raise
                time.sleep(base_delay * (1.5**attempt))
            except OSError as error:
                winerror = getattr(error, "winerror", None)
                if winerror in (5, 32) and attempt < max_retries - 1:
                    time.sleep(base_delay * (1.5**attempt))
                else:
                    raise
    finally:
        try:
            if src_path.is_file():
                src_path.unlink(missing_ok=True)
        except Exception:
            pass


def read_text_retrying(
    path: Path | str,
    max_retries: int = 10,
    base_delay: float = 0.005,
    errors: str = "replace",
) -> str:
    """Read UTF-8 text from a file that ``atomic_write_text`` may be replacing.

    On Windows, opening a file while a rename replaces it raises ``PermissionError``
    for a moment; retry those. Pass ``errors="strict"`` where undecodable bytes must
    fail rather than be replaced.

    Args:
        path: Path to the UTF-8 text file to read.
        max_retries: Maximum number of read attempts on ``PermissionError``.
        base_delay: Initial backoff delay in seconds between retries.
        errors: Error handling scheme passed to ``Path.read_text``.

    Returns:
        Decoded UTF-8 text content of the file.

    Raises:
        PermissionError: If ``PermissionError`` persists across all attempts.
        OSError: If the file cannot be read for another reason.
        UnicodeDecodeError: If ``errors="strict"`` and the file has invalid UTF-8 bytes.
    """
    target = Path(path)
    for attempt in range(max_retries):
        try:
            return target.read_text(encoding="utf-8", errors=errors)
        except PermissionError:
            if attempt == max_retries - 1:
                raise
            time.sleep(base_delay * (1.5**attempt))
    raise AssertionError("unreachable")


def atomic_write_text(
    path: Path | str,
    content: str,
    newline: str | None = None,
) -> None:
    """Write text to ``path`` through a temporary sibling file, so readers never see a partial file.

    Newlines are translated like ``Path.write_text`` unless ``newline`` says otherwise,
    an existing file keeps its permission bits, and the temporary file is removed on failure.

    Args:
        path: Target file path to create or overwrite atomically.
        content: Text content to write encoded as UTF-8.
        newline: Optional newline translation mode passed to ``tempfile.NamedTemporaryFile``.
    """
    target = Path(path)
    tmp_path: Path | None = None
    try:
        # The fixed-length name leaves out target.name, so a long target name cannot push this sibling past the OS path limit.
        with tempfile.NamedTemporaryFile(
            "w", dir=target.parent, prefix=".", suffix=".tmp", delete=False, encoding="utf-8", newline=newline
        ) as tmp:
            tmp_path = Path(tmp.name)
            tmp.write(content)
        # Temporary files start at mode 0600 on POSIX; keep the group and other bits of the file being replaced.
        try:
            os.chmod(tmp_path, stat.S_IMODE(target.stat().st_mode))
        except FileNotFoundError:
            pass
        atomic_replace(tmp_path, target)
    finally:
        if tmp_path is not None:
            tmp_path.unlink(missing_ok=True)
