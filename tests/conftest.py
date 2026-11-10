"""Pytest session fixtures and guards for test isolation.

Redirects HOME, USERPROFILE, APPDATA, and XDG_CONFIG_HOME to a temporary directory
and guards against any test creating, modifying, or deleting files under the real
home directory or the repository's own .plan/ directory.
"""

from __future__ import annotations

import os
from pathlib import Path
import shutil
import tempfile
from typing import Generator

import pytest

# Determine real user home before any environment modification
REAL_HOME: Path = Path(os.environ.get("USERPROFILE") or os.environ.get("HOME") or Path.home()).resolve()

# Cache original environment values to restore on teardown
_ORIGINAL_ENV: dict[str, str | None] = {
    "HOME": os.environ.get("HOME"),
    "USERPROFILE": os.environ.get("USERPROFILE"),
    "APPDATA": os.environ.get("APPDATA"),
    "XDG_CONFIG_HOME": os.environ.get("XDG_CONFIG_HOME"),
}

# Directories inside .plan reserved for orchestrator runtime, sessions, and worktrees
EXCLUDED_PLAN_DIRS: set[str] = {"work", "sessions", "logs", "tmp", "__pycache__", ".git"}
# Directories inside .claude/skills reserved for external tool sync runtime
EXCLUDED_SKILLS_DIRS: set[str] = {"synced"}

# Create session temporary home directory immediately so module-level imports see it
_SESSION_TEMP_HOME: Path = Path(tempfile.mkdtemp(prefix="support-python-test-home-")).resolve()
os.environ["HOME"] = str(_SESSION_TEMP_HOME)
os.environ["USERPROFILE"] = str(_SESSION_TEMP_HOME)
os.environ["APPDATA"] = str(_SESSION_TEMP_HOME / "AppData" / "Roaming")
os.environ["XDG_CONFIG_HOME"] = str(_SESSION_TEMP_HOME / ".config")

(Path(os.environ["APPDATA"])).mkdir(parents=True, exist_ok=True)
(Path(os.environ["XDG_CONFIG_HOME"])).mkdir(parents=True, exist_ok=True)


def find_repo_plan_dir(start: Path | None = None) -> Path | None:
    """Find the repository's .plan directory starting from start or cwd."""
    current = (start or Path.cwd()).resolve()
    for directory in (current, *current.parents):
        if directory.name == ".plan" and directory.is_dir():
            return directory
        plan_subdir = directory / ".plan"
        if plan_subdir.is_dir():
            return plan_subdir
    return None


REPO_PLAN_DIR: Path | None = find_repo_plan_dir()


def get_guarded_home_targets(home_root: Path) -> list[Path]:
    """Return plausible paths under home that tests could touch."""
    return [
        home_root / ".claude" / "CLAUDE.md",
        home_root / ".claude" / "skills",
        home_root / ".codex" / "AGENTS.md",
        home_root / ".codex" / "skills",
        home_root / ".gemini" / "GEMINI.md",
        home_root / ".gemini" / "config" / "skills",
        home_root / ".gemini" / "bin",
        home_root / ".agents",
        home_root / ".support-python",
        home_root / ".config" / "git-repository-backup",
        home_root / ".config" / "backup-git-repos",
        home_root / ".other",
    ]


def take_snapshot(
    home_root: Path | None = None,
    plan_dir: Path | None = None,
) -> dict[str, tuple[int, int]]:
    """Record state of guarded paths under home_root and plan_dir.

    Maps normalized path string -> (mtime_ns, size) or (-1, -1) for existence-only checks.
    """
    entries: dict[str, tuple[int, int]] = {}
    h = (home_root or REAL_HOME).resolve()
    p = plan_dir if plan_dir is not None else REPO_PLAN_DIR
    if p is not None:
        p = p.resolve()

    if h.is_dir():
        # Top-level direct children of home: track existence to catch newly created/deleted files
        try:
            for item in h.iterdir():
                entries[str(item.resolve())] = (-1, -1)
        except OSError:
            pass

        # Targeted subpaths: track content modification (mtime and size)
        for target in get_guarded_home_targets(h):
            if target.is_file():
                try:
                    st = target.stat()
                    entries[str(target.resolve())] = (st.st_mtime_ns, st.st_size)
                except OSError:
                    pass
            elif target.is_dir():
                for root, dirs, files in os.walk(target):
                    dirs[:] = [d for d in dirs if d not in EXCLUDED_SKILLS_DIRS]
                    for file_name in files:
                        fp = Path(root) / file_name
                        try:
                            st = fp.stat()
                            entries[str(fp.resolve())] = (st.st_mtime_ns, st.st_size)
                        except OSError:
                            pass

    if p and p.is_dir():
        for root, dirs, files in os.walk(p):
            # Exclude worktrees, runtime sessions, and ephemeral logs from tracking
            dirs[:] = [d for d in dirs if d not in EXCLUDED_PLAN_DIRS]
            for d in dirs:
                dp = Path(root) / d
                entries[str(dp.resolve())] = (-1, -1)
            for f in files:
                if f.endswith((".log", ".lock")):
                    continue
                fp = Path(root) / f
                try:
                    st = fp.stat()
                    entries[str(fp.resolve())] = (st.st_mtime_ns, st.st_size)
                except OSError:
                    pass

    return entries


def check_snapshot_diff(
    before: dict[str, tuple[int, int]],
    after: dict[str, tuple[int, int]],
) -> dict[str, list[str]]:
    """Compare two snapshots and return created, modified, and deleted paths."""
    created = [path for path in after if path not in before]
    deleted = [path for path in before if path not in after]
    modified = [path for path in before if path in after and before[path] != after[path]]
    return {
        "created": sorted(created),
        "modified": sorted(modified),
        "deleted": sorted(deleted),
    }


def format_leak_report(diff: dict[str, list[str]]) -> str:
    """Format a human-readable leak report from snapshot differences."""
    lines = ["Real-state write guard failed! Test(s) modified protected paths:"]
    if diff["created"]:
        lines.append("  Created:")
        for path in diff["created"]:
            lines.append(f"    + {path}")
    if diff["modified"]:
        lines.append("  Modified:")
        for path in diff["modified"]:
            lines.append(f"    * {path}")
    if diff["deleted"]:
        lines.append("  Deleted:")
        for path in diff["deleted"]:
            lines.append(f"    - {path}")
    return "\n".join(lines)


@pytest.fixture(scope="session", autouse=True)
def guard_against_real_state_writes() -> Generator[Path, None, None]:
    """Session fixture enforcing isolated home environment and guarding real state."""
    # Ensure env vars point to session temp home
    os.environ["HOME"] = str(_SESSION_TEMP_HOME)
    os.environ["USERPROFILE"] = str(_SESSION_TEMP_HOME)
    os.environ["APPDATA"] = str(_SESSION_TEMP_HOME / "AppData" / "Roaming")
    os.environ["XDG_CONFIG_HOME"] = str(_SESSION_TEMP_HOME / ".config")

    home_guard = Path(os.environ["SUPPORT_PYTHON_GUARD_HOME"]) if "SUPPORT_PYTHON_GUARD_HOME" in os.environ else REAL_HOME
    plan_guard = Path(os.environ["SUPPORT_PYTHON_GUARD_PLAN"]) if "SUPPORT_PYTHON_GUARD_PLAN" in os.environ else REPO_PLAN_DIR

    before = take_snapshot(home_root=home_guard, plan_dir=plan_guard)

    yield _SESSION_TEMP_HOME

    after = take_snapshot(home_root=home_guard, plan_dir=plan_guard)
    diff = check_snapshot_diff(before, after)

    # Restore original environment
    for key, value in _ORIGINAL_ENV.items():
        if value is None:
            os.environ.pop(key, None)
        else:
            os.environ[key] = value

    # Clean up temporary home
    shutil.rmtree(_SESSION_TEMP_HOME, ignore_errors=True)

    if diff["created"] or diff["modified"] or diff["deleted"]:
        report = format_leak_report(diff)
        pytest.fail(report, pytrace=False)
