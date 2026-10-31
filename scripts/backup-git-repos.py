#!/usr/bin/env python3
"""Backs up Git repos to bare mirror repos and encrypted 7-Zip archives.

Discovers every Git repo below configured root directories. The mirror layer force-pushes all
branches and tags to one bare repo per project, keeping a reflog so rewritten history stays
recoverable. The archive layer stores a password-encrypted 7-Zip archive holding a `git bundle`
of each changed project. Locations come from the command line or a JSON config file. The archive
password can come from the OS keyring through the optional `keyring` package, for unattended runs.
The restore action rebuilds a working repo from one mirror or archive.
"""

from __future__ import annotations

import argparse
from dataclasses import dataclass
import getpass
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
from typing import Any, Callable, Sequence

# Reconfigure stdout/stderr to UTF-8 on Windows
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

from _tool_common import COPYRIGHT, PROJECT_VERSION, ToolLogger, get_full_version  # noqa: E402
from _harness import ToolHarness  # noqa: E402

TOOL_NAME = "backup-git-repos"
TOOL_VERSION = PROJECT_VERSION
DESCRIPTION = "Backs up Git repos to bare mirror repos and encrypted 7-Zip archives."

EXIT_CODES = {
    0: "success",
    1: "a backup or restore failed, or the archive password was rejected or mismatched",
    2: "invalid arguments or configuration, or no usable password source",
    130: "interrupted with Ctrl+C; a partial restore target is cleaned up when possible",
}
CONFIG_KEYS = ("roots", "mirror-dir", "archive-dir", "depth", "seven-zip", "password-env", "password-keyring")
DEFAULT_DEPTH = 2
STATE_FILE_NAME = "backup-state.json"
PASSWORD_CHECK_NAME = "password-check.7z"
PASSWORD_CHECK_TEXT = "backup-git-repos password check\n"
SEVEN_ZIP_NAMES = ("7z", "7zz", "7za")
SEVEN_ZIP_TIMEOUT_SECONDS = 3600
BACKED_UP_REFS = ("refs/heads", "refs/tags")
KEYRING_USER = "archive-password"
PREFERRED_BRANCHES = ("refs/heads/main", "refs/heads/master")


class UsageError(Exception):
    """Invalid arguments or configuration (exit code 2)."""


class BackupError(Exception):
    """Operational failure while backing up or restoring a repo (exit code 1)."""


@dataclass
class Settings:
    """Resolved backup settings after merging config file and command-line values."""

    roots: list[Path]
    mirror_dir: Path | None
    archive_dir: Path | None
    depth: int
    seven_zip: str | None
    password_env: str | None
    password_keyring: str | None
    dry_run: bool


@dataclass
class RestoreSource:
    """A backup to restore from: a bare mirror directory or an encrypted archive file."""

    kind: str
    path: Path


def get_version_banner() -> str:
    """Return single-line formatted version string."""
    return f"{TOOL_NAME} v{get_full_version()} - {COPYRIGHT}"


def format_exit_codes() -> str:
    """Return the exit code lines of the help screen."""
    return "\n".join(f"  {code:<4}{text}" for code, text in sorted(EXIT_CODES.items()))


def get_long_usage(verbose: bool = False) -> str:
    """Return full help screen formatted per CLI guidelines."""
    base = f"""{get_version_banner()}

{DESCRIPTION}

Usage:
  backup-git-repos backup [options]
  backup-git-repos list [options]
  backup-git-repos restore (--source PATH | --name NAME) --target DIR [options]
  backup-git-repos set-password --archive-dir PATH --password-keyring NAME
  backup-git-repos version
  backup-git-repos help [--verbose]

Actions:
  backup                 back up all discovered repos
  list                   list discovered repos and their backup names without writing anything
  restore                rebuild a working repo from one mirror or archive
  set-password           verify the archive password and store it in the OS keyring
  version                show version information and exit
  help                   show help message and exit (use --verbose for details)

Options:
  -h, --help             show help message and exit
  --version              show version information and exit
  --config PATH          JSON config file (default: ~/.config/backup-git-repos/config.json if present)
  --root PATH            directory to scan for repos; repeatable, replaces config roots
  --depth N              maximum scan depth below each root (default: {DEFAULT_DEPTH})
  --mirror-dir PATH      directory holding one bare mirror repo per project
  --no-mirror            disable the mirror layer
  --archive-dir PATH     directory holding one encrypted archive per project
  --no-archive           disable the archive layer
  --source PATH          restore from this mirror directory ({{{{name}}}}.git) or archive file ({{{{name}}}}.7z)
  --name NAME            restore the backup with this name from the mirror or archive directory
  --target DIR           directory to restore into; must be absent or empty
  --seven-zip PATH       7-Zip executable (default: 7z, 7zz or 7za on PATH)
  --password-env NAME    read the archive password from this environment variable
  --password-keyring NAME
                         read the archive password from this OS keyring service
  --dry-run              report planned actions without writing anything
  -v, --verbose          enable verbose output logging
  --log-file PATH        append operational logs to specified file
  --log-level LEVEL      logging severity threshold (DEBUG, INFO, WARN, ERROR; default: INFO)
  --debug                enable debug output logging

Exit codes:
{format_exit_codes()}
"""
    if not verbose:
        return base

    return f"""{base}
Detailed Action Descriptions:
  backup
      Discovers repos below each root: directories containing a .git directory, up to --depth
      levels deep. Discovery skips linked worktrees and submodules (.git files), symbolic links,
      and directories inside repos. The backup name of a repo is its directory name; duplicate
      names across roots are rejected. Both layers back up branches and tags only; remote-tracking
      refs and stashes are left out. Repos without branches or tags are skipped with a warning.

      Mirror layer: fetches all branches and tags with forced refspecs into {{{{mirror-dir}}}}/{{{{name}}}}.git,
      creating the bare repo on first use with core.logAllRefUpdates=always. Rewritten history
      replaces mirror branches, and the mirror reflog keeps their previous tips. Branches deleted
      locally are never pruned from the mirror. No remote is added to the source repo. Git commands
      on the mirror trust it through safe.directory, because network shares often report files as
      owned by another account. A mirror left half-initialized by an earlier failure is repaired.

      Archive layer: when the branches or tags of a repo changed since the last run, or its archive
      is missing, creates a git bundle of HEAD, branches, and tags and stores it in {{{{archive-dir}}}}/{{{{name}}}}.7z,
      encrypted with AES-256 including file names. The password is passed to 7-Zip on standard
      input, never on the command line. The first run stores {{{{archive-dir}}}}/{PASSWORD_CHECK_NAME}
      to verify the password on later runs. Ref fingerprints are kept in {{{{archive-dir}}}}/{STATE_FILE_NAME}.

      Password sources, in order: --password-env, --password-keyring, interactive prompt.
      Setting both --password-env and --password-keyring is rejected.

  list
      Prints each discovered repo as '{{{{name}}}}  {{{{path}}}}'.

  restore
      Rebuilds a working repo in --target, which must be absent or empty. --source names a bare
      mirror directory or a .7z archive file. --name looks up {{{{mirror-dir}}}}/{{{{name}}}}.git and
      {{{{archive-dir}}}}/{{{{name}}}}.7z, preferring the mirror because it needs no password;
      --no-mirror and --no-archive drop a candidate. Every backed-up branch and tag becomes a local
      ref. A mirror restore checks out the branch the mirror HEAD names. An archive restore checks out
      the branch whose tip matches the bundle HEAD, preferring main and master. No remotes are set.
      Mirrors are trusted through safe.directory, as during backup. Archives are extracted with the
      password from the same sources as backup, asked once when prompting; the archive itself
      proves the password. A failed restore removes what it wrote to --target.

  set-password
      Prompts for the archive password twice and checks it against {{{{archive-dir}}}}/{PASSWORD_CHECK_NAME},
      creating the verifier when none exists. Only a verified password is stored in the OS keyring:
      Windows Credential Manager, macOS Keychain, or a Linux Secret Service store. The entry uses
      the --password-keyring service name and the user name '{KEYRING_USER}'. Requires the optional
      keyring package: pip install keyring.

  version
      Prints the tool name, semantic version with build metadata, and copyright notice.

  help [--verbose]
      Displays command-line usage information. When --verbose is specified, shows detailed
      action descriptions, the config file format, and examples. Running without arguments
      shows this help; options must follow an action.

Config File Format:
  A JSON object whose keys match the option names; command-line values override config values:
    {{
      "roots": ["{{{{root-1}}}}", "{{{{root-2}}}}"],
      "mirror-dir": "{{{{mirror-directory}}}}",
      "archive-dir": "{{{{archive-directory}}}}",
      "depth": {DEFAULT_DEPTH},
      "seven-zip": "{{{{7z-executable}}}}",
      "password-env": "{{{{variable-name}}}}",
      "password-keyring": "{{{{keyring-service}}}}"
    }}
  Set at most one of "password-env" and "password-keyring".

Restoring:
  From the configured mirror or archive directory:
    backup-git-repos restore --name {{{{name}}}} --target {{{{directory}}}}
  From a specific backup:
    backup-git-repos restore --source {{{{mirror-dir}}}}/{{{{name}}}}.git --target {{{{directory}}}}
    backup-git-repos restore --source {{{{archive-dir}}}}/{{{{name}}}}.7z --target {{{{directory}}}}
  Then add a remote: git remote add origin {{{{url}}}}

Scheduling Nightly Runs:
  Remove any "password-env" key from the config file, store the password once, then set "password-keyring":
    backup-git-repos set-password --archive-dir {{{{archive-directory}}}} --password-keyring {{{{keyring-service}}}}
  Run the scheduled job under the account that stored the password; keyrings are per user.
  Windows Task Scheduler:
    schtasks /Create /TN "backup-git-repos" /SC DAILY /ST 02:00 /TR "python {{{{script-path}}}} backup --log-file {{{{log-path}}}}"
  cron:
    0 2 * * * python3 {{{{script-path}}}} backup --log-file {{{{log-path}}}}

Examples:
  backup-git-repos list --root ~/projects
  backup-git-repos backup --root ~/projects --mirror-dir //server/backups/git --no-archive
  backup-git-repos backup --config ~/backup.json --verbose
"""


def default_config_path() -> Path:
    """Return the default config file location in the user's home directory."""
    return Path.home() / ".config" / TOOL_NAME / "config.json"


def load_config(path: Path | None) -> dict[str, Any]:
    """Load the JSON config file; an explicit path must exist, the default path is optional."""
    explicit = path is not None
    config_path = path if path is not None else default_config_path()
    if not config_path.exists():
        if explicit:
            raise UsageError(f"Config file not found: {config_path}")
        return {}
    try:
        data = json.loads(config_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise UsageError(f"Cannot read config file {config_path}: {exc}") from exc
    if not isinstance(data, dict):
        raise UsageError(f"Config file {config_path} must contain a JSON object.")
    unknown = sorted(set(data) - set(CONFIG_KEYS))
    if unknown:
        raise UsageError(f"Unknown config keys in {config_path}: {', '.join(unknown)}")
    return data


def to_path(value: str) -> Path:
    """Convert a user-supplied path string to a Path, expanding '~'."""
    return Path(os.path.expanduser(value))


def resolve_settings(args: argparse.Namespace, config: dict[str, Any]) -> Settings:
    """Merge command-line arguments over config values and validate the result."""
    roots = args.root if args.root else config.get("roots", [])
    if not isinstance(roots, list) or not all(isinstance(root, str) for root in roots):
        raise UsageError("Config key 'roots' must be a list of paths.")

    for key in ("mirror-dir", "archive-dir", "seven-zip", "password-env", "password-keyring"):
        if key in config and not isinstance(config[key], str):
            raise UsageError(f"Config key '{key}' must be a string.")

    mirror_dir = None if args.no_mirror else (args.mirror_dir or config.get("mirror-dir"))
    archive_dir = None if args.no_archive else (args.archive_dir or config.get("archive-dir"))

    depth = args.depth if args.depth is not None else config.get("depth", DEFAULT_DEPTH)
    if not isinstance(depth, int) or isinstance(depth, bool) or depth < 1:
        raise UsageError("Depth must be a positive integer.")

    password_env = args.password_env or config.get("password-env")
    password_keyring = args.password_keyring or config.get("password-keyring")
    if password_env and password_keyring:
        raise UsageError("Set only one of --password-env and --password-keyring.")

    return Settings(
        roots=[to_path(root) for root in roots],
        mirror_dir=to_path(mirror_dir) if mirror_dir else None,
        archive_dir=to_path(archive_dir) if archive_dir else None,
        depth=depth,
        seven_zip=args.seven_zip or config.get("seven-zip"),
        password_env=password_env,
        password_keyring=password_keyring,
        dry_run=args.dry_run,
    )


def is_link(path: Path) -> bool:
    """Return True for symbolic links and Windows junctions."""
    return path.is_symlink() or getattr(path, "is_junction", lambda: False)()


def discover_repos(roots: Sequence[Path], depth: int) -> list[Path]:
    """Return repos below the roots up to the given depth, in root order and sorted by name."""
    found: list[Path] = []

    def scan(directory: Path, remaining: int) -> None:
        try:
            entries = sorted(directory.iterdir(), key=lambda entry: entry.name.lower())
        except OSError:
            return
        for entry in entries:
            if not entry.is_dir() or is_link(entry):
                continue
            if (entry / ".git").is_dir():
                found.append(entry)
            elif remaining > 1:
                scan(entry, remaining - 1)

    for root in roots:
        scan(root, depth)
    return found


def find_duplicate_names(repos: Sequence[Path]) -> dict[str, list[Path]]:
    """Return backup names shared by more than one repo, mapped to their paths."""
    by_name: dict[str, list[Path]] = {}
    for repo in repos:
        by_name.setdefault(repo.name, []).append(repo)
    return {name: paths for name, paths in by_name.items() if len(paths) > 1}


def find_seven_zip(explicit: str | None) -> str | None:
    """Return the 7-Zip executable: the explicit value, a known name on PATH, or the Windows default."""
    if explicit:
        return explicit
    for name in SEVEN_ZIP_NAMES:
        located = shutil.which(name)
        if located:
            return located
    program_files = os.environ.get("ProgramFiles")
    if program_files:
        candidate = Path(program_files) / "7-Zip" / "7z.exe"
        if candidate.exists():
            return str(candidate)
    return None


def run_git(args: Sequence[str], logger: ToolLogger, check: bool = True) -> str:
    """Run git with the given arguments and return its standard output.

    Raises BackupError on failure when check is True; otherwise returns an empty string on failure.
    """
    command = ["git", *args]
    logger.debug_msg(f"Executing: {' '.join(command)}")
    result = subprocess.run(command, capture_output=True, text=True, encoding="utf-8", errors="replace")
    if result.returncode != 0 and not check:
        return ""
    if result.returncode != 0:
        detail = result.stderr.strip() or result.stdout.strip()
        index = 0
        while args[index] in ("-c", "-C"):
            index += 2
        raise BackupError(f"git {args[index]} failed: {detail}")
    return result.stdout


def run_seven_zip(seven_zip: str, args: Sequence[str], password: str, cwd: Path, logger: ToolLogger) -> int:
    """Run 7-Zip feeding the password on standard input and return its exit code."""
    command = [seven_zip, *args]
    logger.debug_msg(f"Executing: {' '.join(command)}")
    result = subprocess.run(
        command,
        cwd=cwd,
        input=f"{password}\n{password}\n",
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=SEVEN_ZIP_TIMEOUT_SECONDS,
    )
    if result.returncode != 0:
        logger.debug_msg(f"7-Zip output: {result.stdout.strip()} {result.stderr.strip()}")
    return result.returncode


def ref_fingerprint(repo: Path, logger: ToolLogger) -> str | None:
    """Return a SHA-256 fingerprint of the backed-up refs in the repo, or None when it has none."""
    output = run_git(["-C", str(repo), "for-each-ref", "--format=%(objectname) %(refname)", *BACKED_UP_REFS], logger)
    if not output.strip():
        return None
    return hashlib.sha256(output.encode("utf-8")).hexdigest()


def head_branch_ref(repo: Path, logger: ToolLogger) -> str | None:
    """Return the branch ref HEAD points to, or the first branch when HEAD is detached."""
    head = run_git(["-C", str(repo), "symbolic-ref", "-q", "HEAD"], logger, check=False).strip()
    if head:
        return head
    branches = run_git(["-C", str(repo), "for-each-ref", "--format=%(refname)", "refs/heads"], logger).split()
    return branches[0] if branches else None


def git_path(path: Path) -> str:
    """Return the absolute path with forward slashes, the form git uses in its ownership checks."""
    return Path(os.path.abspath(path)).as_posix()


def mirror_repo(repo: Path, mirror_dir: Path, dry_run: bool, logger: ToolLogger) -> None:
    """Force-push all branches and tags of the repo to its bare mirror, creating it on first use."""
    mirror = mirror_dir / f"{repo.name}.git"
    if dry_run:
        logger.info(f"[dry-run] Would push {repo.name} to {mirror}")
        return
    # Network shares often report files as owned by another account, which git rejects as dubious ownership.
    mirror_path = git_path(mirror)
    trust = ["-c", f"safe.directory={mirror_path}"]
    # The reflog setting marks a finished setup, so a mirror half-initialized by an earlier failure is set up again.
    log_setting = run_git([*trust, "-C", str(mirror), "config", "core.logAllRefUpdates"], logger, check=False)
    if log_setting.strip() != "always":
        try:
            mirror_dir.mkdir(parents=True, exist_ok=True)
        except OSError as exc:
            raise BackupError(f"Cannot create mirror directory {mirror_dir}: {exc}") from exc
        run_git([*trust, "init", "--bare", "-q", str(mirror)], logger)
        run_git([*trust, "-C", str(mirror), "config", "core.logAllRefUpdates", "always"], logger)
        head = head_branch_ref(repo, logger)
        if head:
            run_git([*trust, "-C", str(mirror), "symbolic-ref", "HEAD", head], logger)
    # Fetching runs git inside the mirror, where the trust option applies; a push would start git there without it.
    run_git(
        [*trust, "-C", mirror_path, "fetch", "-q", git_path(repo), "+refs/heads/*:refs/heads/*", "+refs/tags/*:refs/tags/*"],
        logger,
    )
    if logger.verbose:
        logger.info(f"Mirrored {repo.name} to {mirror}")


def load_state(archive_dir: Path) -> dict[str, str]:
    """Load the ref fingerprints recorded by the previous run."""
    state_file = archive_dir / STATE_FILE_NAME
    if not state_file.exists():
        return {}
    try:
        data = json.loads(state_file.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    return data if isinstance(data, dict) else {}


def save_state(archive_dir: Path, state: dict[str, str]) -> None:
    """Write the ref fingerprints, replacing the previous state file atomically."""
    partial = archive_dir / f"{STATE_FILE_NAME}.partial"
    try:
        partial.write_text(json.dumps(state, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        os.replace(partial, archive_dir / STATE_FILE_NAME)
    except OSError:
        partial.unlink(missing_ok=True)
        raise


def store_file(source: Path, target: Path) -> None:
    """Copy a file next to its target as .partial, then rename it into place."""
    partial = target.with_name(target.name + ".partial")
    try:
        shutil.copyfile(source, partial)
        os.replace(partial, target)
    except OSError:
        partial.unlink(missing_ok=True)
        raise


def keyring_backend() -> Any:
    """Import and return the optional keyring package; tests replace this function with a fake."""
    try:
        import keyring
    except ImportError as exc:
        raise UsageError("The keyring package is not installed; run: pip install keyring") from exc
    return keyring


def read_keyring_password(service: str, archive_dir: Path | None) -> str:
    """Return the archive password stored under the keyring service name; an empty entry counts as missing."""
    backend = keyring_backend()
    try:
        password = backend.get_password(service, KEYRING_USER)
    except Exception as exc:  # Keyring backends raise their own error types.
        raise UsageError(f"Cannot read keyring service {service}: {exc}") from exc
    if not password:
        directory = archive_dir if archive_dir is not None else "{{archive-dir}}"
        raise UsageError(
            f"No password stored in keyring service {service}; "
            f"run: {TOOL_NAME} set-password --archive-dir {directory} --password-keyring {service}"
        )
    return password


def prompt_password(confirm: bool) -> str:
    """Prompt for the archive password, optionally asking a second time to confirm it."""
    password = getpass.getpass("Archive password: ")
    if confirm and getpass.getpass("Confirm archive password: ") != password:
        raise BackupError("Passwords do not match.")
    if not password:
        raise BackupError("Archive password must not be empty.")
    return password


def obtain_password(settings: Settings, confirm: bool, keyring_password: str | None = None) -> str:
    """Return the archive password from the environment variable, the keyring, or an interactive prompt.

    A keyring password read earlier is reused, so the keyring is accessed once per run.
    """
    if settings.password_env:
        password = os.environ[settings.password_env]
    elif settings.password_keyring:
        password = keyring_password or read_keyring_password(settings.password_keyring, settings.archive_dir)
    else:
        return prompt_password(confirm)
    if not password:
        raise BackupError("Archive password must not be empty.")
    return password


def verify_password(settings: Settings, seven_zip: str, logger: ToolLogger, keyring_password: str | None) -> str:
    """Obtain the password and check it against the stored verifier, creating the verifier on first use."""
    archive_dir = settings.archive_dir
    assert archive_dir is not None
    first_use = not (archive_dir / PASSWORD_CHECK_NAME).exists()
    password = obtain_password(settings, confirm=first_use, keyring_password=keyring_password)
    check_password(archive_dir, seven_zip, password, logger)
    return password


def check_password(archive_dir: Path, seven_zip: str, password: str, logger: ToolLogger) -> None:
    """Check the password against the stored verifier, creating the verifier when none exists."""
    check = archive_dir / PASSWORD_CHECK_NAME
    first_use = not check.exists()
    with tempfile.TemporaryDirectory(prefix=f"{TOOL_NAME}-") as tmp:
        work = Path(tmp)
        if not first_use:
            if run_seven_zip(seven_zip, ["t", str(check)], password, work, logger) != 0:
                raise BackupError(f"Archive password does not match {check}.")
            return
        (work / "password-check.txt").write_text(PASSWORD_CHECK_TEXT, encoding="utf-8")
        args = ["a", "-t7z", "-mhe=on", "-p", "--", PASSWORD_CHECK_NAME, "password-check.txt"]
        if run_seven_zip(seven_zip, args, password, work, logger) != 0:
            raise BackupError("7-Zip failed to create the password verifier.")
        store_file(work / PASSWORD_CHECK_NAME, check)
        logger.info(f"Created password verifier {check}")


def run_set_password(settings: Settings, logger: ToolLogger) -> int:
    """Verify a prompted password against the archive verifier and store it in the keyring."""
    archive_dir = settings.archive_dir
    service = settings.password_keyring
    if archive_dir is None:
        raise UsageError("set-password needs an archive directory; pass --archive-dir or set 'archive-dir'.")
    if not service:
        raise UsageError("set-password needs a keyring service name; pass --password-keyring or set 'password-keyring'.")
    seven_zip = find_seven_zip(settings.seven_zip)
    if seven_zip is None:
        raise UsageError("7-Zip executable not found; pass --seven-zip.")
    backend = keyring_backend()
    if settings.dry_run:
        logger.info(f"[dry-run] Would verify the password against {archive_dir} and store it in keyring service {service}")
        return 0
    try:
        password = prompt_password(confirm=True)
        archive_dir.mkdir(parents=True, exist_ok=True)
        check_password(archive_dir, seven_zip, password, logger)
    except (BackupError, OSError, subprocess.TimeoutExpired) as exc:
        logger.error(f"Password not stored: {exc}")
        return 1
    try:
        backend.set_password(service, KEYRING_USER, password)
    except Exception as exc:  # Keyring backends raise their own error types.
        logger.error(f"Cannot store the password in keyring service {service}: {exc}")
        return 1
    logger.info(f"Stored the archive password in keyring service {service}")
    return 0


def archive_repo(repo: Path, archive_dir: Path, seven_zip: str, password: str, logger: ToolLogger) -> None:
    """Bundle all refs of the repo and store the bundle as an encrypted archive."""
    name = repo.name
    with tempfile.TemporaryDirectory(prefix=f"{TOOL_NAME}-") as tmp:
        work = Path(tmp)
        bundle = work / f"{name}.bundle"
        revisions = ["--branches", "--tags"]
        if run_git(["-C", str(repo), "rev-parse", "-q", "--verify", "HEAD"], logger, check=False):
            revisions.insert(0, "HEAD")
        run_git(["-C", str(repo), "bundle", "create", "-q", str(bundle), *revisions], logger)
        run_git(["-C", str(repo), "bundle", "verify", "-q", str(bundle)], logger)
        args = ["a", "-t7z", "-mhe=on", "-p", "--", f"{name}.7z", bundle.name]
        if run_seven_zip(seven_zip, args, password, work, logger) != 0:
            raise BackupError(f"7-Zip failed to archive {name}.")
        store_file(work / f"{name}.7z", archive_dir / f"{name}.7z")
    if logger.verbose:
        logger.info(f"Archived {name} to {archive_dir / f'{name}.7z'}")


def run_backup(settings: Settings, repos: Sequence[Path], logger: ToolLogger) -> int:
    """Back up the repos through the enabled layers and return the exit code."""
    seven_zip = None
    keyring_password = None
    if settings.archive_dir is not None:
        seven_zip = find_seven_zip(settings.seven_zip)
        if seven_zip is None:
            raise UsageError("7-Zip executable not found; pass --seven-zip or disable archives with --no-archive.")
        if settings.password_env and not settings.dry_run and settings.password_env not in os.environ:
            raise UsageError(f"Environment variable {settings.password_env} is not set.")
        if settings.password_keyring and not settings.dry_run:
            keyring_password = read_keyring_password(settings.password_keyring, settings.archive_dir)

    fingerprints: dict[Path, str] = {}
    failures = 0
    for repo in repos:
        try:
            fingerprint = ref_fingerprint(repo, logger)
        except BackupError as exc:
            logger.error(f"{repo}: {exc}")
            failures += 1
            continue
        if fingerprint is None:
            logger.warn(f"Skipping {repo.name}: repo has no commits ({repo}).")
            continue
        fingerprints[repo] = fingerprint

    mirrored = 0
    if settings.mirror_dir is not None:
        for repo in fingerprints:
            try:
                mirror_repo(repo, settings.mirror_dir, settings.dry_run, logger)
                mirrored += 1
            except BackupError as exc:
                logger.error(f"Mirror of {repo.name} failed: {exc}")
                failures += 1

    archived = unchanged = 0
    if settings.archive_dir is not None and seven_zip is not None:
        archive_dir = settings.archive_dir
        state = load_state(archive_dir)
        pending = []
        for repo, fingerprint in fingerprints.items():
            if state.get(repo.name) == fingerprint and (archive_dir / f"{repo.name}.7z").exists():
                unchanged += 1
                if logger.verbose:
                    logger.info(f"Archive of {repo.name} is up to date.")
            else:
                pending.append(repo)

        if settings.dry_run:
            for repo in pending:
                logger.info(f"[dry-run] Would archive {repo.name} to {archive_dir / f'{repo.name}.7z'}")
            archived = len(pending)
        elif pending:
            try:
                archive_dir.mkdir(parents=True, exist_ok=True)
                password = verify_password(settings, seven_zip, logger, keyring_password)
            except (BackupError, OSError) as exc:
                logger.error(f"Archive layer failed: {exc}")
                return 1
            for repo in pending:
                try:
                    archive_repo(repo, archive_dir, seven_zip, password, logger)
                    state[repo.name] = fingerprints[repo]
                    save_state(archive_dir, state)
                    archived += 1
                except (BackupError, OSError, subprocess.TimeoutExpired) as exc:
                    logger.error(f"Archive of {repo.name} failed: {exc}")
                    failures += 1

    summary = [f"{len(fingerprints)} repos"]
    if settings.mirror_dir is not None:
        summary.append(f"{mirrored} mirrored")
    if settings.archive_dir is not None:
        summary.append(f"{archived} archived, {unchanged} unchanged")
    if failures:
        summary.append(f"{failures} failed")
    prefix = "[dry-run] " if settings.dry_run else ""
    logger.info(f"{prefix}Backup finished: {', '.join(summary)}.")
    return 1 if failures else 0


def is_bare_repo(path: Path, logger: ToolLogger) -> bool:
    """Return True when the directory itself is a bare repo, trusting it like a mirror."""
    trust = ["-c", f"safe.directory={git_path(path)}"]
    output = run_git([*trust, "-C", str(path), "rev-parse", "--is-bare-repository", "--absolute-git-dir"], logger, check=False)
    lines = output.splitlines()
    return len(lines) == 2 and lines[0] == "true" and Path(lines[1]).resolve() == path.resolve()


def detect_source(path: Path, logger: ToolLogger) -> RestoreSource:
    """Classify a restore source as an archive file or a bare mirror directory."""
    if path.is_file() and path.suffix.lower() == ".7z":
        return RestoreSource("archive", path)
    if path.is_dir() and is_bare_repo(path, logger):
        return RestoreSource("mirror", path)
    raise UsageError(f"Unsupported restore source {path}; expected a .7z archive file or a bare mirror repo directory.")


def find_named_source(name: str, settings: Settings, logger: ToolLogger) -> RestoreSource:
    """Look up a backup name in the mirror and archive directories, preferring the mirror."""
    # A colon would let a Windows drive prefix such as D:name escape the backup directories.
    if not name or any(part in name for part in ("/", "\\", "..", ":")):
        raise UsageError(f"Invalid backup name '{name}'; pass a repo name without path separators, ':' or '..'.")
    candidates = []
    if settings.mirror_dir is not None:
        candidates.append(settings.mirror_dir / f"{name}.git")
    if settings.archive_dir is not None:
        candidates.append(settings.archive_dir / f"{name}.7z")
    if not candidates:
        raise UsageError("restore --name needs a mirror or archive directory; pass --mirror-dir or --archive-dir.")
    for candidate in candidates:
        if candidate.exists():
            return detect_source(candidate, logger)
    raise UsageError(f"No backup named {name}; checked {', '.join(str(c) for c in candidates)}.")


def check_restore_target(target: Path) -> None:
    """Reject a target that exists as a file or as a non-empty directory."""
    if target.is_dir():
        if any(target.iterdir()):
            raise UsageError(f"Restore target {target} is not empty.")
    elif target.exists():
        raise UsageError(f"Restore target {target} is not a directory.")


def remove_tree(path: Path) -> None:
    """Delete a directory tree, clearing the read-only flag git sets on object files."""

    def make_writable(function: Any, failed: str, _error: Any) -> None:
        os.chmod(failed, 0o700)
        function(failed)

    if sys.version_info >= (3, 12):
        shutil.rmtree(path, onexc=make_writable)
    else:
        shutil.rmtree(path, onerror=make_writable)


def clear_target(target: Path, created: bool) -> None:
    """Undo a failed restore: delete a target this run created, or empty a target that was empty."""
    if not target.exists():
        return
    if created:
        remove_tree(target)
        return
    for child in target.iterdir():
        if child.is_dir() and not child.is_symlink():
            remove_tree(child)
        else:
            child.unlink()


def pick_head(refs: dict[str, str], head_commit: str | None) -> str | None:
    """Return the branch whose tip matches the HEAD commit, preferring main and master, else the first branch."""
    branches = sorted(ref for ref in refs if ref.startswith("refs/heads/"))
    matching = [ref for ref in branches if refs[ref] == head_commit]
    for ref in PREFERRED_BRANCHES:
        if ref in matching:
            return ref
    if matching:
        return matching[0]
    return branches[0] if branches else None


def list_refs(repo: Path, logger: ToolLogger) -> dict[str, str]:
    """Return the branches and tags of a repo mapped to their object names."""
    output = run_git(["-C", str(repo), "for-each-ref", "--format=%(refname) %(objectname)", *BACKED_UP_REFS], logger)
    return dict(line.split(" ", 1) for line in output.splitlines() if line)


def fetch_backup(target: Path, source_url: str, extra: Sequence[str], logger: ToolLogger) -> None:
    """Fetch every branch and tag from a mirror or bundle into the target as local refs."""
    refspecs = ["+refs/heads/*:refs/heads/*", "+refs/tags/*:refs/tags/*"]
    run_git(["-C", str(target), "fetch", "-q", "--update-head-ok", *extra, source_url, *refspecs], logger)


def shell_quote(value: str) -> str:
    """Quote a value for the POSIX shell git uses to start an upload-pack command."""
    return "'" + value.replace("'", "'\\''") + "'"


def restore_from_mirror(mirror: Path, target: Path, logger: ToolLogger) -> str | None:
    """Fetch the mirror into the target and return the branch the mirror's HEAD names."""
    mirror_path = git_path(mirror)
    trust = ["-c", f"safe.directory={mirror_path}"]
    # Git drops command-line config when it starts upload-pack for a local fetch, so the trust goes into that command.
    upload_pack = f"git -c {shell_quote(f'safe.directory={mirror_path}')} upload-pack"
    fetch_backup(target, mirror_path, [f"--upload-pack={upload_pack}"], logger)
    head = run_git([*trust, "-C", mirror_path, "symbolic-ref", "-q", "HEAD"], logger, check=False).strip()
    refs = list_refs(target, logger)
    return head if head in refs else pick_head(refs, None)


def restore_from_archive(archive: Path, target: Path, seven_zip: str, password: str, logger: ToolLogger) -> str | None:
    """Extract the bundle from the archive, fetch it into the target, and return the branch to check out."""
    # Archives on cloud drives may download on first access, so say what the wait is for.
    logger.info(f"Extracting {archive}")
    work = Path(tempfile.mkdtemp(prefix=f"{TOOL_NAME}-"))
    try:
        args = ["x", "-y", f"-o{work}", "--", str(archive.resolve())]
        if run_seven_zip(seven_zip, args, password, work, logger) != 0:
            raise BackupError(f"7-Zip could not extract {archive}; the archive password was rejected or the archive is damaged.")
        bundles = sorted(work.glob("*.bundle"))
        if len(bundles) != 1:
            raise BackupError(f"Expected one git bundle in {archive}, found {len(bundles)}.")
        bundle = bundles[0]
        run_git(["-C", str(target), "bundle", "verify", "-q", str(bundle)], logger)
        heads = run_git(["-C", str(target), "bundle", "list-heads", str(bundle), "HEAD"], logger).split()
        fetch_backup(target, str(bundle), [], logger)
    finally:
        # A failed removal must not hide the original error, but the leftover holds decrypted data.
        try:
            remove_tree(work)
        except OSError as exc:
            logger.warn(f"Cannot remove {work}, which holds the decrypted bundle; delete it manually: {exc}")
    refs = list_refs(target, logger)
    return pick_head(refs, heads[0] if heads else None)


def run_restore(settings: Settings, args: argparse.Namespace, logger: ToolLogger) -> int:
    """Restore one repo from a mirror or archive into the target directory and return the exit code."""
    if not args.target:
        raise UsageError("restore needs --target DIR.")
    if bool(args.source) == bool(args.name):
        raise UsageError("restore needs exactly one of --source PATH and --name NAME.")
    if args.source:
        source = detect_source(to_path(args.source), logger)
    else:
        source = find_named_source(args.name, settings, logger)
    target = to_path(args.target)
    check_restore_target(target)

    seven_zip = None
    if source.kind == "archive":
        seven_zip = find_seven_zip(settings.seven_zip)
        if seven_zip is None:
            raise UsageError("7-Zip executable not found; pass --seven-zip.")
    if settings.dry_run:
        logger.info(f"[dry-run] Would restore {source.kind} {source.path} to {target}")
        return 0

    password = None
    if seven_zip is not None:
        if settings.password_env and settings.password_env not in os.environ:
            raise UsageError(f"Environment variable {settings.password_env} is not set.")
        try:
            password = obtain_password(settings, confirm=False)
        except BackupError as exc:
            logger.error(f"Restore failed: {exc}")
            return 1

    created = not target.exists()
    try:
        target.mkdir(parents=True, exist_ok=True)
        run_git(["init", "-q", str(target)], logger)
        if seven_zip is not None and password is not None:
            head = restore_from_archive(source.path, target, seven_zip, password, logger)
        else:
            head = restore_from_mirror(source.path, target, logger)
        if head is None:
            logger.warn(f"Restored {target} has no branches; nothing was checked out.")
        else:
            run_git(["-C", str(target), "symbolic-ref", "HEAD", head], logger)
            run_git(["-C", str(target), "checkout", "-q", "-f"], logger)
    except (BackupError, OSError, subprocess.TimeoutExpired, KeyboardInterrupt) as exc:
        if isinstance(exc, KeyboardInterrupt):
            logger.error(f"Restore of {source.path} interrupted; cleaning up {target}.")
        else:
            logger.error(f"Restore of {source.path} failed: {exc}")
        try:
            clear_target(target, created)
        except OSError as cleanup_exc:
            logger.error(f"Cannot clean up {target}: {cleanup_exc}")
        except KeyboardInterrupt:
            logger.error(f"Interrupted again; cleanup abandoned, so {target} may hold a partial restore.")
            return 130
        return 130 if isinstance(exc, KeyboardInterrupt) else 1
    logger.info(f"Restored {source.kind} {source.path} to {target}; add a remote with: git remote add origin {{{{url}}}}")
    return 0


def run_action(action: str, args: argparse.Namespace, logger: ToolLogger) -> int:
    """Resolve the settings and run one action; raises UsageError for invalid arguments or configuration."""
    settings = resolve_settings(args, load_config(to_path(args.config) if args.config else None))
    if action == "set-password":
        return run_set_password(settings, logger)
    if action == "restore":
        return run_restore(settings, args, logger)
    if not settings.roots:
        raise UsageError("No roots given; pass --root or set 'roots' in the config file.")
    repos = discover_repos(settings.roots, settings.depth)
    duplicates = find_duplicate_names(repos)
    if duplicates:
        details = "; ".join(f"{name}: {', '.join(str(p) for p in paths)}" for name, paths in duplicates.items())
        raise UsageError(f"Duplicate backup names: {details}")

    if action == "list":
        for repo in repos:
            logger.emit(f"{repo.name}  {repo}")
        return 0

    if settings.mirror_dir is None and settings.archive_dir is None:
        raise UsageError("No backup layer enabled; set a mirror directory or an archive directory.")
    return run_backup(settings, repos, logger)


def action_handler(action: str) -> Callable[[argparse.Namespace, ToolLogger], int]:
    """Return a harness handler running the action, mapping UsageError to exit code 2 and Ctrl+C to 130.

    Returning instead of raising lets the harness log the completion summary for interrupted actions too.
    """

    def handle(args: argparse.Namespace, logger: ToolLogger) -> int:
        try:
            return run_action(action, args, logger)
        except UsageError as exc:
            logger.error(str(exc))
            return 2
        except KeyboardInterrupt:
            logger.error(f"{action} interrupted with Ctrl+C.")
            return 130

    return handle


def describe_config(value: str | None) -> str:
    """Return the config file for the startup banner, marking the default location and its absence."""
    if value:
        return str(to_path(value))
    path = default_config_path()
    return f"{path} (default)" if path.exists() else f"{path} (default, absent)"


class BackupHarness(ToolHarness):
    """Tool harness keeping the detailed help screen and formatting every argument error with severity indicators."""

    config_file: str = ""
    dry_run: bool = False

    def format_help(self, verbose: bool = False) -> str:
        """Return the help screen, which documents option values, config files, and scheduling."""
        return get_long_usage(verbose=verbose)

    def create_logger(self, args: argparse.Namespace) -> ToolLogger:
        """Record the config file and dry-run mode for the startup banner, then build the logger."""
        self.config_file = describe_config(args.config)
        self.dry_run = args.dry_run
        return super().create_logger(args)

    def log_startup(self, logger: ToolLogger, action: str, extra: dict[str, Any] | None = None) -> None:
        """Emit the standard startup banner including the config file and dry-run mode."""
        config = {"Config file": self.config_file, "Dry run": str(self.dry_run).lower(), **(extra or {})}
        super().log_startup(logger, action, extra=config)

    def _build_parser(self, action_name: str | None = None) -> argparse.ArgumentParser:
        """Build the action parser, reporting argument errors with severity indicators."""
        parser = super()._build_parser(action_name)

        def report_error(message: str) -> None:
            ToolLogger().error(f"{message}\nUsage: {self.name} {action_name or '<action>'} [options]")
            sys.exit(2)

        parser.error = report_error  # type: ignore[method-assign]
        return parser

    def run(self, argv: Sequence[str] | None = None, extra_startup: dict[str, Any] | None = None) -> int:
        """Reject unknown actions and options given before an action, then delegate to the harness."""
        raw_args = list(sys.argv[1:] if argv is None else argv)
        known = {*self._actions, "help", "version", "-h", "--help", "--version"}
        if raw_args and raw_args[0] not in known:
            first = raw_args[0]
            if first.startswith("-"):
                message = f"Missing action before option '{first}'; options follow an action such as backup."
            else:
                message = f"Unknown subcommand: '{first}'"
            usage = f"Usage: {self.name} {{help|version|{'|'.join(self._actions)}}} [options]"
            ToolLogger().error(f"{message}\n{usage}")
            return 2
        return super().run(raw_args, extra_startup=extra_startup)


def build_harness() -> BackupHarness:
    """Construct the CLI harness with the backup, list, restore, and set-password actions."""
    harness = BackupHarness(name=TOOL_NAME, description=DESCRIPTION, version=TOOL_VERSION, exit_codes=EXIT_CODES)
    harness.add_global_argument("--config", type=str, default=None, help="JSON config file.")
    harness.add_global_argument("--root", action="append", default=None, help="Directory to scan for repos.")
    harness.add_global_argument("--depth", type=int, default=None, help="Maximum scan depth below each root.")
    harness.add_global_argument("--mirror-dir", type=str, default=None, help="Bare mirror directory.")
    harness.add_global_argument("--no-mirror", action="store_true", help="Disable the mirror layer.")
    harness.add_global_argument("--archive-dir", type=str, default=None, help="Encrypted archive directory.")
    harness.add_global_argument("--no-archive", action="store_true", help="Disable the archive layer.")
    harness.add_global_argument("--source", type=str, default=None, help="Mirror directory or archive file to restore.")
    harness.add_global_argument("--name", type=str, default=None, help="Backup name to restore.")
    harness.add_global_argument("--target", type=str, default=None, help="Directory to restore into.")
    harness.add_global_argument("--seven-zip", type=str, default=None, help="7-Zip executable.")
    harness.add_global_argument("--password-env", type=str, default=None, help="Environment variable holding the password.")
    harness.add_global_argument("--password-keyring", type=str, default=None, help="Keyring service holding the password.")
    harness.add_global_argument("--dry-run", action="store_true", help="Report planned actions without writing.")
    harness.add_action("backup", "back up all discovered repos", handler=action_handler("backup"))
    harness.add_action("list", "list discovered repos and their backup names", handler=action_handler("list"))
    harness.add_action("restore", "rebuild a working repo from one mirror or archive", handler=action_handler("restore"))
    harness.add_action("set-password", "verify the archive password and store it", handler=action_handler("set-password"))
    return harness


def main(argv: Sequence[str] | None = None) -> int:
    """Run the command line and return its exit code."""
    return build_harness().run(argv)


if __name__ == "__main__":
    sys.exit(main())
