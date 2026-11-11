"""Release helpers for version files, CHANGELOG.md headings, release notes, GitHub origins, and a release pipeline.

Version files are read and written byte-faithfully, so their line endings survive. The CHANGELOG.md
helpers work on text and keep the newline style they find; they follow this repository's preamble,
where a version under development carries ``-pre`` and a frozen one carries a ``[status]`` tag.
:class:`ReleasePipeline` combines them into a dry-runnable freeze, tag, push, publish, and reopen flow.
"""

from __future__ import annotations

import re
import subprocess
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Callable, Optional, Sequence

from ..files import atomic_write_text
from ..git import parse_github_remote, parse_status_porcelain
from ..logging import CliLogger
from .steps import EXIT_COMMAND_NOT_FOUND, run_step_command


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
_CHANGELOG_VERSION = VersionFile("CHANGELOG.md", re.compile(r"^##[ \t]+v(\S+)", re.MULTILINE), "## v{version}")


def _read_raw(path: Path) -> str:
    with open(path, encoding="utf-8", newline="") as f:
        return f.read()


def _resolve(root: Path) -> tuple[Path, VersionFile, str, re.Match[str]]:
    """Resolve a declaring manifest or, when no manifests exist, the first changelog version heading.

    Raises:
        FileNotFoundError: If neither a supported manifest nor CHANGELOG.md exists.
        ValueError: If manifests declare no version, or the fallback changelog has no version heading.
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
    path = Path(root) / _CHANGELOG_VERSION.name
    if path.is_file():
        text = _read_raw(path)
        match = _CHANGELOG_VERSION.pattern.search(text)
        if match:
            return path, _CHANGELOG_VERSION, text, match
        raise ValueError(f"No version heading declared in CHANGELOG.md under {root}")
    raise FileNotFoundError(f"No version file ({names}, CHANGELOG.md) found under {root}")


def find_version_file(root: Path) -> Path | None:
    """Return the declaring manifest, or the changelog when no manifest exists; otherwise return ``None``."""
    try:
        return _resolve(root)[0]
    except (FileNotFoundError, ValueError):
        return None


def read_version(root: Path) -> str:
    """Return the manifest version, falling back to the top changelog version when no manifest exists.

    Raises:
        FileNotFoundError: If neither a supported manifest nor CHANGELOG.md exists.
        ValueError: If manifests declare no version, or the fallback changelog has no version heading.
    """
    return _resolve(root)[3].group(1).strip()


def write_version(root: Path, version: str) -> None:
    """Write ``version`` into the manifest or fallback changelog, atomically and preserving line endings.

    Raises:
        FileNotFoundError: If neither a supported manifest nor CHANGELOG.md exists.
        ValueError: If manifests declare no version, or the fallback changelog has no version heading.
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
    parsed = parse_github_remote(remote_url)
    if not parsed:
        raise ValueError(f"Cannot parse a GitHub repository from remote URL: {remote_url}")
    return "/".join(parsed)


def confirm_typed(summary: Sequence[str], phrase: str, *, input_fn: Callable[[str], str] = input) -> bool:
    """Print ``summary`` and return whether the user typed ``phrase``, ignoring surrounding whitespace.

    End of input or an interrupt at the prompt counts as declining.
    """
    for line in summary:
        print(line)
    try:
        answer = input_fn(f"Type '{phrase}' to continue: ")
    except (EOFError, KeyboardInterrupt):
        print()
        return False
    return answer.strip() == phrase


def capture_command(argv: Sequence[str], cwd: Path) -> tuple[int, str]:
    """Run a read-only query command and return its exit code with stdout, or with stderr when it fails.

    A missing executable returns :data:`~support_python.devops.steps.EXIT_COMMAND_NOT_FOUND`.
    """
    args = [str(arg) for arg in argv]
    try:
        result = subprocess.run(
            args,
            cwd=cwd,
            stdin=subprocess.DEVNULL,
            capture_output=True,
            encoding="utf-8",
            errors="replace",
            check=False,
        )
    except FileNotFoundError:
        return EXIT_COMMAND_NOT_FOUND, f"Executable not found on PATH: {args[0]}"
    except OSError as exc:
        return 1, f"Failed to start {args[0]}: {exc}"
    if result.returncode == 0:
        return 0, result.stdout
    return result.returncode, (result.stderr or result.stdout).strip()


#: A planned pipeline step: its description and the action performing it, which returns success.
_Step = tuple[str, Callable[[], bool]]


@dataclass
class ReleasePipeline:
    """Release the project under ``root``: freeze, tag, push, publish a GitHub release, and reopen development.

    ``root`` must hold ``CHANGELOG.md``, optionally a supported manifest, and an
    ``origin`` remote on GitHub. Every precondition runs before any change. Read-only commands run through
    ``query``; every command with side effects runs through ``runner``.

    Attributes:
        root: Repository root.
        logger: Logger receiving progress, planned steps, and errors.
        quality_check: Optional check run before any change; returning ``False`` aborts the release.
        assets: Optional callable returning files to attach, resolved after the quality check, or after ``build``
            when given; relative paths are taken from ``root``.
        build: Optional build run after the freeze commit and before tagging, so the assets carry the release
            version; returning ``False`` stops the release before anything is tagged or pushed.
        main_branch: Branch releases are cut from and pushed to.
        dry_run: Log every planned edit and command without running the quality check, prompting, or changing
            anything. Read-only precondition queries, including ``git fetch``, still run.
        assume_yes: Skip the typed confirmation.
        skip_github_release: Skip all gh queries, GitHub publication, and the final release URL.
        runner: Runs a side-effecting command as ``runner(argv, root, logger)`` and returns its exit code.
        query: Runs a read-only command as ``query(argv, root)`` and returns its exit code and output.
        input_fn: Prompt function used for the typed confirmation.
        today: Returns the release date written into the CHANGELOG.md status tag.
        sync_versions: Optional hook receiving the next development version after its manifest and changelog edits.
            Return repository-relative changed paths to stage in the development commit; raise an exception to abort.
    """

    root: Path
    logger: CliLogger
    quality_check: Callable[[], bool] | None = None
    assets: Callable[[], Sequence[Path]] | None = None
    build: Callable[[], bool] | None = None
    main_branch: str = "main"
    dry_run: bool = False
    assume_yes: bool = False
    runner: Callable[[Sequence[str], Path, CliLogger], int] = run_step_command
    query: Callable[[Sequence[str], Path], tuple[int, str]] = capture_command
    input_fn: Callable[[str], str] = input
    today: Callable[[], date] = date.today
    skip_github_release: bool = False
    sync_versions: Optional[Callable[[str], list[str]]] = None

    def run(self) -> int:
        """Run the pipeline.

        Returns:
            0 when released or when a dry run completes; 1 when a precondition, the quality check, the
            confirmation, or a step fails. A failed step leaves earlier steps in place.
        """
        root = Path(self.root)
        try:
            version_path, entry, _, match = _resolve(root)
        except (FileNotFoundError, ValueError) as exc:
            return self._fail(str(exc))
        current = match.group(1).strip()
        release = release_version(current)
        try:
            next_version = next_dev_version(release)
        except ValueError as exc:
            return self._fail(str(exc))
        tag = f"v{release}"
        freeze = current != release
        version_name = version_path.relative_to(root).as_posix()

        self.logger.info(f"Release version: {tag}")
        self.logger.info(f"Next version: v{next_version}")
        self.logger.info(f"Dry run: {self.dry_run}")

        notes = self._check_preconditions(root, release, tag, version_name if freeze else None)
        if notes is None:
            return 1
        if self.quality_check is not None:
            if self.dry_run:
                self.logger.info("[dry-run] Skipping the quality check.")
            elif not self.quality_check():
                return self._fail("Quality check failed; nothing was changed.")
        assets: list[Path] = []
        if self.build is None:
            assets = self._asset_paths(root)
            missing = [str(asset) for asset in assets if not asset.is_file()]
            if missing and not self.dry_run:
                return self._fail(f"Release assets not found: {', '.join(missing)}")

        steps = self._plan(root, entry, version_name, release, next_version, tag, notes, assets, freeze)
        if self.dry_run:
            for description, _ in steps:
                self.logger.info(f"[dry-run] {description}")
            self.logger.info("[dry-run] No changes were made.")
            return 0
        if not self.assume_yes:
            summary = [f"About to release {tag}:", *(f"  {description}" for description, _ in steps)]
            if not confirm_typed(summary, f"release {tag}", input_fn=self.input_fn):
                return self._fail("Release not confirmed; nothing was changed.")
        for description, action in steps:
            self.logger.info(description)
            if not action():
                return self._fail(f"Step failed: {description}. Earlier steps were not rolled back.")
        url = "" if self.skip_github_release else self._release_url(root, tag)
        self.logger.info(f"Released {tag}{url}.")
        return 0

    def _fail(self, message: str) -> int:
        self.logger.error(message)
        return 1

    def _check_preconditions(self, root: Path, release: str, tag: str, freeze_file: str | None) -> str | None:
        """Return the release notes when every precondition holds; otherwise log the failure and return ``None``."""

        def fail(message: str) -> None:
            self.logger.error(message)

        code, out = self.query(["git", "status", "--porcelain=v1", "-z", "--untracked-files=all"], root)
        if code != 0:
            return fail(f"Could not read the git status: {out}")
        allowed = {freeze_file, "CHANGELOG.md"} if freeze_file else set()
        dirty = sorted({entry["path"] for entry in parse_status_porcelain(out)} - allowed)
        if dirty:
            return fail(f"Uncommitted changes in: {', '.join(dirty)}; commit or stash them before releasing.")

        code, out = self.query(["git", "branch", "--show-current"], root)
        branch = out.strip()
        if code != 0 or branch != self.main_branch:
            return fail(f"Releases must be cut from branch '{self.main_branch}' (currently on '{branch}').")

        if not self.skip_github_release and self.query(["gh", "--version"], root)[0] != 0:
            return fail("The 'gh' CLI is not installed; see https://cli.github.com/.")
        if not self.skip_github_release and self.query(["gh", "auth", "status"], root)[0] != 0:
            return fail("The 'gh' CLI is not authenticated; run 'gh auth login' before releasing.")

        code, out = self.query(["git", "fetch", "origin", self.main_branch, "--tags"], root)
        if code != 0:
            return fail(f"Could not fetch origin/{self.main_branch}: {out}")
        code, out = self.query(["git", "ls-remote", "--tags", "origin", f"refs/tags/{tag}"], root)
        if code != 0:
            return fail(f"Could not list the tags on origin: {out}")
        if out.strip():
            return fail(f"Tag '{tag}' already exists on origin.")
        if self.query(["git", "rev-parse", "-q", "--verify", f"refs/tags/{tag}"], root)[0] == 0:
            return fail(f"Tag '{tag}' already exists locally; delete it or release another version.")
        if not self.skip_github_release and self.query(["gh", "release", "view", tag], root)[0] == 0:
            return fail(f"GitHub release '{tag}' already exists.")

        try:
            text = _read_raw(root / "CHANGELOG.md")
        except OSError as exc:
            return fail(f"Could not read CHANGELOG.md: {exc}")
        lines = text.splitlines()
        heading = next((v for v in (release, f"{release}-pre") if any(_heading(v).match(line) for line in lines)), release)
        try:
            return extract_release_notes(text, heading)
        except ValueError as exc:
            return fail(str(exc))

    def _plan(
        self,
        root: Path,
        entry: VersionFile,
        version_name: str,
        release: str,
        next_version: str,
        tag: str,
        notes: str,
        assets: list[Path],
        freeze: bool,
    ) -> list[_Step]:
        status = f"released: {self.today().isoformat()}"
        changed = list(dict.fromkeys(["CHANGELOG.md", version_name]))
        next_add = ["git", "add", *changed]
        steps: list[_Step] = []
        if freeze:
            steps += [
                self._edit(root, "CHANGELOG.md", f"## v{release} [{status}]", lambda text: freeze_changelog(text, release, status)),
                *([] if version_name == "CHANGELOG.md" else [self._set_version(root, entry, version_name, release)]),
                self._command(root, ["git", "add", *changed]),
                self._command(root, ["git", "commit", "-m", f"Released version {release}."]),
            ]
        if self.build is not None:
            steps.append(self._build(root, assets))
        steps += [
            self._command(root, ["git", "tag", tag]),
            self._command(root, ["git", "push", "origin", self.main_branch]),
            self._command(root, ["git", "push", "origin", tag]),
            *([] if self.skip_github_release else [self._publish(root, tag, notes, assets, built=self.build is not None)]),
            self._edit(root, "CHANGELOG.md", f"## v{next_version}", lambda text: open_dev_changelog(text, next_version)),
            *([] if version_name == "CHANGELOG.md" else [self._set_version(root, entry, version_name, next_version)]),
            *([] if self.sync_versions is None else [self._sync_versions(next_version, next_add)]),
            self._command(root, next_add),
            self._command(root, ["git", "commit", "-m", f"Started version {next_version} after the {release} release."]),
            self._command(root, ["git", "push", "origin", self.main_branch]),
        ]
        return steps

    def _sync_versions(self, version: str, next_add: list[str]) -> _Step:
        def action() -> bool:
            try:
                paths = self.sync_versions(version) if self.sync_versions is not None else []
                next_add.extend(path for path in dict.fromkeys(paths) if path not in next_add[2:])
            except Exception as exc:
                self.logger.error(f"Could not sync extra version targets: {exc}")
                return False
            return True

        return f"sync extra version targets to {version}", action

    def _asset_paths(self, root: Path) -> list[Path]:
        return [root / Path(asset) for asset in self.assets()] if self.assets is not None else []

    def _build(self, root: Path, assets: list[Path]) -> _Step:
        """Return the step running ``build`` and filling ``assets`` with its outputs."""

        def action() -> bool:
            if self.build is None or not self.build():
                return False
            assets[:] = self._asset_paths(root)
            missing = [str(asset) for asset in assets if not asset.is_file()]
            if missing:
                self.logger.error(f"Release assets not found: {', '.join(missing)}")
                return False
            return True

        return "build release assets from the frozen version", action

    def _command(self, root: Path, argv: list[str]) -> _Step:
        return subprocess.list2cmdline(argv), lambda: self.runner(argv, root, self.logger) == 0

    def _edit(self, root: Path, name: str, change: str, transform: Callable[[str], str]) -> _Step:
        def action() -> bool:
            path = root / name
            try:
                atomic_write_text(path, transform(_read_raw(path)), newline="")
            except (OSError, ValueError) as exc:
                self.logger.error(f"Could not update {name}: {exc}")
                return False
            return True

        return f"edit {name}: {change}", action

    def _set_version(self, root: Path, entry: VersionFile, name: str, version: str) -> _Step:
        def action() -> bool:
            try:
                write_version(root, version)
            except (OSError, ValueError) as exc:
                self.logger.error(f"Could not update {name}: {exc}")
                return False
            return True

        return f"edit {name}: {entry.template.format(version=version)}", action

    def _publish(self, root: Path, tag: str, notes: str, assets: Sequence[Path], *, built: bool = False) -> _Step:
        """Return the publish step; with ``built``, ``assets`` is filled by the build step before it runs."""

        def argv(notes_file: str, planned: bool = False) -> list[str]:
            files = ["<built-assets>"] if planned and built else [str(asset) for asset in assets]
            return ["gh", "release", "create", tag, "--title", tag, "--notes-file", notes_file, *files]

        def action() -> bool:
            with TemporaryDirectory(prefix="release-notes-") as tmp:
                notes_file = Path(tmp) / "notes.md"
                notes_file.write_text(notes, encoding="utf-8")
                return self.runner(argv(str(notes_file)), root, self.logger) == 0

        return subprocess.list2cmdline(argv("<notes-file>", planned=True)), action

    def _release_url(self, root: Path, tag: str) -> str:
        code, out = self.query(["git", "remote", "get-url", "origin"], root)
        if code != 0:
            return ""
        try:
            return f": https://github.com/{parse_github_repo(out)}/releases/tag/{tag}"
        except ValueError:
            return ""
