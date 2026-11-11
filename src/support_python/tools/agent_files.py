#!/usr/bin/env python3
"""
Deterministically install an existing agent digest (default ./agent-digest.md) into a guarded block in
each installed AI coding tool's global instructions file, plus the skills under ./agent-skills, and
(separately) offer a `review` action where a tool's own CLI inspects this repository for improvement
suggestions. Generating the digest and skills is agent-digest's job; this script never regenerates them.

See docs/agent-instruction-files-notes.md for the design rationale.
Each target file keeps the guarded `dev-guidelines` block first and any tool-specific/personal
content after it, untouched by this script.
"""

from __future__ import annotations

import argparse
import difflib
import json
import os
import re
import shutil
import subprocess
import sys
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable, Sequence

from support_python.cli import PROJECT_VERSION, ToolHarness  # noqa: E402
from support_python.config import SettingsSchema, add_config_actions  # noqa: E402
from support_python.logging import (  # noqa: E402
    CliLogger,
    format_severity_indicator as format_severity_indicator,
)
from support_python.tools import TOOLS_COPYRIGHT
from support_python.tools.agent_files_config import (
    DEFAULT_DIGEST_RELPATH,
    DEFAULT_LEGACY_SKILL_NAMES,
    DEFAULT_MANIFEST_NAME,
    DEFAULT_MANIFEST_SOURCE,
    DEFAULT_MARKER,
    DEFAULT_MARKER_BEGIN,
    DEFAULT_MARKER_END,
    DEFAULT_SKILLS_RELPATH,
    begin_marker_pattern,
    build_schema,
)


TOOL_NAME = "agent-files"
TOOL_VERSION = PROJECT_VERSION


def find_project_root(path: Path | None = None) -> Path:
    """Find the root of the project containing path by searching upward for repository or project markers."""
    resolved = (path or Path.cwd()).resolve()
    current = resolved.parent if resolved.is_file() else resolved
    for directory in (current, *current.parents):
        if (directory / ".git").exists():
            return directory
    for directory in (current, *current.parents):
        if any(
            (directory / marker).exists()
            for marker in ("PLAN.md", "pyproject.toml", "package.json", "pom.xml", "build.gradle", "go.mod", "Cargo.toml")
        ):
            return directory
    return current


REPO_ROOT = find_project_root()
DIGEST_PATH = REPO_ROOT / DEFAULT_DIGEST_RELPATH
SKILLS_DIR = REPO_ROOT / DEFAULT_SKILLS_RELPATH
_INITIAL_REPO_ROOT = REPO_ROOT
_INITIAL_DIGEST_PATH = DIGEST_PATH
_INITIAL_SKILLS_DIR = SKILLS_DIR


def _resolve_repo_root() -> Path:
    """Return REPO_ROOT if overridden by a caller, or resolve from the current working directory."""
    return REPO_ROOT if REPO_ROOT is not _INITIAL_REPO_ROOT else find_project_root()


def _resolve_digest_path() -> Path:
    """Return DIGEST_PATH if overridden by a caller, or resolve under the active repository root."""
    return DIGEST_PATH if DIGEST_PATH is not _INITIAL_DIGEST_PATH else _resolve_repo_root() / DEFAULT_DIGEST_RELPATH


def _resolve_skills_dir() -> Path:
    """Return SKILLS_DIR if overridden by a caller, or resolve under the active repository root."""
    return SKILLS_DIR if SKILLS_DIR is not _INITIAL_SKILLS_DIR else _resolve_repo_root() / DEFAULT_SKILLS_RELPATH


DEFAULT_TIMEOUT_SECONDS = 900

# Ownership manifest written into each tool's skills directory, so `sync` can prune skills this
# script installed earlier without ever touching skills installed by anything else.
SKILLS_MANIFEST_NAME = DEFAULT_MANIFEST_NAME
SKILLS_MANIFEST_SCHEMA_VERSION = 1
SKILLS_MANIFEST_SOURCE = DEFAULT_MANIFEST_SOURCE
# Skills installed by versions of this script that predate the manifest; used when none exists yet.
LEGACY_SKILL_NAMES: tuple[str, ...] = DEFAULT_LEGACY_SKILL_NAMES
STALE_FILE_DIFF_PREFIX = "stale file in target: "


MARKER_BEGIN = DEFAULT_MARKER_BEGIN
MARKER_END = DEFAULT_MARKER_END
# Also recognizes begin lines of earlier marker wordings; None when the begin marker was configured explicitly.
MARKER_BEGIN_PATTERN: re.Pattern[str] | None = begin_marker_pattern(DEFAULT_MARKER)

REVIEW_PROMPT_TEMPLATE = """\
You are reviewing the guidelines repository at "{repository_root}".

Inspect the repository's current guideline documents, notes, and supporting scripts. Also inspect your own
global instructions file at "{target_file}" and use it as additional context for identifying useful practices,
inconsistencies, omissions, or improvements that this guidelines repository should consider.

Make local edits directly in the guidelines repository when you identify worthwhile improvements. Keep the edits
focused, preserve the repository's existing intent, and do not modify your global instructions file. Do not commit,
push, publish, or deploy anything. Do not change files outside the guidelines repository.

After editing, briefly summarize the changes you made, the changes you considered but did not make, and any
remaining suggestions. If no edits are justified, leave the repository unchanged and explain why.
"""


def format_duration(seconds: float) -> str:
    """Format duration in seconds to a concise human-readable string (e.g. '1h 23m 45s' or '12.3s')."""
    if seconds < 0:
        return "0.0s"
    if seconds < 60:
        return f"{seconds:.1f}s"
    mins, secs = divmod(int(seconds), 60)
    hours, mins = divmod(mins, 60)
    if hours > 0:
        return f"{hours}h {mins:02d}m {secs:02d}s"
    return f"{mins}m {secs:02d}s"


@dataclass(frozen=True)
class Tool:
    """An agent CLI that reviews its global instruction file: its command, target file, and review arguments."""

    name: str
    command: str
    target_file: Path
    review_args: Callable[[str, str, int], list[str]]
    fallback_paths: tuple[Path, ...] = ()  # well-known install locations to try when not on PATH
    skills_dir: Path | None = None
    native_skill_discovery: bool = False  # tool indexes skills_dir itself, so no catalog is injected
    # Directories this script installed skills into before skills_dir moved; cleaned up on sync.
    legacy_skills_dirs: tuple[Path, ...] = ()
    # Names assumed to be owned in skills_dir when it has no manifest yet.
    bootstrap_skill_names: tuple[str, ...] = LEGACY_SKILL_NAMES
    aliases: tuple[str, ...] = ()


def claude_review_args(prompt: str, target_filename: str, timeout: int) -> list[str]:
    """Return the Claude CLI arguments for a non-interactive review that may edit files."""
    return ["-p", "--permission-mode", "acceptEdits"]


def antigravity_review_args(prompt: str, target_filename: str, timeout: int) -> list[str]:
    """Return the Antigravity CLI arguments, with a print timeout set to 90% of ``timeout``."""
    # agy's own --print-timeout defaults to 5m; set it to 90% of our wrapper's timeout so our
    # wrapper (not agy) is the one that fires on a real hang.
    agy_timeout_seconds = max(60, int(timeout * 0.9))
    agy_timeout = f"{agy_timeout_seconds // 60}m{agy_timeout_seconds % 60}s"
    return ["--dangerously-skip-permissions", "--disable-slash-commands", "--print-timeout", agy_timeout, "--print", prompt]


def codex_review_args(prompt: str, target_filename: str, timeout: int) -> list[str]:
    """Return the Codex CLI arguments for a non-interactive review with full file access."""
    # danger-full-access is required: workspace-write determines the writable area by git root
    # detection, and this repo is the git root, which is what we actually want write access to.
    return ["exec", "--sandbox", "danger-full-access", "--skip-git-repo-check"]


TOOLS: list[Tool] = [
    Tool(
        "claude-code",
        "claude",
        Path.home() / ".claude" / "CLAUDE.md",
        claude_review_args,
        skills_dir=Path.home() / ".claude" / "skills",
        native_skill_discovery=True,
        aliases=("claude",),
    ),
    Tool(
        "antigravity",
        "agy",
        Path.home() / ".gemini" / "GEMINI.md",
        antigravity_review_args,
        fallback_paths=(
            # Antigravity installer puts agy in ~/.gemini/bin, which is added to PATH only in
            # interactive shell sessions. Python subprocesses may not inherit it on Windows.
            Path.home() / ".gemini" / "bin" / "agy.exe",
            Path.home() / ".gemini" / "bin" / "agy",
        ),
        skills_dir=Path.home() / ".gemini" / "config" / "skills",
        native_skill_discovery=True,
    ),
    Tool(
        "codex-cli",
        "codex",
        Path.home() / ".codex" / "AGENTS.md",
        codex_review_args,
        # ~/.agents/skills is the user-level location Codex documents; ~/.codex/skills is still
        # scanned but deprecated, so copies left there would show up as duplicate skills.
        skills_dir=Path.home() / ".agents" / "skills",
        native_skill_discovery=True,
        legacy_skills_dirs=(Path.home() / ".codex" / "skills",),
        # ~/.agents/skills is shared with other installers and was never written by older versions
        # of this script, so nothing there is owned until a manifest says so.
        bootstrap_skill_names=(),
        aliases=("codex",),
    ),
]
_INITIAL_TOOLS: list[Tool] = list(TOOLS)

# GitHub Copilot is not included yet: its personal/global instructions, where supported, live in
# VS Code's own JSON settings rather than a plain-text file, and it has no confirmed local CLI to
# drive headlessly. Add an adapter here once that's confirmed.


def load_digest() -> str:
    """Return the stripped digest text, or an empty string when the digest file is missing."""
    digest_path = _resolve_digest_path()
    if not digest_path.is_file():
        return ""
    return digest_path.read_text(encoding="utf-8").strip()


def build_guarded_block(digest: str, skills_catalog: str = "") -> str:
    """Wrap the digest, and the skills catalog when present, between the guarded-block markers."""
    content = digest.strip()
    if skills_catalog.strip():
        content = f"{content}\n\n{skills_catalog.strip()}"
    return f"{MARKER_BEGIN}\n\n{content}\n\n{MARKER_END}"


def _find_begin_marker(content: str) -> int | None:
    """Return the offset of the guarded block's begin marker in content, or None when it has none.

    The earliest of the exact MARKER_BEGIN text and a MARKER_BEGIN_PATTERN match wins.
    The pattern finds begin lines of earlier marker wordings.
    """
    offsets = [content.index(MARKER_BEGIN)] if MARKER_BEGIN in content else []
    match = MARKER_BEGIN_PATTERN.search(content) if MARKER_BEGIN_PATTERN is not None else None
    if match:
        offsets.append(match.start())
    return min(offsets) if offsets else None


def apply_guarded_block(current_content: str, guarded_block: str) -> str:
    """Return current_content with its dev-guidelines guarded block replaced by guarded_block, or --
    if no guarded block exists yet -- guarded_block inserted at the very top, ahead of any existing
    (tool-specific/personal) content, which is otherwise left completely untouched."""
    begin_idx = _find_begin_marker(current_content)
    has_begin = begin_idx is not None
    has_end = MARKER_END in current_content

    if has_begin and has_end:
        end_idx = current_content.index(MARKER_END)
        if end_idx < begin_idx:
            raise ValueError("the dev-guidelines END marker appears before the BEGIN marker")
        new_content = current_content[:begin_idx] + guarded_block + current_content[end_idx + len(MARKER_END) :]
    elif not has_begin and not has_end:
        rest = current_content.strip()
        new_content = guarded_block if not rest else f"{guarded_block}\n\n{rest}"
    else:
        raise ValueError(
            "found only one of the dev-guidelines BEGIN/END markers -- the file may have been "
            "edited by hand into an inconsistent state; resolve manually before running sync"
        )

    return new_content.strip() + "\n"


def collect_tools_info() -> list[dict[str, str | bool]]:
    """Return structured metadata for each configured tool."""
    entries: list[dict[str, str | bool]] = []
    for tool in TOOLS:
        executable = resolve_command(tool)
        if executable is None:
            executable, version = "not found", "not found"
        else:
            try:
                res = subprocess.run([executable, "--version"], capture_output=True, text=True, timeout=10)
                version = (res.stdout.strip() or res.stderr.strip() or "unknown").splitlines()[0]
            except (OSError, subprocess.TimeoutExpired):
                version = "unknown"
        entries.append(
            {
                "tool": tool.name,
                "command": tool.command,
                "available": executable != "not found",
                "executable": executable,
                "version": version,
                "instructions_file": str(tool.target_file),
                "skills_dir": str(tool.skills_dir) if tool.skills_dir else "n/a",
            }
        )
    return entries


def print_tools(logger: CliLogger | None = None) -> None:
    """Print a table of the supported tools and whether each one is available."""
    rows = [
        (
            str(i["tool"]),
            str(i["command"]),
            "available" if i["available"] else "unavailable",
            str(i["executable"]),
            str(i["version"]),
            str(i["instructions_file"]),
            str(i["skills_dir"]),
        )
        for i in collect_tools_info()
    ]
    headers = ("Tool", "Command", "Status", "Executable", "Version", "Target", "Skills Target")
    widths = [max(len(header), *(len(row[index]) for row in rows)) for index, header in enumerate(headers)]

    lines = [
        "Configured AI tools",
        "-------------------",
        "  ".join(header.ljust(width) for header, width in zip(headers, widths)),
        "  ".join("-" * width for width in widths),
        *("  ".join(value.ljust(width) for value, width in zip(row, widths)) for row in rows),
    ]
    for line in lines:
        logger.emit(line) if logger is not None else print(line)


def select_tools(tool_names: list[str]) -> list[Tool]:
    """Return the configured tools named in tool_names (already validated), or all tools when empty."""
    from support_python.tools.agent_files_config import ToolRegistry

    return ToolRegistry(TOOLS).select(tool_names)


def backup(target_file: Path) -> Path | None:
    """Copy ``target_file`` to a timestamped ``.bak-`` sibling and return its path, or None when the file is missing."""
    if not target_file.exists():
        return None
    stamp = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
    backup_path = target_file.with_name(f"{target_file.name}.bak-{stamp}")
    shutil.copy2(target_file, backup_path)
    return backup_path


def write_text_in_place(path: Path, content: str, newline: str | None = None) -> None:
    """Write content to path, rewriting an existing file in place rather than recreating it.
    Windows refuses mode "w" on a hidden file, while "r+" opens it and keeps its Hidden attribute."""
    try:
        file = path.open("r+", encoding="utf-8", newline=newline)
    except FileNotFoundError:
        file = path.open("w", encoding="utf-8", newline=newline)
    with file:
        file.write(content)
        file.truncate()


def copy_file_in_place(src: str, dst: str) -> str:
    """A `shutil.copytree` copy_function that overwrites existing (possibly hidden) files in place,
    then copies metadata like `shutil.copy2`."""
    data = Path(src).read_bytes()
    try:
        file = open(dst, "r+b")
    except FileNotFoundError:
        file = open(dst, "wb")
    with file:
        file.write(data)
        file.truncate()
    shutil.copystat(src, dst)
    return dst


def resolve_command(tool: Tool) -> str | None:
    """Return the resolved executable path for tool, or None if not found."""
    resolved = shutil.which(tool.command)
    if resolved is not None:
        return resolved
    for path in tool.fallback_paths:
        if path.is_file():
            return str(path)
    return None


def sync_tool(
    tool: Tool,
    guarded_block: str,
    action: str,
    logger: CliLogger,
    changes: list[str] | None = None,
) -> bool:
    """Apply (action == 'sync') or preview (action == 'check') the deterministic guarded-block sync
    for one tool. Returns True on success with no error; for `check`, also returns False if the tool
    has pending changes, so the overall exit code can signal 'needs sync'."""
    try:
        current_content = tool.target_file.read_text(encoding="utf-8") if tool.target_file.exists() else ""
        new_content = apply_guarded_block(current_content, guarded_block)
    except (OSError, ValueError) as error:
        logger.error(f"FAILED: {error}", origin=tool.name)
        if changes is not None:
            changes.append(f"invalid target {tool.target_file}: {error}")
        return False

    if new_content == current_content:
        logger.info(f"{action}: already up to date", origin=tool.name)
        return True

    if action == "check":
        diff_lines = list(
            difflib.unified_diff(
                current_content.splitlines(keepends=True),
                new_content.splitlines(keepends=True),
                fromfile=str(tool.target_file),
                tofile=str(tool.target_file),
            )
        )
        logger.info(f"{action}: pending changes --\n{''.join(diff_lines)}", origin=tool.name)
        if changes is not None:
            changes.append(f"instructions file out of date: {tool.target_file}")
        return False

    tool.target_file.parent.mkdir(parents=True, exist_ok=True)
    backup_path = backup(tool.target_file)
    if backup_path is not None:
        logger.info(f"backed up existing file to {backup_path}", origin=tool.name)
    write_text_in_place(tool.target_file, new_content)
    logger.info(f"{action}: guarded dev-guidelines block synced", origin=tool.name)
    if changes is not None:
        changes.append(f"instructions file updated: {tool.target_file}")
    return True


def get_available_skills(skills_root: Path | None = None) -> list[Path]:
    """Return all valid skill directories under skills_root (subdirectories containing SKILL.md)."""
    if skills_root is None:
        skills_root = _resolve_skills_dir()
    if not skills_root.is_dir():
        return []
    skills: list[Path] = []
    for entry in sorted(skills_root.iterdir()):
        if entry.is_dir() and (entry / "SKILL.md").is_file():
            skills.append(entry)
    return skills


@dataclass(frozen=True)
class SkillMetadata:
    """A skill's name, description, and directory, read from its ``SKILL.md`` front matter."""

    name: str
    description: str
    directory: Path


def parse_skill_metadata(skill_dir: Path) -> SkillMetadata | None:
    """Parse name and description from a skill directory's SKILL.md YAML frontmatter."""
    skill_file = skill_dir / "SKILL.md"
    if not skill_file.is_file():
        return None
    try:
        content = skill_file.read_text(encoding="utf-8")
    except OSError:
        return None

    if not content.startswith("---"):
        return None
    parts = content.split("---", 2)
    if len(parts) < 3:
        return None
    frontmatter_lines = parts[1].splitlines()

    name = ""
    description_lines: list[str] = []
    in_description = False

    for line in frontmatter_lines:
        if re.match(r"^name:\s*", line):
            name = re.sub(r"^name:\s*", "", line).strip().strip("'\"")
            in_description = False
        elif re.match(r"^description:\s*", line):
            in_description = True
            raw_val = re.sub(r"^description:\s*", "", line).strip().strip("'\"")
            if raw_val and raw_val not in (">-", ">", "|-", "|"):
                description_lines.append(raw_val)
        elif in_description:
            if line.startswith("  ") or line.startswith("\t"):
                cleaned = line.strip().strip("'\"")
                if cleaned:
                    description_lines.append(cleaned)
            elif not line.strip():
                continue
            else:
                in_description = False

    if not name:
        return None

    description = " ".join(description_lines).strip()
    return SkillMetadata(name=name, description=description, directory=skill_dir)


def format_display_skill_path(skills_dir: Path, skill_name: str) -> str:
    """Format the display path for a skill's SKILL.md file, preferring a tilde path when under home."""
    try:
        rel = skills_dir.relative_to(Path.home()).as_posix()
        return f"~/{rel}/{skill_name}/SKILL.md"
    except ValueError:
        return (skills_dir / skill_name / "SKILL.md").as_posix()


def build_skills_catalog(tool: Tool, skills: list[Path]) -> str:
    """Build a Markdown 'Available Skills' catalog for tools that lack native directory discovery.

    Tools flagged with native_skill_discovery (currently all configured tools) index their skills
    directory themselves, so no catalog block is injected. For any other tool, an on-demand catalog
    is generated so the models know when and where to read each skill.
    """
    if tool.skills_dir is None or not skills or tool.native_skill_discovery:
        return ""

    entries: list[str] = []
    for skill_dir in sorted(skills):
        meta = parse_skill_metadata(skill_dir)
        if meta is None:
            continue
        display_path = format_display_skill_path(tool.skills_dir, meta.name)
        desc = meta.description.strip()
        if desc and not desc.endswith("."):
            desc += "."
        if desc:
            entries.append(f"- **{meta.name}**: {desc}\n  Read `{display_path}`.")
        else:
            entries.append(f"- **{meta.name}**: Read `{display_path}`.")

    if not entries:
        return ""

    return (
        "## Available Skills\n"
        "When relevant to your current task, read the skill's instructions before proceeding:\n" + "\n".join(entries)
    )


def load_skills_manifest(
    skills_dir: Path,
    logger: CliLogger,
    origin: str,
    fallback_names: tuple[str, ...] | None = None,
    warn_if_missing: bool = True,
) -> list[str]:
    """Return the skill names this script previously installed in skills_dir.

    Falls back to fallback_names, with a WARN entry, when the manifest is missing or malformed."""
    fallback_names = LEGACY_SKILL_NAMES if fallback_names is None else fallback_names
    manifest_path = skills_dir / SKILLS_MANIFEST_NAME
    assumption = "assuming the legacy skill list" if fallback_names else "assuming no previously installed skills"
    if not manifest_path.is_file():
        if skills_dir.is_dir() and fallback_names and warn_if_missing:
            logger.warn(f"no {SKILLS_MANIFEST_NAME} in {skills_dir}; {assumption}", origin=origin)
        return list(fallback_names)

    try:
        data = json.loads(manifest_path.read_text(encoding="utf-8"))
        names = data["skills"]
        if (
            data.get("schema_version") != SKILLS_MANIFEST_SCHEMA_VERSION
            or data.get("source") != SKILLS_MANIFEST_SOURCE
            or not isinstance(names, list)
            or not all(isinstance(name, str) for name in names)
        ):
            raise ValueError("unexpected manifest structure")
    except (OSError, ValueError, KeyError, TypeError, AttributeError) as error:
        logger.warn(f"malformed {manifest_path} ({error}); {assumption}", origin=origin)
        return list(fallback_names)

    return sorted(set(names))


def write_skills_manifest(skills_dir: Path, skill_names: list[str]) -> None:
    """Record the skill directory names this script owns in skills_dir."""
    manifest = {
        "schema_version": SKILLS_MANIFEST_SCHEMA_VERSION,
        "source": SKILLS_MANIFEST_SOURCE,
        "skills": sorted(set(skill_names)),
    }
    content = json.dumps(manifest, indent=2) + "\n"
    manifest_path = skills_dir / SKILLS_MANIFEST_NAME
    if manifest_path.is_file() and manifest_path.read_text(encoding="utf-8") == content:
        return
    skills_dir.mkdir(parents=True, exist_ok=True)
    write_text_in_place(manifest_path, content, newline="\n")


def is_direct_child_dir(skills_dir: Path, candidate: Path) -> bool:
    """Return True only if candidate, with symlinks resolved, is a directory directly inside skills_dir."""
    try:
        resolved = candidate.resolve()
        return resolved.is_dir() and resolved.parent == skills_dir.resolve()
    except OSError:
        return False


def prune_skill_dirs(
    tool_name: str,
    skills_dir: Path,
    skill_names: list[str],
    action: str,
    logger: CliLogger,
    prune: bool,
    deprecated: bool = False,
    changes: list[str] | None = None,
) -> tuple[bool, list[str]]:
    """Report (check) or delete (sync) the named skill directories this script owns in skills_dir.
    Returns (ok, names still present afterwards); ok is False on pending changes or failed deletions.
    """
    located_in = f" in {skills_dir}" if deprecated else ""
    removed_from = f" from {skills_dir}" if deprecated else ""
    ok = True
    retained: list[str] = []
    for skill_name in sorted(set(skill_names)):
        stale_dir = skills_dir / skill_name
        if not stale_dir.exists() and not stale_dir.is_symlink():
            continue

        if not prune:
            logger.info(f"{action}: stale skill '{skill_name}'{located_in} kept (--no-prune)", origin=tool_name)
            retained.append(skill_name)
            continue

        if action == "check":
            msg = f"stale skill '{skill_name}'{located_in} would be removed"
            logger.info(msg, origin=tool_name)
            if changes is not None:
                changes.append(msg)
            retained.append(skill_name)
            ok = False
        elif action == "sync":
            try:
                if not is_direct_child_dir(skills_dir, stale_dir):
                    raise OSError(f"{stale_dir} is not a direct child directory of {skills_dir}")
                shutil.rmtree(stale_dir)
                logger.info(f"{action}: pruned stale skill '{skill_name}'{removed_from}", origin=tool_name)
                if changes is not None:
                    changes.append(f"stale skill '{skill_name}'{located_in} removed")
            except Exception as error:
                logger.error(f"FAILED to prune stale skill '{skill_name}'{removed_from}: {error}", origin=tool_name)
                if changes is not None:
                    changes.append(f"failed to prune stale skill '{skill_name}'{removed_from}: {error}")
                retained.append(skill_name)
                ok = False

    return ok, retained


def clean_legacy_skills_dir(
    tool: Tool,
    legacy_dir: Path,
    skills: list[Path],
    action: str,
    logger: CliLogger,
    prune: bool,
    changes: list[str] | None = None,
) -> bool:
    """Remove the skills this script installed in a directory the tool's skills target moved away from.
    Returns True if clean/successful, False if check has pending changes or a deletion failed.
    """
    if not legacy_dir.is_dir():
        return True

    owned_names = load_skills_manifest(legacy_dir, logger, tool.name, warn_if_missing=False)
    for skill_path in skills:
        if skill_path.name not in owned_names and (legacy_dir / skill_path.name).is_dir():
            logger.warn(
                f"possible duplicate skill '{skill_path.name}' in {legacy_dir} was not installed by this script; "
                "remove it manually if it is a leftover",
                origin=tool.name,
            )

    ok, retained = prune_skill_dirs(tool.name, legacy_dir, owned_names, action, logger, prune, deprecated=True, changes=changes)

    if action == "sync" and ok:
        manifest_path = legacy_dir / SKILLS_MANIFEST_NAME
        try:
            if retained:
                write_skills_manifest(legacy_dir, retained)
            elif manifest_path.is_file():
                manifest_path.unlink()
        except OSError as error:
            logger.error(f"FAILED to update {manifest_path}: {error}", origin=tool.name)
            ok = False

    return ok


def find_stale_skill_files(src: Path, dest: Path) -> list[Path]:
    """Return relative paths of files installed in dest that no longer exist in the source skill."""
    if not dest.is_dir():
        return []
    src_files = {p.relative_to(src) for p in src.rglob("*") if p.is_file()}
    dest_files = {p.relative_to(dest) for p in dest.rglob("*") if p.is_file()}
    return sorted(dest_files - src_files)


def remove_stale_skill_files(target_dir: Path, stale_files: list[Path]) -> None:
    """Delete stale files from an installed skill, along with any directories left empty."""
    for rel_path in stale_files:
        stale_file = target_dir / rel_path
        stale_file.unlink()
        parent = stale_file.parent
        while parent != target_dir and not any(parent.iterdir()):
            parent.rmdir()
            parent = parent.parent


def compare_skill_trees(src: Path, dest: Path) -> tuple[list[str], list[str]]:
    """Compare two skill directories.
    Returns (pending_diff_descriptions, all_rel_paths).
    """
    diffs: list[str] = []
    if not dest.exists():
        diffs.append(f"new skill '{src.name}' not yet installed at {dest}")
        return diffs, []

    src_files = {p.relative_to(src) for p in src.rglob("*") if p.is_file()}
    dest_files = {p.relative_to(dest) for p in dest.rglob("*") if p.is_file()}

    # Missing files in target
    for rel_path in sorted(src_files - dest_files):
        diffs.append(f"missing file in target: {rel_path.as_posix()}")

    # Stale files in target
    for rel_path in sorted(dest_files - src_files):
        diffs.append(f"{STALE_FILE_DIFF_PREFIX}{rel_path.as_posix()}")

    # Modified files
    for rel_path in sorted(src_files & dest_files):
        src_file = src / rel_path
        dest_file = dest / rel_path
        try:
            if src_file.read_bytes() != dest_file.read_bytes():
                diffs.append(f"content mismatch: {rel_path.as_posix()}")
        except OSError as err:
            diffs.append(f"error reading file {rel_path.as_posix()}: {err}")

    return diffs, [p.as_posix() for p in src_files]


def sync_tool_skills(
    tool: Tool,
    skills: list[Path],
    action: str,
    logger: CliLogger,
    prune: bool = True,
    changes: list[str] | None = None,
) -> bool:
    """Sync or check skills for one tool, pruning stale skills and stale skill files this script owns.
    Returns True if clean/successful, False if check has pending changes or sync failed.
    """
    if tool.skills_dir is None or not skills:
        return True

    all_ok = True
    for skill_path in skills:
        skill_name = skill_path.name
        target_dir = tool.skills_dir / skill_name
        diffs, _ = compare_skill_trees(skill_path, target_dir)
        stale_files = find_stale_skill_files(skill_path, target_dir)

        if action == "sync" and not prune and stale_files:
            for rel_path in stale_files:
                logger.info(
                    f"{action}: stale file kept in skill '{skill_name}' (--no-prune): {rel_path.as_posix()}", origin=tool.name
                )
            diffs = [diff for diff in diffs if not diff.startswith(STALE_FILE_DIFF_PREFIX)]
            stale_files = []

        if not diffs:
            logger.debug_msg(f"{action}: skill '{skill_name}' already up to date", origin=tool.name)
            continue

        if action == "check":
            diff_summary = "\n  ".join(diffs)
            logger.info(f"{action}: skill '{skill_name}' pending changes --\n  {diff_summary}", origin=tool.name)
            if changes is not None:
                changes.extend(f"skill '{skill_name}': {d}" for d in diffs)
            all_ok = False
        elif action == "sync":
            try:
                target_dir.parent.mkdir(parents=True, exist_ok=True)
                shutil.copytree(skill_path, target_dir, copy_function=copy_file_in_place, dirs_exist_ok=True)
                remove_stale_skill_files(target_dir, stale_files)
                logger.info(f"{action}: synced skill '{skill_name}'", origin=tool.name)
                if changes is not None:
                    changes.extend(f"skill '{skill_name}' updated: {d}" for d in diffs)
            except Exception as error:
                logger.error(f"FAILED to sync skill '{skill_name}': {error}", origin=tool.name)
                if changes is not None:
                    changes.append(f"failed to sync skill '{skill_name}': {error}")
                all_ok = False

    # Prune skills this script installed earlier that no longer exist in the source directory.
    current_names = {skill_path.name for skill_path in skills}
    previous_names = load_skills_manifest(tool.skills_dir, logger, tool.name, fallback_names=tool.bootstrap_skill_names)
    stale_names = sorted(set(previous_names) - current_names)
    prune_ok, retained = prune_skill_dirs(tool.name, tool.skills_dir, stale_names, action, logger, prune, changes=changes)
    all_ok = all_ok and prune_ok

    for legacy_dir in tool.legacy_skills_dirs:
        all_ok = clean_legacy_skills_dir(tool, legacy_dir, skills, action, logger, prune, changes=changes) and all_ok

    if action == "sync" and all_ok:
        try:
            write_skills_manifest(tool.skills_dir, [*current_names, *retained])
        except OSError as error:
            logger.error(f"FAILED to write {SKILLS_MANIFEST_NAME}: {error}", origin=tool.name)
            all_ok = False

    return all_ok


def run_review(tool: Tool, verbose: bool, timeout: int, logger: CliLogger) -> bool:
    """Run the agent review for one tool; return True on success or when the tool is not installed."""
    resolved_command = resolve_command(tool)
    if resolved_command is None:
        logger.info(f"skip: '{tool.command}' not found on PATH or in known locations", origin=tool.name)
        return True

    repo_root = _resolve_repo_root()
    prompt = REVIEW_PROMPT_TEMPLATE.format(repository_root=repo_root, target_file=tool.target_file)
    args = [resolved_command, *tool.review_args(prompt, tool.target_file.name, timeout)]
    # Debug-level: internal invocation detail, shown only when the log level allows DEBUG (e.g. --debug).
    logger.debug_msg(f"command line: {subprocess.list2cmdline(args)}", origin=tool.name)

    tool_env = os.environ.copy()
    if tool.name == "claude-code":
        # Remove API key to allow claude.ai login headless authentication
        tool_env.pop("ANTHROPIC_API_KEY", None)
    tool_env["PYTHONUTF8"] = "1"
    tool_env["PYTHONIOENCODING"] = "utf-8"

    if verbose:
        logger.info(f"running {resolved_command} (review) ...", origin=tool.name)
    else:
        logger.info(f"running {tool.command} (review) ...", origin=tool.name)
    try:
        result = subprocess.run(
            args,
            cwd=repo_root,
            input=prompt if tool.name != "antigravity" else None,
            capture_output=True,
            text=True,
            encoding="utf-8",
            timeout=timeout,
            env=tool_env,
        )
    except subprocess.TimeoutExpired:
        logger.error(f"FAILED: timed out after {timeout}s", origin=tool.name)
        return False
    except FileNotFoundError as error:
        logger.error(f"FAILED: could not launch '{resolved_command}': {error}", origin=tool.name)
        return False

    if result.returncode != 0:
        message = f"FAILED (exit {result.returncode})"
        if result.stderr.strip():
            message += f"\n{result.stderr.strip()}"
        logger.error(message, origin=tool.name)
        return False

    message = "review complete"
    if result.stdout.strip():
        message += f"\n{result.stdout.strip()}"
    logger.info(message, origin=tool.name)
    return True


def tool_name_argument(value: str) -> str:
    """Validate a TOOL positional argument against the configured tools."""
    from support_python.tools.agent_files_config import ToolRegistry

    registry = ToolRegistry(TOOLS)
    matched = registry.get(value)
    if matched is None:
        raise argparse.ArgumentTypeError(f"unknown tool name '{value}' (choose from: {', '.join(registry.names())})")
    return matched.name


def configure_tool_names(parser: argparse.ArgumentParser) -> None:
    """Add the optional TOOL positional arguments selecting which tools an action targets."""
    parser.add_argument(
        "tool_names",
        nargs="*",
        metavar="TOOL",
        type=tool_name_argument,
        help="tool names to process (default: all configured tools)",
    )


def configure_list_parser(parser: argparse.ArgumentParser) -> None:
    """Register output format flags for the list action."""
    ToolHarness.add_format_option(parser)


def configure_check_parser(parser: argparse.ArgumentParser) -> None:
    """Register tool names and output format flags for the check and sync actions."""
    configure_tool_names(parser)
    ToolHarness.add_format_option(parser)


def action_list(args: argparse.Namespace, logger: CliLogger) -> int:
    """Handle the ``list`` action: show the supported tools as JSON or a table; return the exit code."""
    output_format = getattr(args, "format", "text")
    if output_format == "json":
        logger.emit_json(collect_tools_info(), indent=2)
        return 0
    print_tools(logger)
    return 0


def action_sync(action: str, args: argparse.Namespace, logger: CliLogger) -> int:
    """Run the sync or check action across the selected tools."""
    selected = select_tools(args.tool_names)
    is_json = getattr(args, "format", "text") == "json"
    # A dry-run sync only reports, so it runs the read-only check path end to end.
    sync_action = "check" if args.dry_run else action
    digest_path = _resolve_digest_path()
    skills_dir = _resolve_skills_dir()
    digest = load_digest()
    if not digest:
        logger.error(
            f"digest not found or empty at {digest_path}; create it with "
            f"'agent-digest generate {{{{path}}}}... --digest {digest_path} --skills-dir {skills_dir}'",
            origin=TOOL_NAME,
        )
        return 1
    skills = get_available_skills(skills_dir)
    if skills:
        logger.debug_msg(
            f"discovered {len(skills)} skill(s) in {skills_dir.name}: {', '.join(s.name for s in skills)}", origin=TOOL_NAME
        )
    payload: list[dict[str, object]] = []
    ok = True
    for tool in selected:
        skills_catalog = build_skills_catalog(tool, skills)
        guarded_block = build_guarded_block(digest, skills_catalog)
        tool_changes: list[str] = []
        tool_ok = sync_tool(tool, guarded_block, sync_action, logger, changes=tool_changes)
        skills_ok = sync_tool_skills(tool, skills, sync_action, logger, prune=not args.no_prune, changes=tool_changes)
        ok = ok and tool_ok and skills_ok
        if is_json:
            has_invalid = any(c.startswith("invalid target ") for c in tool_changes)
            if has_invalid:
                status = "unavailable"
            elif sync_action == "sync":
                status = ("synced" if tool_changes else "up-to-date") if (tool_ok and skills_ok) else "failed"
            else:
                status = "up-to-date" if (tool_ok and skills_ok) else "changes-pending"
            payload.append({"tool": tool.name, "status": status, "changes": tool_changes})
    if is_json:
        logger.emit_json(payload, indent=2)
    return 0 if ok else 1


def action_review(args: argparse.Namespace, logger: CliLogger) -> int:
    """Run the review action across the selected tools."""
    ok = True
    for tool in select_tools(args.tool_names):
        ok = run_review(tool, args.verbose, args.timeout, logger) and ok
    return 0 if ok else 1


class SyncHarness(ToolHarness):
    """Tool harness adding tool selection and sync options to the startup banner, and reporting
    argument errors with severity indicators."""

    args: argparse.Namespace | None = None

    def create_logger(self, args: argparse.Namespace) -> CliLogger:
        """Record the parsed arguments for the startup banner, then build the logger."""
        self.args = args
        return super().create_logger(args)

    def log_startup(self, logger: CliLogger, action: str, extra: dict | None = None) -> None:
        """Emit the standard startup banner including the selected tools and action options."""
        config: dict = {}
        args = self.args
        if args is not None and action in ("sync", "check", "review"):
            config["Tools selected"] = ", ".join(args.tool_names or [tool.name for tool in TOOLS])
            if action == "review":
                config["Timeout per tool"] = f"{args.timeout}s"
            else:
                config["Dry run"] = str(args.dry_run).lower()
                config["Prune stale skills"] = str(not args.no_prune).lower()
        super().log_startup(logger, action, extra={**config, **(extra or {})})

    def log_completion(self, logger: CliLogger, action: str, exit_code: int, started_at: float) -> None:
        """Emit the completion summary, formatting long review runs in minutes and hours."""
        duration = format_duration(time.monotonic() - started_at)
        message = f"Finished {self.name} {action} in {duration} with status: {'succeeded' if exit_code == 0 else 'failed'}"
        logger.info(message, to_stdout=logger.verbose) if exit_code == 0 else logger.error(message)

    def _build_parser(self, action_name: str | None = None) -> argparse.ArgumentParser:
        """Build the action parser, reporting argument errors with severity indicators."""
        parser = super()._build_parser(action_name)
        action = self._actions.get(action_name or "")
        suffix = action.usage_suffix if action else "[options]"

        def report_error(message: str) -> None:
            usage = f"Usage: {self.name} {action_name or '<action>'} {suffix}"
            CliLogger().error(f"{message}\n{usage}")
            sys.exit(2)

        parser.error = report_error
        return parser

    def run(self, argv: Sequence[str] | None = None, extra_startup: dict | None = None) -> int:
        """Reject unknown actions with an indicator-formatted error and usage, then delegate to the harness."""
        from support_python.tools.agent_files_config import load_agent_files_config

        global REPO_ROOT, DIGEST_PATH, SKILLS_DIR, MARKER_BEGIN, MARKER_END, MARKER_BEGIN_PATTERN
        global SKILLS_MANIFEST_NAME, SKILLS_MANIFEST_SOURCE, LEGACY_SKILL_NAMES, TOOLS
        raw_args = [
            "--digest"
            if arg == "--digest-path"
            else (f"--digest={arg.split('=', 1)[1]}" if arg.startswith("--digest-path=") else arg)
            for arg in (sys.argv[1:] if argv is None else argv)
        ]
        known = {*self._actions, "help", "version", "-h", "--help", "--version"}
        if raw_args and raw_args[0] not in known:
            usage = f"Usage: {self.name} {{help|version|{'|'.join(self._actions)}}} [TOOL ...] [options]"
            CliLogger().error(f"Unknown subcommand: '{raw_args[0]}'\n{usage}")
            return 2

        is_meta = (
            not raw_args
            or raw_args[0] in ("help", "version", "config", "-h", "--help", "--version")
            or any(flag in raw_args for flag in ("-h", "--help", "--version"))
        )
        saved = (
            REPO_ROOT,
            DIGEST_PATH,
            SKILLS_DIR,
            MARKER_BEGIN,
            MARKER_END,
            MARKER_BEGIN_PATTERN,
            SKILLS_MANIFEST_NAME,
            SKILLS_MANIFEST_SOURCE,
            LEGACY_SKILL_NAMES,
            TOOLS,
        )
        try:
            if not is_meta:
                pre = argparse.ArgumentParser(add_help=False)
                for flag in (
                    "--config",
                    "--repo-root",
                    "--skills-dir",
                    "--marker",
                    "--marker-begin",
                    "--marker-end",
                    "--manifest-source",
                ):
                    pre.add_argument(flag, default=None)
                pre.add_argument("--digest", dest="digest_path", default=None)
                pre.add_argument("--legacy-skill", action="append", dest="legacy_skill_names", default=None)
                ns, _ = pre.parse_known_args(raw_args[1:])
                early_logger = self._extract_early_logger(raw_args)
                try:
                    cfg = load_agent_files_config(
                        ns.config,
                        repo_root=ns.repo_root,
                        digest_path=ns.digest_path,
                        skills_dir=ns.skills_dir,
                        marker=ns.marker,
                        marker_begin=ns.marker_begin,
                        marker_end=ns.marker_end,
                        manifest_source=ns.manifest_source,
                        legacy_skill_names=ns.legacy_skill_names,
                        base_tools=TOOLS if TOOLS != _INITIAL_TOOLS else None,
                        logger=early_logger,
                    )
                except (FileNotFoundError, ValueError) as exc:
                    early_logger.error(str(exc))
                    return 2
                finally:
                    early_logger.close()
                if REPO_ROOT == _INITIAL_REPO_ROOT:
                    REPO_ROOT = cfg.repo_root
                if DIGEST_PATH == _INITIAL_DIGEST_PATH:
                    DIGEST_PATH = cfg.digest_path
                if SKILLS_DIR == _INITIAL_SKILLS_DIR:
                    SKILLS_DIR = cfg.skills_dir
                MARKER_BEGIN, MARKER_END = cfg.marker_begin, cfg.marker_end
                MARKER_BEGIN_PATTERN = None if cfg.marker_begin_explicit else begin_marker_pattern(cfg.marker)
                SKILLS_MANIFEST_NAME, SKILLS_MANIFEST_SOURCE = cfg.manifest_name, cfg.manifest_source
                LEGACY_SKILL_NAMES, TOOLS = cfg.legacy_skill_names, list(cfg.tools)
            return super().run(raw_args, extra_startup=extra_startup)
        finally:
            (
                REPO_ROOT,
                DIGEST_PATH,
                SKILLS_DIR,
                MARKER_BEGIN,
                MARKER_END,
                MARKER_BEGIN_PATTERN,
                SKILLS_MANIFEST_NAME,
                SKILLS_MANIFEST_SOURCE,
                LEGACY_SKILL_NAMES,
                TOOLS,
            ) = saved


def system_config_path() -> Path:
    """Return the system config file location: ``%PROGRAMDATA%/agent-files/config.json`` or ``/etc/...``."""
    return SettingsSchema(TOOL_NAME, [], tiers=("system",)).path("system")


def build_settings_schema() -> SettingsSchema:
    """Return the declared settings, with the project file in the Git root of the current directory."""
    return build_schema(project_dir=find_project_root(), system_path=system_config_path())


def build_harness() -> SyncHarness:
    """Construct the CLI harness with the list, sync, check, and review actions."""
    harness = SyncHarness(
        name=TOOL_NAME,
        description="Sync this repository's guidelines digest and skills into installed AI coding tools.",
        version=TOOL_VERSION,
        copyright=TOOLS_COPYRIGHT,
        exit_codes={
            0: "success (check: no tool has pending changes)",
            1: "a tool failed, the digest is missing, a runtime error occurred, or (check) changes are pending",
            2: "invalid command-line arguments or unknown tool names",
        },
        examples=[
            f"{TOOL_NAME} list",
            f"{TOOL_NAME} check claude-code",
            f"{TOOL_NAME} sync --dry-run",
            f"{TOOL_NAME} review codex-cli --timeout 1200 --log-file logs/review.log",
        ],
        detailed_help="Configured tools:\n" + "\n".join(f"  {tool.name:<23}{tool.target_file}" for tool in TOOLS),
    )
    for flag, meta, desc in (
        ("--config", "PATH", "path to a .agent-files.json file that replaces the discovered files"),
        ("--repo-root", "PATH", "repository root directory override"),
        ("--digest", "PATH", f"digest file to install (default: ./{DEFAULT_DIGEST_RELPATH})"),
        ("--skills-dir", "PATH", f"skills directory to install (default: ./{DEFAULT_SKILLS_RELPATH})"),
        ("--marker", "NAME", "guarded block marker identifier override"),
        ("--marker-begin", "TEXT", "guarded block begin marker line override"),
        ("--marker-end", "TEXT", "guarded block end marker line override"),
        ("--manifest-source", "NAME", "skills ownership manifest source name override"),
    ):
        harness.add_global_argument(
            flag,
            **({"dest": "digest_path"} if flag == "--digest" else {}),
            default=None,
            metavar=meta,
            help=desc,
        )
    harness.add_global_argument(
        "--legacy-skill",
        action="append",
        dest="legacy_skill_names",
        default=None,
        metavar="NAME",
        help="replace legacy_skill_names with bootstrap skill name (repeatable)",
    )
    harness.add_global_argument(
        "--dry-run",
        action="store_true",
        help="report what sync would change without writing or deleting anything",
    )
    harness.add_global_argument(
        "--no-prune",
        action="store_true",
        help="keep stale skills and stale skill files on sync, reporting them only",
    )
    harness.add_global_argument(
        "--timeout",
        type=int,
        default=DEFAULT_TIMEOUT_SECONDS,
        metavar="SECONDS",
        help=f"per-tool timeout in seconds for review (default: {DEFAULT_TIMEOUT_SECONDS})",
    )
    harness.add_action(
        "list",
        "list configured tools with their executables, versions, and targets",
        handler=action_list,
        detail="Prints a table of each configured tool: command, availability, executable,\n"
        "version, global instructions file, and skills directory (or JSON with --format json).",
        configure_parser=configure_list_parser,
    )
    harness.add_action(
        "sync",
        "sync guidelines and skills into each tool's configuration (default: all tools)",
        handler=lambda args, logger: action_sync("sync", args, logger),
        detail="Installs the existing digest into the guarded block in each tool's instructions file and\n"
        "installs skills, pruning stale owned skills unless --no-prune. Never regenerates the digest;\n"
        "run 'agent-digest generate' first. Exits 1 when the digest is missing.\n"
        "With --dry-run, reports what would change without writing or deleting anything.\n"
        "With --format json, prints one JSON document with each tool's status and its planned or applied changes.",
        usage_suffix="[TOOL ...] [options]",
        configure_parser=configure_check_parser,
    )
    harness.add_action(
        "check",
        "show what sync would change, without writing anything (default: all tools)",
        handler=lambda args, logger: action_sync("check", args, logger),
        detail="Compares each tool's guarded block and installed skills against the existing digest and\n"
        "skills directory. Exits 1 when any tool has pending changes or the digest is missing.",
        usage_suffix="[TOOL ...] [options]",
        configure_parser=configure_check_parser,
    )
    harness.add_action(
        "review",
        "ask each tool's own CLI to review and improve this repository locally (default: all tools)",
        handler=action_review,
        detail="Runs each available tool headlessly against this repository with a review prompt.\n"
        "Tools may edit files locally but never commit or push; --timeout bounds each run.",
        usage_suffix="[TOOL ...] [options]",
        configure_parser=configure_tool_names,
    )
    add_config_actions(harness, build_settings_schema())
    return harness


def main(argv: Sequence[str] | None = None) -> int:
    """Run the command line and return its exit code."""
    return build_harness().run(argv)


if __name__ == "__main__":
    raise SystemExit(main())
