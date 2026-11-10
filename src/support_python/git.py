"""Git execution and read-only repository queries.

Query helpers return None on execution failure, including missing Git, timeouts,
and invalid repositories. Boolean helpers return False only for confirmed negative
results. The runner raises errors and can execute mutating commands explicitly.
Porcelain parsers accept newline and NUL-delimited output; prefer NUL output for
paths containing quotes, newlines, or Git escape sequences.
"""

from __future__ import annotations

import os
from pathlib import Path
import re
import subprocess
import sys

DEFAULT_GIT_TIMEOUT: float = 10.0
DEFAULT_GIT_ENV: dict[str, str] = {
    "GIT_OPTIONAL_LOCKS": "0",
    "GIT_NO_LAZY_FETCH": "1",
    "GIT_TERMINAL_PROMPT": "0",
}


def _has_console() -> bool:
    """Return whether this process is attached to a console, visible or hidden.

    A hidden console from CREATE_NO_WINDOW has no window handle, so GetConsoleWindow cannot
    detect it. GetConsoleProcessList returns 0 only when the process has no console at all.
    The check runs on every call because a process can attach to or free its console.
    """
    if sys.platform != "win32":
        return True
    try:
        import ctypes

        return ctypes.windll.kernel32.GetConsoleProcessList((ctypes.c_uint * 1)(), 1) > 0
    except (AttributeError, OSError):
        return True


def _git_creationflags() -> int:
    """Return subprocess creation flags that keep git from opening a console window.

    Only a Windows process with no console at all makes its children open new visible consoles.
    A child that inherits any console, even a hidden one, opens no window, and CREATE_NO_WINDOW
    would give it a second, slower console. The flag is therefore applied only without a console.

    Returns:
        CREATE_NO_WINDOW on Windows when this process has no console, else 0.
    """
    if sys.platform == "win32" and not _has_console():
        return getattr(subprocess, "CREATE_NO_WINDOW", 0x08000000)
    return 0


def run_git_command(
    cwd: Path | str,
    *args: str,
    timeout: float = DEFAULT_GIT_TIMEOUT,
    allowed_returncodes: tuple[int, ...] = (0,),
    env: dict[str, str] | None = None,
    no_optional_locks: bool = True,
    input_data: str | None = None,
) -> subprocess.CompletedProcess[str]:
    """Execute a git command with timeout and safe environment protections.

    Args:
        cwd: Working directory for git command execution.
        *args: Git command-line argument tokens.
        timeout: Maximum execution time in seconds.
        allowed_returncodes: Tuple of permitted exit codes (default: (0,)).
        env: Optional environment dictionary override or extension.
        no_optional_locks: Whether to prepend '--no-optional-locks'.
        input_data: Optional stdin string payload passed to the git process.

    Returns:
        subprocess.CompletedProcess object containing stdout/stderr.

    Raises:
        subprocess.CalledProcessError: If exit code is not in allowed_returncodes.
        subprocess.TimeoutExpired: If git execution exceeds timeout.
        OSError: If git binary is not found or cannot execute.
    """
    merged_env = {**os.environ, **DEFAULT_GIT_ENV, **(env or {})}
    cmd = ["git"]
    if no_optional_locks:
        cmd.append("--no-optional-locks")
    cmd.extend(args)

    result = subprocess.run(
        cmd,
        cwd=cwd,
        env=merged_env,
        capture_output=True,
        encoding="utf-8",
        errors="replace",
        timeout=timeout,
        shell=False,
        input=input_data,
        creationflags=_git_creationflags(),
    )
    if result.returncode not in allowed_returncodes:
        raise subprocess.CalledProcessError(result.returncode, cmd, output=result.stdout, stderr=result.stderr)
    return result


def get_repo_root(cwd: Path | str, timeout: float = DEFAULT_GIT_TIMEOUT) -> Path | None:
    """Resolve the top-level repository directory for a path.

    Args:
        cwd: Working directory to inspect.
        timeout: Command timeout in seconds.

    Returns:
        Resolved Path to top-level repository root, or None if not inside a git repository.
    """
    try:
        res = run_git_command(cwd, "rev-parse", "--show-toplevel", timeout=timeout)
        root = res.stdout.strip()
        return Path(root).resolve() if root else None
    except (OSError, subprocess.SubprocessError):
        return None


def get_head_commit(cwd: Path | str, *, short: bool = False, timeout: float = DEFAULT_GIT_TIMEOUT) -> str | None:
    """Retrieve the current HEAD commit hash for a repository.

    Args:
        cwd: Working directory of the repository.
        short: If True, return the short commit hash.
        timeout: Command timeout in seconds.

    Returns:
        Commit hash string, or None on failure.
    """
    try:
        args = ["rev-parse", "--short", "HEAD"] if short else ["rev-parse", "--verify", "HEAD"]
        res = run_git_command(cwd, *args, timeout=timeout)
        commit = res.stdout.strip()
        return commit if commit else None
    except (OSError, subprocess.SubprocessError):
        return None


def get_current_branch(cwd: Path | str, timeout: float = DEFAULT_GIT_TIMEOUT) -> str | None:
    """Retrieve the current symbolic branch name, or '(detached)' if in detached HEAD state.

    Args:
        cwd: Working directory of the repository.
        timeout: Command timeout in seconds.

    Returns:
        Branch name string, '(detached)', or None on execution failure.
    """
    try:
        res = run_git_command(
            cwd,
            "symbolic-ref",
            "--quiet",
            "--short",
            "HEAD",
            timeout=timeout,
            allowed_returncodes=(0, 1),
        )
        if res.returncode == 0:
            branch = res.stdout.strip()
            return branch if branch else "(detached)"
        return "(detached)"
    except (OSError, subprocess.SubprocessError):
        return None


def branch_exists(cwd: Path | str, branch_name: str, timeout: float = DEFAULT_GIT_TIMEOUT) -> bool | None:
    """Check whether a local branch exists in the repository.

    Args:
        cwd: Working directory of the repository.
        branch_name: Name of the local branch (without 'refs/heads/' prefix).
        timeout: Command timeout in seconds.

    Returns:
        True if branch exists, False if confirmed absent, or None on query failure.
    """
    try:
        res = run_git_command(
            cwd,
            "for-each-ref",
            "--format=%(refname)",
            f"refs/heads/{branch_name}",
            timeout=timeout,
        )
        return f"refs/heads/{branch_name}" in res.stdout.splitlines()
    except (OSError, subprocess.SubprocessError):
        return None


def parse_worktree_porcelain(raw: str) -> list[dict[str, str]]:
    """Parse output from 'git worktree list --porcelain' (both newline and null-delimited).

    Args:
        raw: Raw stdout text from 'git worktree list --porcelain' or '... -z'.

    Returns:
        List of parsed worktree dictionaries.
    """
    records: list[dict[str, str]] = []
    record: dict[str, str] = {}

    if "\0" in raw:
        items = raw.split("\0")
    else:
        items = raw.splitlines()

    for item in items:
        if not item:
            if record:
                records.append(record)
                record = {}
            continue
        key, _, value = item.partition(" ")
        record[key] = value

    if record:
        records.append(record)
    return records


def list_worktrees(cwd: Path | str, timeout: float = DEFAULT_GIT_TIMEOUT) -> list[dict[str, str]] | None:
    """List all registered worktrees for a repository.

    Args:
        cwd: Working directory of the repository.
        timeout: Command timeout in seconds.

    Returns:
        List of worktree dictionaries, or None on failure.
    """
    try:
        res = run_git_command(cwd, "worktree", "list", "--porcelain", "-z", timeout=timeout)
        return parse_worktree_porcelain(res.stdout)
    except (OSError, subprocess.SubprocessError):
        return None


def parse_status_porcelain(raw: str) -> list[dict[str, str]]:
    """Parse porcelain v1 git status output (both newline and -z null-delimited).

    Args:
        raw: Raw porcelain status output from git status.

    Returns:
        List of status dictionaries with 'status', 'path', and optional 'original_path'.
    """
    files: list[dict[str, str]] = []
    if "\0" in raw:
        tokens = iter(raw.split("\0"))
        for token in tokens:
            if not token:
                continue
            entry = {"status": token[:2], "path": token[3:]}
            if "R" in token[:2] or "C" in token[:2]:
                entry["original_path"] = next(tokens, "")
            files.append(entry)
    else:
        for line in raw.splitlines():
            line = line.rstrip("\r\n")
            if len(line) >= 3:
                status_code = line[:2]
                path_part = line[3:].strip()
                if ("R" in status_code or "C" in status_code) and " -> " in path_part:
                    orig, _, target = path_part.partition(" -> ")
                    files.append({"status": status_code, "path": target.strip('"'), "original_path": orig.strip('"')})
                else:
                    files.append({"status": status_code, "path": path_part.strip('"')})
    return files


def get_working_tree_status(
    cwd: Path | str,
    *,
    untracked: bool = True,
    timeout: float = DEFAULT_GIT_TIMEOUT,
) -> list[dict[str, str]] | None:
    """Query modified, staged, and untracked files in a working tree.

    Args:
        cwd: Working directory of the repository.
        untracked: Whether to include untracked files.
        timeout: Command timeout in seconds.

    Returns:
        List of status dictionaries, or None on failure.
    """
    try:
        untracked_arg = "--untracked-files=all" if untracked else "--untracked-files=no"
        res = run_git_command(
            cwd,
            "-c",
            "core.fsmonitor=false",
            "status",
            "--porcelain=v1",
            "-z",
            untracked_arg,
            timeout=timeout,
        )
        return parse_status_porcelain(res.stdout)
    except (OSError, subprocess.SubprocessError):
        return None


def is_git_clean(cwd: Path | str, timeout: float = DEFAULT_GIT_TIMEOUT) -> bool | None:
    """Check whether a working tree has no uncommitted changes or untracked files.

    Args:
        cwd: Working directory to inspect.
        timeout: Command timeout in seconds.

    Returns:
        True if clean, False if dirty, or None on query failure.
    """
    status = get_working_tree_status(cwd, untracked=True, timeout=timeout)
    return None if status is None else len(status) == 0


def has_remote(cwd: Path | str, remote: str = "origin", timeout: float = DEFAULT_GIT_TIMEOUT) -> bool | None:
    """Check whether a given git remote is configured in the repository.

    Args:
        cwd: Working directory of the repository.
        remote: Remote name to look for (default: 'origin').
        timeout: Command timeout in seconds.

    Returns:
        True if configured, False if absent, or None on query failure.
    """
    try:
        res = run_git_command(cwd, "remote", timeout=timeout)
        remotes = [line.strip() for line in res.stdout.splitlines() if line.strip()]
        return remote in remotes
    except (OSError, subprocess.SubprocessError):
        return None


def get_remote_url(cwd: Path | str, remote: str = "origin", timeout: float = DEFAULT_GIT_TIMEOUT) -> str | None:
    """Retrieve the fetch URL of a git remote.

    Args:
        cwd: Working directory of the repository.
        remote: Remote name (default: 'origin').
        timeout: Command timeout in seconds.

    Returns:
        Remote URL string, or None if the remote is absent or the query fails.
    """
    try:
        res = run_git_command(cwd, "remote", "get-url", remote, timeout=timeout)
        url = res.stdout.strip()
        return url if url else None
    except (OSError, subprocess.SubprocessError):
        return None


def parse_github_remote(remote_url: str) -> tuple[str, str] | None:
    """Parse ``(owner, name)`` from an https or ssh GitHub remote URL.

    Args:
        remote_url: Remote URL, e.g. 'https://github.com/owner/name.git' or 'git@github.com:owner/name.git'.

    Returns:
        Tuple of owner and repository name, or None if the URL does not point at github.com.
    """
    match = re.search(r"github\.com[:/]([^/\s]+)/([^/\s]+?)(?:\.git)?/?$", remote_url.strip())
    return (match.group(1), match.group(2)) if match else None


def get_github_repo(cwd: Path | str, remote: str = "origin", timeout: float = DEFAULT_GIT_TIMEOUT) -> tuple[str, str] | None:
    """Retrieve the GitHub ``(owner, name)`` of a git remote.

    Args:
        cwd: Working directory of the repository.
        remote: Remote name (default: 'origin').
        timeout: Command timeout in seconds.

    Returns:
        Tuple of owner and repository name, or None if the remote is absent, not on GitHub, or the query fails.
    """
    url = get_remote_url(cwd, remote, timeout=timeout)
    return parse_github_remote(url) if url else None


def get_default_branch(cwd: Path | str, remote: str = "origin", timeout: float = DEFAULT_GIT_TIMEOUT) -> str | None:
    """Retrieve a remote's default branch from its locally recorded HEAD reference.

    Args:
        cwd: Working directory of the repository.
        remote: Remote name (default: 'origin').
        timeout: Command timeout in seconds.

    Returns:
        Branch name without the remote prefix, or None if 'refs/remotes/<remote>/HEAD' is unset or the query fails.
    """
    try:
        res = run_git_command(cwd, "symbolic-ref", "--quiet", "--short", f"refs/remotes/{remote}/HEAD", timeout=timeout)
        ref = res.stdout.strip()
        prefix = f"{remote}/"
        return ref[len(prefix) :] if ref.startswith(prefix) and len(ref) > len(prefix) else None
    except (OSError, subprocess.SubprocessError):
        return None


__all__ = [
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
    "get_remote_url",
    "parse_github_remote",
    "get_github_repo",
    "get_default_branch",
]
