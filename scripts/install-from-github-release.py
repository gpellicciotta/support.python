#!/usr/bin/env python3
# Copyright (c) Giovanni Pellicciotta
"""Installs a released wheel of a Python project straight from its GitHub release.

Stdlib-only and self-contained, so a consumer can copy this one file into its own scripts/ directory.
The repository defaults to the current directory's git origin and the package name to its pyproject.toml,
so a project can install its own releases; --repo and --package target any other project.

Usage:
  python scripts/install-from-github-release.py 1.2.3
  python scripts/install-from-github-release.py 1.2.3 --global
  python scripts/install-from-github-release.py 1.2.3 --repo owner/name --package name
"""

from __future__ import annotations

import argparse
import re
import shlex
import shutil
import subprocess
import sys
from pathlib import Path

PROG = "install-from-github-release"
EXIT_CODES = "Exit codes: 0 success, 1 bad arguments or undeterminable repository/package, 2 installation failed."


def parse_github_repo(remote_url: str) -> str:
    """Return ``owner/name`` from an https or ssh GitHub remote URL.

    Raises:
        ValueError: If the URL does not point at github.com.
    """
    match = re.search(r"github\.com[:/]([^/\s]+/[^/\s]+?)(?:\.git)?/?$", remote_url.strip())
    if not match:
        raise ValueError(f"Cannot parse a GitHub repository from remote URL: {remote_url}")
    return match.group(1)


def read_project_name(pyproject_text: str) -> str:
    """Return the ``name`` of the ``[project]`` table.

    Raises:
        ValueError: If no project name is declared.
    """
    section = re.search(r"^\[project\]\s*$(.*?)(?=^\[|\Z)", pyproject_text, re.MULTILINE | re.DOTALL)
    match = re.search(r'^name\s*=\s*"([^"]+)"', section.group(1) if section else "", re.MULTILINE)
    if not match:
        raise ValueError("Cannot find [project] name in pyproject.toml")
    return match.group(1)


def wheel_filename(package: str, version: str) -> str:
    """Return the wheel file name of a pure-Python package, normalized per PEP 427."""
    return f"{re.sub(r'[-_.]+', '_', package)}-{version}-py3-none-any.whl"


def release_asset_url(repo: str, version: str, asset: str) -> str:
    """Return the download URL of a release asset; the tag is ``v<version>``."""
    return f"https://github.com/{repo}/releases/download/v{version}/{asset}"


def build_install_command(url: str, global_install: bool, pipx_available: bool) -> list[str]:
    """Return the install command: pipx for global installs, else pip into the current environment."""
    if global_install and pipx_available:
        return ["pipx", "install", url, "--force"]
    if global_install:
        return [sys.executable, "-m", "pip", "install", "--user", url]
    return [sys.executable, "-m", "pip", "install", url]


def _origin_repo() -> str:
    result = subprocess.run(["git", "remote", "get-url", "origin"], capture_output=True, text=True, check=False)
    if result.returncode != 0:
        raise ValueError("Cannot read git remote 'origin'; pass --repo owner/name")
    return parse_github_repo(result.stdout)


def _local_package() -> str:
    try:
        return read_project_name(Path("pyproject.toml").read_text(encoding="utf-8"))
    except OSError as exc:
        raise ValueError(f"Cannot read pyproject.toml ({exc}); pass --package name") from exc


def version_line() -> str:
    """Returns `{name} v{version} - {copyright}`, reading the version from the pyproject.toml beside scripts/."""
    version = "unknown"
    try:
        text = (Path(__file__).resolve().parent.parent / "pyproject.toml").read_text(encoding="utf-8")
        match = re.search(r'^version\s*=\s*"([^"]+)"', text, re.MULTILINE)
        version = match.group(1) if match else version
    except OSError:
        pass
    return f"{PROG} v{version} - Copyright (c) Giovanni Pellicciotta"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog=PROG,
        description="Install a released wheel of a Python project from its GitHub release.",
        epilog=EXIT_CODES,
    )
    parser.add_argument("--version", action="version", version=version_line())
    parser.add_argument("version", help="release version to install, with or without a leading 'v' (e.g. 1.2.3)")
    parser.add_argument("--repo", metavar="OWNER/NAME", help="GitHub repository (default: git origin of the current directory)")
    parser.add_argument("--package", metavar="NAME", help="package name (default: [project] name in ./pyproject.toml)")
    parser.add_argument("--asset", metavar="FILE", help="release asset to install (default: the package's pure-Python wheel)")
    parser.add_argument("--global", dest="global_install", action="store_true", help="install via pipx, else pip --user")
    parser.add_argument("--dry-run", action="store_true", help="print the install command without running it")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    version = re.sub(r"^v", "", args.version, flags=re.IGNORECASE)
    try:
        repo = args.repo or _origin_repo()
        package = args.package or (repo.split("/")[1] if args.asset else _local_package())
    except ValueError as exc:
        print(f"**[ERROR]**: {exc}", file=sys.stderr)
        return 1
    asset = args.asset or wheel_filename(package, version)
    url = release_asset_url(repo, version, asset)

    pipx_available = shutil.which("pipx") is not None
    if args.global_install and not pipx_available:
        print("**[WARN]**:  pipx not found; falling back to 'pip install --user'.", file=sys.stderr)
    command = build_install_command(url, args.global_install, pipx_available)

    print(f"Repository : {repo}")
    print(f"Version    : v{version}")
    print(f"Source     : {url}")
    print(f"$ {shlex.join(command)}")
    if args.dry_run:
        return 0
    returncode = subprocess.run(command, check=False).returncode
    if returncode != 0:
        print(f"**[ERROR]**: Installation failed (exit code {returncode}).", file=sys.stderr)
        return 2
    print(f"Installed {package} v{version}.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
