"""Release helpers for version files, CHANGELOG.md headings, release notes, and GitHub origins.

Version files are read and written byte-faithfully, so their line endings survive. The CHANGELOG.md
helpers work on text and keep the newline style they find; they follow this repository's preamble,
where a version under development carries ``-pre`` and a frozen one carries a ``[status]`` tag.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

from ..files import atomic_write_text


@dataclass(frozen=True)
class VersionFile:
    """A supported project version file.

    Attributes:
        name: File name relative to the project root.
        pattern: Pattern whose group 1 is the version.
        template: Replacement for the whole match, with a ``{version}`` placeholder.
    """

    name: str
    pattern: re.Pattern[str]
    template: str


#: Supported version files, checked in this order.
VERSION_FILES: tuple[VersionFile, ...] = (
    VersionFile("pyproject.toml", re.compile(r'^version\s*=\s*"([^"]+)"', re.MULTILINE), 'version = "{version}"'),
    VersionFile("gradle.properties", re.compile(r"^version=([^\r\n]*)", re.MULTILINE), "version={version}"),
    VersionFile("package.json", re.compile(r'"version"\s*:\s*"([^"]+)"'), '"version": "{version}"'),
)

_PARTS = ("major", "minor", "patch")


def _read_raw(path: Path) -> str:
    with open(path, encoding="utf-8", newline="") as f:
        return f.read()


def _resolve(root: Path) -> tuple[Path, VersionFile, str, re.Match[str]]:
    """Return the first version file under ``root`` that declares a version, with its text and version match.

    Raises:
        FileNotFoundError: If no supported version file exists.
        ValueError: If version files exist but none declares a version.
    """
    present = False
    for entry in VERSION_FILES:
        path = Path(root) / entry.name
        if path.is_file():
            present = True
            text = _read_raw(path)
            match = entry.pattern.search(text)
            if match:
                return path, entry, text, match
    names = ", ".join(entry.name for entry in VERSION_FILES)
    if present:
        raise ValueError(f"No version declared in {names} under {root}")
    raise FileNotFoundError(f"No version file ({names}) found under {root}")


def find_version_file(root: Path) -> Path | None:
    """Return the first supported version file under ``root`` that declares a version, or ``None``."""
    try:
        return _resolve(root)[0]
    except (FileNotFoundError, ValueError):
        return None


def read_version(root: Path) -> str:
    """Return the project version, including any ``-pre`` suffix.

    Raises:
        FileNotFoundError: If no supported version file exists.
        ValueError: If version files exist but none declares a version.
    """
    return _resolve(root)[3].group(1).strip()


def write_version(root: Path, version: str) -> None:
    """Write ``version`` into the first version file, atomically and keeping its line endings.

    Raises:
        FileNotFoundError: If no supported version file exists.
        ValueError: If version files exist but none declares a version.
    """
    path, entry, text, match = _resolve(root)
    updated = text[: match.start()] + entry.template.format(version=version) + text[match.end() :]
    atomic_write_text(path, updated, newline="")


def release_version(version: str) -> str:
    """Return ``version`` without its ``-pre`` suffix (``1.2.3-pre`` becomes ``1.2.3``)."""
    return version.removesuffix("-pre")


def next_dev_version(version: str, part: str = "patch") -> str:
    """Return the next development version after ``version`` (``1.2.3`` becomes ``1.2.4-pre``).

    Args:
        version: Current ``MAJOR.MINOR.PATCH`` version, with or without ``-pre``.
        part: Part to bump: ``major``, ``minor``, or ``patch``; lower parts reset to 0.

    Raises:
        ValueError: If ``part`` is unknown or ``version`` is not ``MAJOR.MINOR.PATCH``.
    """
    if part not in _PARTS:
        raise ValueError(f"Unknown version part '{part}'; expected one of {', '.join(_PARTS)}")
    match = re.fullmatch(r"(\d+)\.(\d+)\.(\d+)", release_version(version))
    if not match:
        raise ValueError(f"Not a MAJOR.MINOR.PATCH version: {version}")
    numbers = [int(n) for n in match.groups()]
    index = _PARTS.index(part)
    numbers[index] += 1
    numbers[index + 1 :] = [0] * (len(numbers) - index - 1)
    return ".".join(str(n) for n in numbers) + "-pre"


def changelog_top_version(text: str) -> str | None:
    """Return the version of the first ``## v`` heading, suffix included, or ``None``."""
    match = re.search(r"^##\s+v(\S+)", text, re.MULTILINE)
    return match.group(1) if match else None


def _heading(version: str) -> re.Pattern[str]:
    return re.compile(rf"^##\s+v{re.escape(version)}(?![\w.-])")


def extract_release_notes(text: str, version: str) -> str:
    """Return the body under the ``## v<version> ...`` heading, without the heading line.

    Args:
        text: Raw CHANGELOG.md content.
        version: Version to extract, with or without a leading ``v``.

    Returns:
        The trimmed section body, ending at the next ``##`` heading.

    Raises:
        ValueError: If no heading for the version exists or its section is empty.
    """
    normalized = re.sub(r"^v", "", version, flags=re.IGNORECASE)
    lines = text.splitlines()
    heading = _heading(normalized)
    start = next((i for i, line in enumerate(lines) if heading.match(line)), None)
    if start is None:
        raise ValueError(f"No CHANGELOG.md heading found for version v{normalized}")
    end = next((i for i in range(start + 1, len(lines)) if re.match(r"^##\s+", lines[i])), len(lines))
    notes = "\n".join(lines[start + 1 : end]).strip()
    if not notes:
        raise ValueError(f"Release notes for v{normalized} in CHANGELOG.md are empty")
    return notes


def freeze_changelog(text: str, version: str, status: str) -> str:
    """Replace the ``## v<version>-pre`` (or bare ``## v<version>``) heading with ``## v<version> [<status>]``.

    Args:
        text: Raw CHANGELOG.md content.
        version: Version to freeze, with or without ``-pre``.
        status: Status tag body, e.g. ``2026-11-09`` (frozen) or ``released: 2026-11-09``.

    Returns:
        The updated text, or ``text`` unchanged when the heading already carries a status.

    Raises:
        ValueError: If no heading for the version exists.
    """
    release = release_version(version)
    pattern = re.compile(rf"^##\s+v{re.escape(release)}(?:-pre)?(?=[ \t\r]*$)", re.MULTILINE)
    frozen, count = pattern.subn(lambda _: f"## v{release} [{status}]", text, count=1)
    if count:
        return frozen
    if any(_heading(release).match(line) for line in text.splitlines()):
        return text
    raise ValueError(f"No '## v{release}' or '## v{release}-pre' heading in CHANGELOG.md")


def open_dev_changelog(text: str, version: str) -> str:
    """Insert an empty ``## v<version>`` section right after the first ``---`` line.

    Raises:
        ValueError: If the text has no ``---`` separator line.
    """
    match = re.search(r"^---[ \t]*(\r?\n|\Z)", text, re.MULTILINE)
    if not match:
        raise ValueError("No '---' separator line in CHANGELOG.md")
    newline = match.group(1) or ("\r\n" if "\r\n" in text else "\n")
    insertion = ("" if match.group(1) else newline) + f"{newline}## v{version}{newline}"
    return text[: match.end()] + insertion + text[match.end() :]


def parse_github_repo(remote_url: str) -> str:
    """Return ``owner/name`` from an https or ssh GitHub remote URL.

    Raises:
        ValueError: If the URL does not point at github.com.
    """
    match = re.search(r"github\.com[:/]([^/\s]+/[^/\s]+?)(?:\.git)?/?$", remote_url.strip())
    if not match:
        raise ValueError(f"Cannot parse a GitHub repository from remote URL: {remote_url}")
    return match.group(1)
