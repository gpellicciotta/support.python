#!/usr/bin/env python3
"""Runs the typical operations of this project through its virtual environment.

Run `python scripts/bootstrap-dev-environment.py` first to create the virtual environment.

Usage:
  python scripts/devops.py lint
  python scripts/devops.py test
  python scripts/devops.py build
  python scripts/devops.py check
  python scripts/devops.py --version
"""

from __future__ import annotations

import re
import shutil
import subprocess
import sys
from pathlib import Path

from _cli_common import build_action_parser, print_help, print_version

PROG = "devops"
DESCRIPTION = "Runs lint, test, build, and clean operations of this project in its virtual environment."
ACTIONS = ["lint", "test", "build", "check", "clean", "version", "help"]
EXIT_CODES = [(0, "Success"), (1, "An operation failed or the virtual environment is missing")]
REPO_ROOT = Path(__file__).resolve().parent.parent
VENV_DIR = REPO_ROOT / ".venv"
DIST_DIR = REPO_ROOT / "dist"


def get_project_version() -> str:
    """Resolves the current project version from pyproject.toml."""
    content = (REPO_ROOT / "pyproject.toml").read_text(encoding="utf-8")
    match = re.search(r'^version\s*=\s*"([^"]+)"', content, re.MULTILINE)
    return match.group(1).strip() if match else "0.0.0+unknown"


def venv_python() -> Path:
    """Returns the path to the venv's own python executable, cross-platform."""
    return VENV_DIR / ("Scripts/python.exe" if sys.platform == "win32" else "bin/python")


def run(args: list) -> bool:
    """Runs one command in the repository root. Returns whether it succeeded."""
    print(f"[*] {' '.join(args)}", flush=True)
    return subprocess.run(args, cwd=str(REPO_ROOT), check=False).returncode == 0


def lint(python: str) -> bool:
    return run([python, "-m", "ruff", "check", "."]) and run([python, "-m", "ruff", "format", "--check", "."])


def test(python: str) -> bool:
    return run([python, "-m", "pytest", "-q"])


def build(python: str) -> bool:
    shutil.rmtree(DIST_DIR, ignore_errors=True)
    return run([python, "-m", "build", "-o", str(DIST_DIR)])


def clean(python: str) -> bool:
    shutil.rmtree(DIST_DIR, ignore_errors=True)
    shutil.rmtree(REPO_ROOT / "build", ignore_errors=True)
    return True


def main() -> int:
    parser = build_action_parser(PROG, DESCRIPTION, ACTIONS, "help")
    args = parser.parse_args()
    version = get_project_version()

    if args.version or args.action == "version":
        print_version(PROG, version)
        return 0
    if args.help or args.action == "help":
        print_help(PROG, version, DESCRIPTION, parser, EXIT_CODES)
        return 0

    if not venv_python().exists():
        print("[!] Virtual environment missing; run scripts/bootstrap-dev-environment.py first.", file=sys.stderr)
        return 1
    python = str(venv_python())
    operations = {"lint": [lint], "test": [test], "build": [build], "clean": [clean], "check": [lint, test, build]}
    return 0 if all(operation(python) for operation in operations[args.action]) else 1


if __name__ == "__main__":
    sys.exit(main())
