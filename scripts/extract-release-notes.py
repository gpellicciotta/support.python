#!/usr/bin/env python3
# Copyright (c) Giovanni Pellicciotta
"""Extracts one version's section from CHANGELOG.md for use as GitHub Release notes.

Usage:
  python scripts/extract-release-notes.py 2.0.1
  python scripts/extract-release-notes.py v2.0.1 path/to/CHANGELOG.md
"""

from __future__ import annotations

import re
import sys
from pathlib import Path


def extract_release_notes(changelog_text: str, version: str) -> str:
    """Return the body under the ``## v<version> ...`` heading, without the heading line.

    Args:
        changelog_text: Raw CHANGELOG.md content.
        version: Version to extract, with or without a leading ``v``.

    Returns:
        The trimmed section body, ending at the next ``##`` heading.

    Raises:
        ValueError: If no heading for the version exists.
    """
    normalized = re.sub(r"^v", "", version, flags=re.IGNORECASE)
    lines = changelog_text.splitlines()
    heading = re.compile(rf"^##\s+v{re.escape(normalized)}(?![\w.-])")
    start = next((i for i, line in enumerate(lines) if heading.match(line)), None)
    if start is None:
        raise ValueError(f"No CHANGELOG.md heading found for version v{normalized}")
    end = next((i for i in range(start + 1, len(lines)) if re.match(r"^##\s+", lines[i])), len(lines))
    return "\n".join(lines[start + 1 : end]).strip()


def main(argv: list[str] | None = None) -> int:
    args = sys.argv[1:] if argv is None else argv
    if not args:
        print("Usage: extract-release-notes.py <version> [changelog-path]", file=sys.stderr)
        return 1
    path = Path(args[1] if len(args) > 1 else "CHANGELOG.md")
    try:
        print(extract_release_notes(path.read_text(encoding="utf-8"), args[0]))
    except (OSError, ValueError) as exc:
        print(f"**[ERROR]**: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
