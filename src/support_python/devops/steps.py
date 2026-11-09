"""Subprocess step execution and output streaming helpers for DevOps scripts."""

from __future__ import annotations

import shutil
import subprocess
import sys
import sysconfig
from pathlib import Path
from typing import Callable, Mapping, Optional, Sequence, Union

from ..logging import CliLogger

#: Exit code reported when a subprocess executable cannot be found, matching POSIX shell conventions.
EXIT_COMMAND_NOT_FOUND: int = 127


def resolve_executable(name: str) -> Optional[str]:
    """Resolve an executable name, preferring the current Python interpreter's scripts directory over ``PATH``.

    Args:
        name: Executable binary name or filesystem path.

    Returns:
        Resolved path string to the executable if found, or ``None``.
    """
    if name == sys.executable:
        return name
    scripts_dir = sysconfig.get_path("scripts")
    if scripts_dir:
        found = shutil.which(name, path=scripts_dir)
        if found:
            return found
    found = shutil.which(name)
    if found:
        return found
    candidate = Path(name)
    if candidate.is_file():
        return str(candidate)
    return None


def stream_subprocess(
    cmd: Sequence[str],
    cwd: Optional[Union[Path, str]] = None,
    env: Optional[Mapping[str, str]] = None,
    logger: Optional[CliLogger] = None,
    origin: Optional[str] = None,
    on_line: Optional[Callable[[str], None]] = None,
    *,
    agent_tag: Optional[str] = None,
) -> int:
    """Run a child process, streaming merged stdout and stderr line by line to a :class:`CliLogger`.

    Starts the child with ``stdin=subprocess.DEVNULL``, logs the full command line and PID before any
    child output, skips blank lines when logging, invokes ``on_line`` (if provided) on every raw line
    without letting callback exceptions abort streaming, and terminates (then kills after 5 seconds)
    the child on :exc:`KeyboardInterrupt` before re-raising.

    Args:
        cmd: Command-line argument sequence to execute.
        cwd: Optional working directory for the child process.
        env: Optional environment variable mapping for the child process.
        logger: Optional :class:`~support_python.logging.CliLogger` receiving the streamed lines.
        origin: Optional origin tag passed to ``logger.log`` and ``logger.error``.
        on_line: Optional per-line callback invoked with each raw line read from the child stream.
        agent_tag: Optional alias for ``origin`` kept for caller compatibility.

    Returns:
        The child process exit code, :data:`EXIT_COMMAND_NOT_FOUND` (127) if the executable cannot be
        resolved, or ``1`` if launching fails with :exc:`OSError`.
    """
    argv = [str(arg) for arg in cmd]
    effective_origin = origin if origin is not None else agent_tag
    active_logger = logger if logger is not None else CliLogger(origin=effective_origin)

    if not argv:
        active_logger.error("Empty command argument list passed to stream_subprocess", origin=effective_origin)
        return EXIT_COMMAND_NOT_FOUND

    executable = resolve_executable(argv[0])
    if executable is None:
        active_logger.error(f"Executable not found on PATH: {argv[0]}", origin=effective_origin)
        return EXIT_COMMAND_NOT_FOUND

    full_cmd = [executable, *argv[1:]]
    try:
        process = subprocess.Popen(
            full_cmd,
            cwd=str(cwd) if cwd is not None else None,
            env=dict(env) if env is not None else None,
            stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            encoding="utf-8",
            errors="replace",
            bufsize=1,
        )
    except FileNotFoundError:
        active_logger.error(f"Executable not found on PATH: {argv[0]}", origin=effective_origin)
        return EXIT_COMMAND_NOT_FOUND
    except OSError as exc:
        active_logger.error(f"Failed to start {argv[0]}: {exc}", origin=effective_origin)
        return 1

    active_logger.log(f"Command: {subprocess.list2cmdline(argv)}", level="INFO", origin=effective_origin)
    active_logger.log(f"Process ID: {process.pid}", level="INFO", origin=effective_origin)
    assert process.stdout is not None

    try:
        for line in iter(process.stdout.readline, ""):
            if on_line is not None:
                try:
                    on_line(line)
                except Exception:
                    pass
            cleaned = line.rstrip("\r\n")
            if cleaned.strip():
                active_logger.log(cleaned, level="INFO", origin=effective_origin)
        return process.wait()
    except KeyboardInterrupt:
        active_logger.log(
            "\n[Interrupt received. Terminating child process...]",
            level="INFO",
            origin=effective_origin,
        )
        process.terminate()
        try:
            process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait()
        raise
    finally:
        if process.stdout and not process.stdout.closed:
            process.stdout.close()


def run_step_command(
    argv: Sequence[str],
    cwd: Optional[Union[Path, str]] = None,
    logger: Optional[CliLogger] = None,
    *,
    origin: Optional[str] = None,
    on_line: Optional[Callable[[str], None]] = None,
) -> int:
    """Run one step command and stream its output to ``logger``, returning the child exit code.

    Args:
        argv: Command-line argument sequence to execute.
        cwd: Optional working directory for the child process.
        logger: Optional :class:`~support_python.logging.CliLogger` receiving output and error messages.
        origin: Optional origin tag override.
        on_line: Optional per-line callback invoked on each raw line.

    Returns:
        The child process exit code, or :data:`EXIT_COMMAND_NOT_FOUND` (127) when the executable is missing.
    """
    return stream_subprocess(argv, cwd=cwd, logger=logger, origin=origin, on_line=on_line)


def run_step(
    description: str,
    args: Sequence[str],
    cwd: Optional[Union[Path, str]] = None,
    logger: Optional[CliLogger] = None,
    *,
    stream: bool = False,
    origin: Optional[str] = None,
    on_line: Optional[Callable[[str], None]] = None,
) -> bool:
    """Run one step of a multi-step ops script (e.g. bootstrap, deploy), printing its outcome.

    Prints a banner and the step's own output unconditionally, so progress stays visible during a
    long-running script even without ``--verbose``. When given, ``logger`` additionally records the step
    (and any failure) through the caller's own ``CliLogger`` (file output, verbose stdout, etc.).
    When ``stream=True``, runs the child via :func:`stream_subprocess` so merged output is streamed
    line by line through ``logger``.

    Args:
        description: Human-readable description of the operation being executed.
        args: Command-line arguments list to execute.
        cwd: Optional working directory for the subprocess. Defaults to current directory.
        logger: Optional :class:`~support_python.logging.CliLogger` for recording progress.
        stream: If True, stream child output line by line via :func:`stream_subprocess`.
        origin: Optional origin tag when ``stream=True``.
        on_line: Optional per-line callback when ``stream=True``.

    Returns:
        True if the subprocess exited with return code 0, False otherwise.
    """
    print(f"\n[*] {description}", flush=True)
    print("=" * 60, flush=True)
    if logger:
        logger.progress(description)

    if stream:
        returncode = stream_subprocess(
            args,
            cwd=cwd,
            logger=logger,
            origin=origin,
            on_line=on_line,
        )
    else:
        result = subprocess.run(list(args), cwd=str(cwd) if cwd else None, check=False)
        returncode = result.returncode

    if returncode != 0:
        failure_msg = f"{description} failed (exit code {returncode})"
        print(f"[!] {failure_msg}", flush=True)
        if logger:
            logger.warning(failure_msg)
        return False

    return True


__all__ = [
    "EXIT_COMMAND_NOT_FOUND",
    "resolve_executable",
    "stream_subprocess",
    "run_step_command",
    "run_step",
]
