#!/usr/bin/env python3
# Copyright (c) Giovanni Pellicciotta
"""Move the current repo from one namespace/brand word to another (e.g. --old acme --new widgets).

Run the steps in order, one at a time, reviewing the result of each:

    rewrite      rename dirs, rewrite text, bump to the next major as X.0.0-pre, commit
    build        run the build command (default: scripts/devops.py check)
    rename-repo  rename the GitHub repo and repoint origin           (outbound)
    freeze       freeze CHANGELOG/version as X.0.0, commit
    push         push the branch                                     (outbound)
    publish      check CI is green, run the publish command          (outbound)
    finish       mark released, commit, tag, push, GitHub Release    (outbound)

Outbound steps print the exact command and need a typed "yes". The version lives in gradle.properties,
pyproject.toml, or package.json, whichever exists first. The script acts on the Git repository
containing the current directory.
"""

from __future__ import annotations

import argparse
import datetime
import json
import os
import re
import shlex
import subprocess
import sys
import tempfile
import time
from pathlib import Path

_SRC = Path(__file__).resolve().parent.parent / "src"
if _SRC.is_dir():
    sys.path.insert(0, str(_SRC))

from support_python.devops.release import (  # noqa: E402
    confirm_typed,
    extract_release_notes,
    next_dev_version,
    read_version,
    release_version,
    write_version,
)
from support_python.git import get_current_branch, get_default_branch, get_github_repo, get_remote_url, get_repo_root  # noqa: E402
from support_python.version import get_project_version  # noqa: E402

#: Root of the Git repository containing the current directory; set by main().
ROOT = Path.cwd()


def version_line(prog: str) -> str:
    """Returns the standard `{name} v{version} - {copyright}` line for --version."""
    return f"{prog} v{get_project_version(Path(__file__).resolve().parent)} - Copyright (c) Giovanni Pellicciotta"


SELF = "scripts/migrate-namespace.py"
# plan owns .plan and PLAN.md; the changelog is edited by hand below; the scripts must not rewrite themselves
SKIP_PREFIXES = (".plan/", "PLAN.md", "CHANGELOG.md", SELF, "scripts/reset-history.py")
PRE_HEADING_RE = re.compile(r"^## v(\d+)\.(\d+)\.(\d+)-pre$", re.MULTILINE)


def die(message: str) -> None:
    """Exit with a severity-tagged error message."""
    sys.exit(f"**[ERROR]**: {message}")


def run(args: list[str], capture: bool = False, check: bool = True) -> str:
    """Echo and run a command in the repository root. Returns trimmed stdout when capturing."""
    print(f"$ {shlex.join(args)}")
    result = subprocess.run(args, cwd=ROOT, check=check, text=True, capture_output=capture)
    return result.stdout.strip() if capture else ""


def outbound(args: list[str]) -> None:
    """Run a command that leaves this machine only after the user types 'yes'."""
    if not confirm_typed(["", f"OUTBOUND: {shlex.join(args)}", ""], "yes"):
        sys.exit("aborted")
    run(args)


def read(name: str) -> str:
    """Read a repository file as UTF-8 without newline translation."""
    with open(ROOT / name, encoding="utf-8", newline="") as f:
        return f.read()


def write(name: str, text: str) -> None:
    """Write a repository file as UTF-8 without newline translation."""
    with open(ROOT / name, "w", encoding="utf-8", newline="") as f:
        f.write(text)


def read_changelog() -> tuple[str, str]:
    """Return CHANGELOG.md as LF text plus its on-disk line ending."""
    text = read("CHANGELOG.md")
    return text.replace("\r\n", "\n"), "\r\n" if "\r\n" in text else "\n"


def write_changelog(text: str, newline: str) -> None:
    """Write LF text to CHANGELOG.md using the given line ending."""
    write("CHANGELOG.md", text.replace("\n", newline))


def current_version() -> str:
    """Read the project version, including any -pre suffix."""
    try:
        return read_version(ROOT)
    except (OSError, ValueError) as exc:
        die(str(exc))
        raise AssertionError("unreachable") from exc


def set_version(version: str) -> None:
    """Write the project version into the first supported version file."""
    try:
        write_version(ROOT, version)
    except (OSError, ValueError) as exc:
        die(str(exc))


def origin() -> tuple[str, str]:
    """Return the (owner, repo) of the GitHub origin remote."""
    repo = get_github_repo(ROOT)
    if repo is None:
        die(f"cannot parse origin {get_remote_url(ROOT) or '(missing)'}")
    return repo


def default_branch() -> str:
    """Return origin's default branch, falling back to the current branch, then 'main'."""
    branch = get_default_branch(ROOT) or get_current_branch(ROOT)
    return branch if branch and branch != "(detached)" else "main"


def tracked_files() -> list[str]:
    return run(["git", "ls-files", "--cached", "--others", "--exclude-standard"], capture=True).splitlines()


def require_clean_branch(branch: str) -> None:
    dirty = [line for line in run(["git", "status", "--porcelain"], capture=True).splitlines() if not line.endswith(SELF)]
    if dirty:
        die("working tree is not clean; commit or stash first")
    if run(["git", "branch", "--show-current"], capture=True) != branch:
        die(f"not on {branch}")


def read_safe(name: str) -> str:
    try:
        return read(name)
    except (UnicodeDecodeError, OSError):
        return ""


def case_preserving(new: str, text: str) -> str:
    if text.isupper():
        return new.upper()
    if text[0].isupper():
        return new.capitalize()
    return new


def new_repo_name(args: argparse.Namespace) -> str:
    _, repo = origin()
    return args.repo_name or re.sub(re.escape(args.old), args.new, repo, flags=re.IGNORECASE)


def ensure_absent(rel: str) -> None:
    """Make sure a rename target is free; `git mv` would otherwise move the source *inside* an existing target.

    Empty leftover directories (git leaves them behind after a reset) are removed; anything else aborts.
    """
    target = ROOT / rel
    for dirpath, _, _ in os.walk(target, topdown=False):
        try:
            os.rmdir(dirpath)
        except OSError:
            pass
    if target.exists():
        die(f"{rel} already exists and is not empty; remove it first")


def rename_dirs(old: str, new: str) -> None:
    while True:
        for path in tracked_files():
            parts = path.split("/")
            if path.startswith(SKIP_PREFIXES) or old not in parts[:-1]:
                continue
            i = parts.index(old)
            ensure_absent("/".join(parts[:i] + [new]))
            run(["git", "mv", "/".join(parts[: i + 1]), "/".join(parts[:i] + [new])])
            break
        else:
            return


def rewrite_text(args: argparse.Namespace) -> int:
    specific = dict(r.split("=", 1) for r in args.replace)
    _, repo = origin()
    specific[repo] = new_repo_name(args)
    parts = [re.escape(n) for n in sorted(specific, key=len, reverse=True)]
    pattern = re.compile("|".join(parts + [f"(?i:{re.escape(args.old)})"]))

    def repl(match: re.Match) -> str:
        return specific.get(match.group(0)) or case_preserving(args.new, match.group(0))

    changed = 0
    for name in tracked_files():
        if name.startswith(SKIP_PREFIXES):
            continue
        try:
            text = read(name)
        except (UnicodeDecodeError, OSError):
            continue  # binary
        new_text = pattern.sub(repl, text)
        if new_text != text:
            write(name, new_text)
            changed += 1
    return changed


def next_major(version: str) -> str:
    try:
        return release_version(next_dev_version(version, "major"))
    except ValueError as exc:
        die(str(exc))
        raise AssertionError("unreachable") from exc


def update_changelog_for_rewrite(args: argparse.Namespace, version: str) -> None:
    text, newline = read_changelog()
    match = PRE_HEADING_RE.search(text)
    if not match:
        die("CHANGELOG.md has no '## vX.Y.Z-pre' heading")
    note = (
        f"\n\n- **[breaking]** Renamed `{args.old}` to `{args.new}`. Consumers must update dependency coordinates, "
        f"imports, and every config file, resource path, or logger name that mentions `{args.old}`. "
        f"Versions up to the last `{args.old}` release stay available under the old names."
    )
    write_changelog(text[: match.start()] + f"## v{version}-pre" + note + text[match.end() :], newline)


def cmd_rewrite(args: argparse.Namespace) -> None:
    require_clean_branch(args.branch)
    version = args.new_version or next_major(current_version())
    rename_dirs(args.old, args.new)
    print(f"rewrote {rewrite_text(args)} files")
    set_version(f"{version}-pre")
    update_changelog_for_rewrite(args, version)
    leftovers = [f for f in tracked_files() if not f.startswith(SKIP_PREFIXES) and args.old in read_safe(f).lower()]
    if leftovers:
        print("**[WARN]** : leftover references:", *leftovers, sep="\n  ")
    run(["git", "add", "-A"])
    run(["git", "commit", "-m", f"Renamed {args.old} to {args.new} and bumped the version to {version}-pre."])


def cmd_build(args: argparse.Namespace) -> None:
    command = args.build_command or f"{shlex.quote(sys.executable)} scripts/devops.py check"
    run(shlex.split(command))


def cmd_rename_repo(args: argparse.Namespace) -> None:
    owner, repo = origin()
    new = new_repo_name(args)
    if repo == new:
        print("repo already named", new)
        return
    outbound(["gh", "repo", "rename", new, "-R", f"{owner}/{repo}", "--yes"])
    run(["git", "remote", "set-url", "origin", f"https://github.com/{owner}/{new}.git"])


def top_heading(text: str) -> re.Match:
    match = re.search(r"^## v\S+.*$", text, re.MULTILINE)
    if not match:
        die("CHANGELOG.md has no version heading")
    return match


def cmd_freeze(args: argparse.Namespace) -> None:
    require_clean_branch(args.branch)
    text, newline = read_changelog()
    match = PRE_HEADING_RE.fullmatch(top_heading(text).group(0))
    if not match:
        die("top CHANGELOG heading is not '-pre'")
    major, minor, patch = (int(g) for g in match.groups())
    version = f"{major}.{minor}.{patch}"
    if current_version() != f"{version}-pre":
        die(f"version file says {current_version()}, CHANGELOG says {version}-pre")
    today = datetime.date.today().isoformat()
    top = top_heading(text)
    text = text[: top.start()] + f"## v{next_dev_version(version)}\n\n---\n\n## v{version} [{today}]" + text[top.end() :]
    write_changelog(text, newline)
    set_version(version)
    run(["git", "add", "-A"])
    run(["git", "commit", "-m", f"Froze version {version} with the rename."])


def cmd_push(args: argparse.Namespace) -> None:
    outbound(["git", "push", "origin", args.branch])


def cmd_publish(args: argparse.Namespace) -> None:
    if not args.publish_command:
        die('publish needs --publish-command, e.g. "./gradlew publish" or "twine upload dist/*"')
    require_clean_branch(args.branch)
    sha = run(["git", "rev-parse", "HEAD"], capture=True)
    deadline = time.monotonic() + 15 * 60
    while True:
        runs = json.loads(run(["gh", "run", "list", "--commit", sha, "--json", "status,conclusion,name"], capture=True))
        print(runs)
        if not runs:
            die("no CI run found for HEAD; push first")
        if all(r["status"] == "completed" for r in runs):
            break
        if time.monotonic() > deadline:
            die("CI still running after 15 minutes; re-run publish later")
        print("CI still running; checking again in 20 seconds")
        time.sleep(20)
    if any(r["conclusion"] != "success" for r in runs):
        die("CI for HEAD is red; fix before publishing")
    outbound(shlex.split(args.publish_command))


def release_notes(text: str, version: str) -> str:
    try:
        return extract_release_notes(text, version)
    except ValueError:
        return ""


def cmd_finish(args: argparse.Namespace) -> None:
    require_clean_branch(args.branch)
    version = current_version()
    text, newline = read_changelog()
    today = datetime.date.today().isoformat()
    new_text = re.sub(
        rf"^(## v{re.escape(version)}) \[\d{{4}}-\d{{2}}-\d{{2}}\]$", rf"\1 [released: {today}]", text, count=1, flags=re.MULTILINE
    )
    if new_text == text:
        die(f"no frozen '## v{version} [date]' heading found")
    write_changelog(new_text, newline)
    run(["git", "add", "-A"])
    run(["git", "commit", "-m", f"Marked version {version} as released."])
    tag = f"v{version}"
    run(["git", "tag", "-a", tag, "-m", f"Release {tag}"])
    outbound(["git", "push", "origin", args.branch, tag])
    with tempfile.NamedTemporaryFile("w", suffix=".md", delete=False, encoding="utf-8") as f:
        f.write(release_notes(new_text, version))
    outbound(["gh", "release", "create", tag, "--title", tag, "--notes-file", f.name])


def main() -> int:
    global ROOT
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--version", action="version", version=version_line("migrate-namespace"))
    parser.add_argument("--old", required=True, help="word to replace")
    parser.add_argument("--new", required=True, help="replacement word")
    parser.add_argument("--repo-name", help="new GitHub repo name (default: the old name with the word replaced)")
    parser.add_argument("--replace", action="append", default=[], metavar="OLD=NEW", help="extra exact replacement, repeatable")
    parser.add_argument("--new-version", help="new version for 'rewrite' (default: next major, X.0.0)")
    parser.add_argument("--branch", help="release branch (default: origin's default branch)")
    parser.add_argument("--build-command", help="command run by 'build' (default: scripts/devops.py check)")
    parser.add_argument("--publish-command", help="command run by 'publish' after CI is green")
    sub = parser.add_subparsers(dest="step", required=True)
    steps = (
        ("rewrite", cmd_rewrite),
        ("build", cmd_build),
        ("rename-repo", cmd_rename_repo),
        ("freeze", cmd_freeze),
        ("push", cmd_push),
        ("publish", cmd_publish),
        ("finish", cmd_finish),
    )
    for name, fn in steps:
        sub.add_parser(name).set_defaults(fn=fn)
    args = parser.parse_args()
    root = get_repo_root(Path.cwd())
    if root is None:
        die("not inside a Git repository")
    ROOT = root
    args.branch = args.branch or default_branch()
    args.fn(args)
    return 0


if __name__ == "__main__":
    sys.exit(main())
