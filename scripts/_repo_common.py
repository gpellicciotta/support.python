"""Shared helpers for the repository maintenance scripts (reset-history.py and migrate-namespace.py).

Wraps command execution with echo, typed confirmation for outbound or destructive steps, version-file and
CHANGELOG.md access that keeps the on-disk line endings, and GitHub origin parsing.
"""

from __future__ import annotations

import re
import shlex
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent

#: Supported version files: (file name, pattern whose group 1 is the version, replacement template).
VERSION_FILES = (
    ("gradle.properties", re.compile(r"^version=([^\r\n]*)", re.MULTILINE), "version={version}"),
    ("pyproject.toml", re.compile(r'^version\s*=\s*"([^"]+)"', re.MULTILINE), 'version = "{version}"'),
    ("package.json", re.compile(r'"version"\s*:\s*"([^"]+)"'), '"version": "{version}"'),
)


def die(message: str) -> None:
    """Exit with a severity-tagged error message."""
    sys.exit(f"**[ERROR]**: {message}")


def run(args: list[str], capture: bool = False, check: bool = True) -> str:
    """Echo and run a command in the repository root. Returns trimmed stdout when capturing."""
    print(f"$ {shlex.join(args)}")
    result = subprocess.run(args, cwd=REPO_ROOT, check=check, text=True, capture_output=capture)
    return result.stdout.strip() if capture else ""


def confirm(summary: list[str], phrase: str) -> None:
    """Print a summary and require the user to type the phrase; exit otherwise."""
    print()
    print("\n".join(summary))
    if input(f"\nType '{phrase}' to proceed: ").strip() != phrase:
        sys.exit("aborted")


def outbound(args: list[str]) -> None:
    """Run a command that leaves this machine only after the user types 'yes'."""
    confirm([f"OUTBOUND: {shlex.join(args)}"], "yes")
    run(args)


def read(name: str) -> str:
    """Read a repository file as UTF-8 without newline translation."""
    with open(REPO_ROOT / name, encoding="utf-8", newline="") as f:
        return f.read()


def write(name: str, text: str) -> None:
    """Write a repository file as UTF-8 without newline translation."""
    with open(REPO_ROOT / name, "w", encoding="utf-8", newline="") as f:
        f.write(text)


def read_changelog() -> tuple[str, str]:
    """Return CHANGELOG.md as LF text plus its on-disk line ending."""
    text = read("CHANGELOG.md")
    return text.replace("\r\n", "\n"), "\r\n" if "\r\n" in text else "\n"


def write_changelog(text: str, newline: str) -> None:
    """Write LF text to CHANGELOG.md using the given line ending."""
    write("CHANGELOG.md", text.replace("\n", newline))


def version_file() -> tuple[str, re.Pattern, str]:
    """Return the first supported version file present in the repository."""
    for entry in VERSION_FILES:
        if (REPO_ROOT / entry[0]).is_file() and entry[1].search(read(entry[0])):
            return entry
    die("no version found in " + ", ".join(name for name, _, _ in VERSION_FILES))
    raise AssertionError("unreachable")


def current_version() -> str:
    """Read the project version, including any -pre suffix."""
    name, pattern, _ = version_file()
    return pattern.search(read(name)).group(1).strip()


def set_version(version: str) -> None:
    """Write the project version into the first supported version file."""
    name, pattern, template = version_file()
    write(name, pattern.sub(lambda _: template.format(version=version), read(name), count=1))


def origin() -> tuple[str, str]:
    """Return the (owner, repo) of the GitHub origin remote."""
    url = run(["git", "remote", "get-url", "origin"], capture=True)
    match = re.search(r"github\.com[/:]([^/]+)/(.+?)(?:\.git)?$", url)
    if not match:
        die(f"cannot parse origin {url}")
    return match.group(1), match.group(2)


def default_branch() -> str:
    """Return origin's default branch, falling back to the current branch, then 'main'."""
    ref = run(["git", "symbolic-ref", "--short", "refs/remotes/origin/HEAD"], capture=True, check=False)
    if ref.startswith("origin/"):
        return ref[len("origin/") :]
    return run(["git", "branch", "--show-current"], capture=True) or "main"
