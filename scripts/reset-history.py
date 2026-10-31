#!/usr/bin/env python3
# Copyright (c) Giovanni Pellicciotta
"""One-off: start this repo completely fresh from the current codebase at a chosen version.

DESTRUCTIVE and mostly irreversible. Run the steps in order:

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
import shutil
import subprocess
import sys
from pathlib import Path

from _repo_common import (
    REPO_ROOT,
    confirm,
    default_branch,
    die,
    origin,
    read,
    read_changelog,
    run,
    set_version,
    write_changelog,
)

EXCLUDED_SCRIPTS = ("scripts/reset-history.py", "scripts/migrate-namespace.py")
DEFAULT_VERSION = "1.0.0"
DEFAULT_ENTRY = "- Initial release."


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
    reset_changelog_and_version(args.version, entry)
    run(["git", "checkout", "--orphan", "fresh"])
    run(["git", "rm", "-r", "-q", "--cached", "--ignore-unmatch", *EXCLUDED_SCRIPTS])
    exclude = REPO_ROOT / ".git" / "info" / "exclude"
    existing = exclude.read_text(encoding="utf-8") if exclude.exists() else ""
    exclude.write_text(existing + "".join(f"/{s}\n" for s in EXCLUDED_SCRIPTS if f"/{s}" not in existing), encoding="utf-8")
    run(["git", "add", "-A"])
    run(["git", "commit", "-m", f"Started the repository fresh at version {args.version}-pre from the current codebase."])
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
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
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
            step.add_argument("--version", default=DEFAULT_VERSION, help="fresh start version (default: %(default)s)")
            step.add_argument("--entry-file", help=f"file with the initial CHANGELOG bullets (default: '{DEFAULT_ENTRY}')")
        else:
            step.add_argument("--drop-secrets", action="store_true", help="do not prompt for Actions secrets; drop them all")
            step.add_argument("--package-type", help="also delete linked GitHub packages of this type (maven, npm, ...)")
    args = parser.parse_args()
    args.branch = args.branch or default_branch()
    args.fn(args)
    return 0


if __name__ == "__main__":
    sys.exit(main())
