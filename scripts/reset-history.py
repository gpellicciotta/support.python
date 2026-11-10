#!/usr/bin/env python3
# Copyright (c) Giovanni Pellicciotta
"""One-off: start the current repo completely fresh from its current codebase at a chosen version.

DESTRUCTIVE and mostly irreversible. Acts on the Git repository containing the current directory.
Run the steps in order:

    backup DIR       mirror-clone the repo (all history, tags, branches) into DIR, outside the repo
    reinit           delete all plan tasks, reset CHANGELOG/version to vX.Y.Z-pre, replace local
                     history with one root commit, purge old local objects
    recreate-remote  delete the GitHub repo (releases, tags, branches, PRs, runs, packages) and
                     create it again, private and EMPTY (nothing is pushed); restore description,
                     topics, and Actions secrets (asked for interactively)          (outbound)

Then push, publish, and release as the project requires.
"""

from __future__ import annotations

import argparse
import getpass
import json
import re
import shlex
import shutil
import subprocess
import sys
from pathlib import Path

_SRC = Path(__file__).resolve().parent.parent / "src"
if _SRC.is_dir():
    sys.path.insert(0, str(_SRC))

from support_python.devops.release import confirm_typed, write_version  # noqa: E402
from support_python.git import get_current_branch, get_default_branch, get_github_repo, get_remote_url, get_repo_root  # noqa: E402
from support_python.version import get_project_version  # noqa: E402

#: Root of the Git repository containing the current directory; set by main().
REPO_ROOT = Path.cwd()

EXCLUDED_SCRIPTS = ("scripts/reset-history.py", "scripts/migrate-namespace.py")
DEFAULT_VERSION = "1.0.0"
DEFAULT_ENTRY = "- Initial release."


def version_line(prog: str) -> str:
    """Returns the standard `{name} v{version} - {copyright}` line for --version."""
    return f"{prog} v{get_project_version(Path(__file__).resolve().parent)} - Copyright (c) Giovanni Pellicciotta"


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
    if not confirm_typed(["", *summary, ""], phrase):
        sys.exit("aborted")


def read(name: str) -> str:
    """Read a repository file as UTF-8 without newline translation."""
    with open(REPO_ROOT / name, encoding="utf-8", newline="") as f:
        return f.read()


def read_changelog() -> tuple[str, str]:
    """Return CHANGELOG.md as LF text plus its on-disk line ending."""
    text = read("CHANGELOG.md")
    return text.replace("\r\n", "\n"), "\r\n" if "\r\n" in text else "\n"


def write_changelog(text: str, newline: str) -> None:
    """Write LF text to CHANGELOG.md using the given line ending."""
    with open(REPO_ROOT / "CHANGELOG.md", "w", encoding="utf-8", newline="") as f:
        f.write(text.replace("\n", newline))


def set_version(version: str) -> None:
    """Write the project version into the first supported version file."""
    try:
        write_version(REPO_ROOT, version)
    except (OSError, ValueError) as exc:
        die(str(exc))


def origin() -> tuple[str, str]:
    """Return the (owner, repo) of the GitHub origin remote."""
    repo = get_github_repo(REPO_ROOT)
    if repo is None:
        die(f"cannot parse origin {get_remote_url(REPO_ROOT) or '(missing)'}")
    return repo


def default_branch() -> str:
    """Return origin's default branch, falling back to the current branch, then 'main'."""
    branch = get_default_branch(REPO_ROOT) or get_current_branch(REPO_ROOT)
    return branch if branch and branch != "(detached)" else "main"


def repo_slug() -> str:
    owner, repo = origin()
    return f"{owner}/{repo}"


def mirror_name() -> str:
    return f"{REPO_ROOT.name}-mirror.git"


def cmd_backup(args: argparse.Namespace) -> None:
    target = Path(args.dir).resolve()
    if REPO_ROOT in (target, *target.parents):
        die("backup directory must be outside the repository")
    target.mkdir(parents=True, exist_ok=True)
    mirror = target / mirror_name()
    if mirror.exists():
        die(f"{mirror} already exists")
    run(["git", "clone", "--mirror", str(REPO_ROOT), str(mirror)])
    print(f"backup written to {mirror}")
    print("NOTE: GitHub Packages are NOT part of this backup and cannot be restored once deleted.")


def require_backup(dir_: str) -> None:
    mirror = Path(dir_).resolve() / mirror_name()
    if not (mirror / "HEAD").exists():
        die(f"no backup at {mirror}; run 'backup' first")


def gh_json(args: list[str]) -> list | dict:
    return json.loads(run(["gh", *args], capture=True) or "[]")


def token_scopes() -> set[str]:
    out = run(["gh", "api", "-i", "user"], capture=True)
    match = re.search(r"^x-oauth-scopes:\s*(.*)$", out, re.IGNORECASE | re.MULTILINE)
    return {s.strip() for s in match.group(1).split(",")} if match else set()


def user_packages(package_type: str | None) -> list[dict]:
    if not package_type:
        return []
    return gh_json(["api", f"user/packages?package_type={package_type}&per_page=100"])


def repo_packages(slug: str, package_type: str | None) -> list[str]:
    return [p["name"] for p in user_packages(package_type) if (p.get("repository") or {}).get("full_name") == slug]


def cmd_recreate_remote(args: argparse.Namespace) -> None:
    """Delete the GitHub repo (and with it releases, tags, branches, PRs, runs) and create it anew, empty (no push)."""
    require_backup(args.backup_dir)
    if run(["git", "rev-list", "--count", "HEAD"], capture=True) != "1":
        die("HEAD has more than one commit; run 'reinit' first")
    slug = repo_slug()
    scopes = token_scopes()
    required = {"delete_repo", "repo", "workflow"} | ({"delete:packages"} if args.package_type else set())
    missing = required - scopes
    if missing:
        die(f"the gh token lacks scopes {sorted(missing)}; use a token that has them (current: {sorted(scopes)})")

    info = gh_json(["repo", "view", slug, "--json", "description,homepageUrl,repositoryTopics,isPrivate"])
    topics = [t["name"] for t in (info.get("repositoryTopics") or [])]
    secrets = [s["name"] for s in gh_json(["api", f"repos/{slug}/actions/secrets", "--jq", ".secrets"])]
    variables = gh_json(["api", f"repos/{slug}/actions/variables", "--jq", ".variables"])
    if variables:
        die(f"repo has Actions variables {[v['name'] for v in variables]}; this script does not restore them")
    values = {}
    if not args.drop_secrets:
        values = {name: getpass.getpass(f"Value for Actions secret {name} (not echoed; empty = drop it): ") for name in secrets}
    values = {name: value for name, value in values.items() if value}
    packages = repo_packages(slug, args.package_type)

    confirm(
        [
            f"IRREVERSIBLE: delete GitHub repo {slug} and create it again, private and empty (nothing is pushed).",
            "Lost for good: releases, tags, branches, PRs, Actions runs, stars, watchers.",
            f"Packages linked to the repo (deleted afterwards if they survive): {packages}",
            f"Restored: description, topics {topics}, secrets {sorted(values)} (dropped: {sorted(set(secrets) - set(values))}).",
        ],
        f"delete and recreate {slug}",
    )
    run(["gh", "repo", "delete", slug, "--yes"])
    run(["git", "remote", "remove", "origin"])
    create = ["gh", "repo", "create", slug, "--private", "--source", ".", "--remote", "origin"]
    if info.get("description"):
        create += ["--description", info["description"]]
    if info.get("homepageUrl"):
        create += ["--homepage", info["homepageUrl"]]
    run(create)
    for topic in topics:
        run(["gh", "repo", "edit", slug, "--add-topic", topic])
    for name, value in values.items():
        print(f"$ gh secret set {name} --repo {slug}   (value from stdin)")
        subprocess.run(["gh", "secret", "set", name, "--repo", slug], input=value, text=True, check=True, cwd=REPO_ROOT)
    survivors = {p["name"] for p in user_packages(args.package_type)} & set(packages)
    for name in sorted(survivors):
        run(["gh", "api", "-X", "DELETE", f"user/packages/{args.package_type}/{name}"])
    print(f"\nRecreated {slug} empty. origin points at it. Push when ready.")
    print(f"After the first push, check that the default branch is {args.branch}.")


def reset_plan() -> None:
    tasks = REPO_ROOT / ".plan" / "tasks"
    if not tasks.is_dir():
        return
    pending = [line for line in read("PLAN.md").splitlines() if re.match(r"\s*- \[[ ~!]\] ", line)]
    if pending:
        die("PLAN.md still has open tasks; finish or cancel them first:\n  " + "\n  ".join(pending))
    run(["plan", "gc"])
    for child in tasks.iterdir():
        if child.is_dir():
            shutil.rmtree(child)
        else:
            child.unlink()
    (tasks / ".gitkeep").write_text("", encoding="utf-8")


def reset_changelog_and_version(version: str, entry: str) -> None:
    text, newline = read_changelog()
    match = re.search(r"^---\n", text, re.MULTILINE)
    if not match:
        die("CHANGELOG.md has no '---' line ending its introduction")
    write_changelog(text[: match.end()] + f"\n## v{version}-pre\n\n{entry.strip()}\n", newline)
    set_version(f"{version}-pre")


def cmd_reinit(args: argparse.Namespace) -> None:
    require_backup(args.backup_dir)
    if run(["git", "branch", "--show-current"], capture=True) != args.branch:
        die(f"not on {args.branch}")
    dirty = run(["git", "status", "--porcelain"], capture=True)
    confirm(
        [
            "Replaces ALL local history with one root commit of the current working tree.",
            "Deletes all plan tasks, local tags, reflogs and old objects (the mirror backup keeps them).",
            "Uncommitted changes (included in the root commit):",
            dirty or "  (none)",
        ],
        "reinit",
    )
    entry = Path(args.entry_file).read_text(encoding="utf-8") if args.entry_file else DEFAULT_ENTRY
    reset_plan()
    reset_changelog_and_version(args.new_version, entry)
    run(["git", "checkout", "--orphan", "fresh"])
    run(["git", "rm", "-r", "-q", "--cached", "--ignore-unmatch", *EXCLUDED_SCRIPTS])
    exclude = REPO_ROOT / ".git" / "info" / "exclude"
    existing = exclude.read_text(encoding="utf-8") if exclude.exists() else ""
    exclude.write_text(existing + "".join(f"/{s}\n" for s in EXCLUDED_SCRIPTS if f"/{s}" not in existing), encoding="utf-8")
    run(["git", "add", "-A"])
    run(["git", "commit", "-m", f"Started the repository fresh at version {args.new_version}-pre from the current codebase."])
    run(["git", "branch", "-M", args.branch])
    for branch in run(["git", "branch", "--format=%(refname:short)"], capture=True).splitlines():
        if branch != args.branch:
            run(["git", "branch", "-D", branch])
    for tag in run(["git", "tag"], capture=True).splitlines():
        run(["git", "tag", "-d", tag])
    for ref in run(["git", "for-each-ref", "--format=%(refname)", "refs/remotes"], capture=True).splitlines():
        run(["git", "update-ref", "-d", ref])
    run(["git", "reflog", "expire", "--expire=now", "--all"])
    run(["git", "gc", "--prune=now"])
    if (REPO_ROOT / ".plan").is_dir():
        run(["plan", "tasks", "validate"], check=False)
    print("\nNext: build and test, then recreate-remote.")


def main() -> int:
    global REPO_ROOT
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--version", action="version", version=version_line("reset-history"))
    parser.add_argument("--branch", default=None, help="branch to keep (default: origin's default branch)")
    sub = parser.add_subparsers(dest="step", required=True)
    step = sub.add_parser("backup")
    step.add_argument("dir", help="directory outside the repo to hold the mirror backup")
    step.set_defaults(fn=cmd_backup)
    for name, fn in (("reinit", cmd_reinit), ("recreate-remote", cmd_recreate_remote)):
        step = sub.add_parser(name)
        step.add_argument("--backup-dir", required=True, help="the DIR given to 'backup'")
        step.set_defaults(fn=fn)
        if name == "reinit":
            step.add_argument("--new-version", default=DEFAULT_VERSION, help="fresh start version (default: %(default)s)")
            step.add_argument("--entry-file", help=f"file with the initial CHANGELOG bullets (default: '{DEFAULT_ENTRY}')")
        else:
            step.add_argument("--drop-secrets", action="store_true", help="do not prompt for Actions secrets; drop them all")
            step.add_argument("--package-type", help="also delete linked GitHub packages of this type (maven, npm, ...)")
    args = parser.parse_args()
    root = get_repo_root(Path.cwd())
    if root is None:
        die("not inside a Git repository")
    REPO_ROOT = root
    args.branch = args.branch or default_branch()
    args.fn(args)
    return 0


if __name__ == "__main__":
    sys.exit(main())
