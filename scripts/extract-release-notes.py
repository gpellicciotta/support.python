#!/usr/bin/env python3
# Copyright (c) Giovanni Pellicciotta
"""Extracts one version's section from CHANGELOG.md for use as GitHub Release notes.

Reads CHANGELOG.md at the root of the Git repository containing the current directory,
unless a changelog path is given.

Usage:
  python scripts/extract-release-notes.py 2.0.1
  python scripts/extract-release-notes.py v2.0.1 path/to/CHANGELOG.md
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

_SRC = Path(__file__).resolve().parent.parent / "src"
if _SRC.is_dir():
    sys.path.insert(0, str(_SRC))

from support_python.devops.release import extract_release_notes  # noqa: E402
from support_python.git import get_repo_root  # noqa: E402
from support_python.version import get_project_version  # noqa: E402

__all__ = ["extract_release_notes", "main"]


def version_line() -> str:
    """Returns the standard `{name} v{version} - {copyright}` line for --version."""
    return f"extract-release-notes v{get_project_version(Path(__file__).resolve().parent)} - Copyright (c) Giovanni Pellicciotta"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="extract-release-notes",
        description="Extracts one version's section from CHANGELOG.md for use as GitHub Release notes.",
    )
    parser.add_argument("--version", action="version", version=version_line())
    parser.add_argument("release_version", metavar="version", help="version to extract, with or without a leading 'v'")
    parser.add_argument("changelog", nargs="?", help="changelog path (default: CHANGELOG.md at the Git repository root)")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.changelog:
        path = Path(args.changelog)
    else:
        root = get_repo_root(Path.cwd())
        if root is None:
            print("**[ERROR]**: not inside a Git repository", file=sys.stderr)
            return 1
        path = root / "CHANGELOG.md"
    try:
        print(extract_release_notes(path.read_text(encoding="utf-8"), args.release_version))
    except (OSError, ValueError) as exc:
        print(f"**[ERROR]**: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
