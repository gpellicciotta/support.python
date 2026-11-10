#!/usr/bin/env python3
"""Command-line interface for the lint-markdown standalone tool."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys
from typing import Any, List, NoReturn, Optional

from support_python.cli import ToolHarness
from support_python.logging import CliLogger
from support_python.markdown.lint import DEFAULT_EXCLUDES, LintIssue, MarkdownLinter
from support_python.markdown.lint import discover_markdown_files, find_project_root, parse_rule_codes
from support_python.markdown.profiles import DEFAULT_CONFIG_FILENAME, LEGACY_CONFIG_FILENAME, load_profile

TOOL_NAME = "lint-markdown"
DESCRIPTION = """Automated markdown linter enforcing repository markdown styling guidelines.
Directory walks skip Git-ignored files; files named explicitly are always linted."""
SHORT_USAGE = f"{TOOL_NAME} {{check|fix|help|version}} [{{{{path}}}}...] [options]"


class _JsonAwareLogger(CliLogger):
    """CLI logger that suppresses non-emit stdout log lines in JSON output mode while preserving stderr."""

    def __init__(self, *args: Any, json_mode: bool = False, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self.json_mode = json_mode

    def log(self, message: str = "", level: Optional[str] = None, origin: Optional[str] = None, **kwargs: Any) -> None:
        is_err = (level or "").strip().upper() in ("WARN", "WARNING", "ERROR")
        kwargs.setdefault("to_stderr", is_err)
        if self.json_mode and level is not None:
            kwargs["to_stdout"] = False
        else:
            kwargs.setdefault("to_stdout", not is_err)
        super().log(message, level=level, origin=origin, **kwargs)


class LintMarkdownHarness(ToolHarness):
    """Tool harness supporting JSON output mode on check."""

    def create_logger(self, args: argparse.Namespace) -> CliLogger:
        """Build a logger that suppresses non-JSON console output when --format json is active."""
        base = super().create_logger(args)
        json_mode = getattr(args, "format", "text") == "json"
        if not json_mode:
            return base
        return _JsonAwareLogger(
            log_file=base.log_file,
            log_level=base.effective_level if base._explicit_level_set else None,
            debug=base.debug_flag,
            verbose=base.verbose,
            json_mode=True,
        )


def report_argument_error(message: str) -> NoReturn:
    """Log an argument error with the standard severity indicator, then exit with code 2."""
    early_logger = ToolHarness(name=TOOL_NAME, description=DESCRIPTION)._extract_early_logger(sys.argv[1:])
    early_logger.error(f"{message}\nUsage: {SHORT_USAGE}; run '{TOOL_NAME} help' for details.")
    early_logger.close()
    sys.exit(2)


def configure_lint_parser(parser: argparse.ArgumentParser) -> None:
    """Add the path arguments and standard error reporting to the 'check' and 'fix' parsers."""
    parser.add_argument("paths", nargs="*", type=Path)
    parser.parse_args = parser.parse_intermixed_args  # type: ignore[method-assign]
    parser.error = report_argument_error  # type: ignore[method-assign]


def configure_check_parser(parser: argparse.ArgumentParser) -> None:
    """Add the path arguments and '--format' option to the 'check' parser."""
    configure_lint_parser(parser)
    parser.add_argument("--format", choices=["text", "json"], default="text", help="output format (text or json; default: text)")


def configure_fix_parser(parser: argparse.ArgumentParser) -> None:
    """Add the path arguments and '--dry-run' option to the 'fix' parser."""
    configure_lint_parser(parser)
    parser.add_argument("--dry-run", action="store_true", help="report files and issues that would be fixed without writing")


def plural(count: int, noun: str) -> str:
    """Return the count followed by the noun, pluralized when the count is not one."""
    return f"{count} {noun}{'s' if count != 1 else ''}"


def _discover_config_path(input_paths: List[Path], repo_root: Path, logger: Optional[CliLogger] = None) -> Optional[Path]:
    """Locate a '.lint-markdown.json' (or legacy '.markdown-lint.json') file in the target path or project root."""
    dirs: List[Path] = []
    for base in (*input_paths, find_project_root(input_paths[0]), repo_root):
        cand_dir = base.resolve().parent if base.resolve().is_file() else base.resolve()
        if cand_dir not in dirs:
            dirs.append(cand_dir)
    for cand_dir in dirs:
        candidate = cand_dir / DEFAULT_CONFIG_FILENAME
        if candidate.is_file():
            return candidate
        legacy = cand_dir / LEGACY_CONFIG_FILENAME
        if legacy.is_file():
            if logger is not None:
                logger.warn(
                    f"Reading legacy config {legacy}; rename it to {DEFAULT_CONFIG_FILENAME}. "
                    "The legacy filename is removed in v3.0.0."
                )
            return legacy
    return None


def _emit_json_check(logger: CliLogger, files_checked: int, issues: List[LintIssue], repo_root: Path) -> None:
    """Emit the JSON check payload on stdout."""
    payload = {
        "files_checked": files_checked,
        "issues": [issue.to_dict(relative_to=repo_root) for issue in issues],
    }
    logger.emit(json.dumps(payload))


def run_lint(args: argparse.Namespace, logger: CliLogger, fix: bool) -> int:
    """Lint the markdown files under the requested paths, fixing safe issues first when asked."""
    repo_root = Path.cwd()
    dry_run = fix and bool(getattr(args, "dry_run", False))
    is_json = not fix and getattr(args, "format", "text") == "json"

    for p in args.paths:
        if not p.resolve().exists():
            logger.error(f"Path does not exist: {p}")
            return 2
    input_paths = list(args.paths) or [repo_root]

    cfg_arg = getattr(args, "config", None)
    prof_arg = getattr(args, "profile", None)
    if cfg_arg is not None and not Path(cfg_arg).resolve().exists():
        logger.error(f"Configuration file does not exist: {cfg_arg}")
        return 2
    resolved_cfg = Path(cfg_arg).resolve() if cfg_arg is not None else _discover_config_path(input_paths, repo_root, logger=logger)
    try:
        profile = load_profile(resolved_cfg, profile=prof_arg)
        linter = MarkdownLinter(
            enabled_rules=parse_rule_codes(args.rules), offline=args.offline, timeout=args.timeout, profile=profile
        )
    except ValueError as exc:
        logger.error(str(exc))
        return 2

    excludes = DEFAULT_EXCLUDES + (list(profile.excludes) if profile else []) + (args.exclude or [])
    files = discover_markdown_files(input_paths, repo_root, excludes)
    logger.debug_msg(
        f"Linting {plural(len(files), 'markdown file')} "
        f"(rules: {','.join(sorted(linter.enabled_rules))}; offline: {str(args.offline).lower()}; timeout: {args.timeout}s)"
    )
    if not files:
        if is_json:
            _emit_json_check(logger, 0, [], repo_root)
        else:
            logger.info("No markdown files found to lint.")
        return 0

    total_issues: List[LintIssue] = []
    planned_fixes: List[LintIssue] = []
    files_fixed = 0
    for file_path in files:
        try:
            raw_bytes = file_path.read_bytes()
        except OSError as e:
            logger.error(f"Failed to read {file_path}: {e}")
            return 1
        if dry_run:
            fixed_bytes = linter.fix_content(file_path, raw_bytes)
            if fixed_bytes != raw_bytes:
                files_fixed += 1
                before_issues = linter.lint_content(file_path, raw_bytes)
                after_keys = {
                    (i.line_number, i.column_number, i.rule_id, i.message) for i in linter.lint_content(file_path, fixed_bytes)
                }
                file_fixes = [
                    i
                    for i in before_issues
                    if i.fixable or (i.line_number, i.column_number, i.rule_id, i.message) not in after_keys
                ]
                planned_fixes.extend(file_fixes)
            continue
        if fix:
            fixed_bytes = linter.fix_content(file_path, raw_bytes)
            if fixed_bytes != raw_bytes:
                file_path.write_bytes(fixed_bytes)
                files_fixed += 1
                raw_bytes = fixed_bytes
        issues = linter.lint_content(file_path, raw_bytes)
        total_issues.extend(issues)
        if args.verbose and not issues:
            rel = file_path.relative_to(repo_root) if file_path.is_relative_to(repo_root) else file_path
            logger.info(f"OK: {rel}")

    if dry_run:
        for issue in planned_fixes:
            logger.emit(issue.format(relative_to=repo_root))
        if files_fixed > 0:
            logger.info(
                f"Dry run: would auto-fix {plural(len(planned_fixes), 'formatting issue')} across {plural(files_fixed, 'file')}."
            )
        else:
            logger.info(f"Dry run: no fixable formatting issues found across {plural(len(files), 'file')}.")
        return 0

    if is_json:
        _emit_json_check(logger, len(files), total_issues, repo_root)
        if total_issues:
            logger.warn(f"Found {plural(len(total_issues), 'lint issue')} across {len(files)} files.")
            return 1
        return 0

    for issue in total_issues:
        logger.emit(issue.format(relative_to=repo_root))
    if fix and files_fixed > 0:
        logger.info(f"Auto-fixed formatting issues in {plural(files_fixed, 'file')}.")
    if total_issues:
        logger.warn(f"Found {plural(len(total_issues), 'lint issue')} across {len(files)} files.")
        return 1
    logger.info(f"All {len(files)} markdown files passed linting.")
    return 0


def get_rules_help() -> str:
    """Return the verbose help section listing every lint rule."""
    width = max(len(name) for name, _ in MarkdownLinter.RULES.values())
    rules = [f"  {rid}  {name:<{width}}  {desc}" for rid, (name, desc) in MarkdownLinter.RULES.items()]
    return "\n".join(
        [
            "Rules:",
            *rules,
            "",
            "Path selection:",
            "  Without paths, lints every markdown file under the current directory.",
            "  Directory walks skip Git-ignored files; files named explicitly are always linted.",
            f"  Default excludes: {', '.join(DEFAULT_EXCLUDES)}",
        ]
    )


def build_harness() -> ToolHarness:
    """Build the command-line harness exposing the 'check' and 'fix' actions."""
    harness = LintMarkdownHarness(
        name=TOOL_NAME,
        description=DESCRIPTION,
        exit_codes={
            1: "lint violations found, or an operational error occurred",
            2: "invalid arguments, syntax errors, or nonexistent paths",
        },
        examples=[
            f"{TOOL_NAME} check",
            f"{TOOL_NAME} check --offline --format json README.md docs",
            f"{TOOL_NAME} check --profile dev-guidelines docs",
            f"{TOOL_NAME} check --rules MD001,MD017 guidelines",
            f"{TOOL_NAME} check --exclude 'archive/*' --log-file lint.log",
            f"{TOOL_NAME} fix docs",
            f"{TOOL_NAME} fix --dry-run docs",
        ],
        detailed_help=get_rules_help(),
    )
    harness.add_global_argument(
        "--exclude", action="append", metavar="GLOB", help="exclude paths matching the glob pattern (repeatable)"
    )
    harness.add_global_argument("--rules", metavar="RULES", help="comma-separated rule codes to check (default: all)")
    harness.add_global_argument("--profile", metavar="PROFILE", help="named lint profile (default or dev-guidelines)")
    harness.add_global_argument("--config", type=Path, metavar="PATH", help=f"path to {DEFAULT_CONFIG_FILENAME} config file")
    harness.add_global_argument("--offline", action="store_true", help="skip external link checks (rule MD018)")
    harness.add_global_argument(
        "--timeout", type=float, default=10.0, metavar="SECONDS", help="external link timeout in seconds (default: 10.0)"
    )
    check_detail = (
        "Lints the markdown files under each path, or under the current directory when no\n"
        "path is given, and prints one line per violation (or a JSON document with --format json).\n"
        "Exits 1 if any violation is found."
    )
    fix_detail = (
        "Rewrites files in-place to normalize line endings, bullet markers, tabs, trailing\n"
        "whitespace, blank lines after subheadings and before lists, and table alignment,\n"
        "then lints the result like 'check'.\n"
        "With --dry-run, lists every file and issue it would fix, writes nothing, and exits 0.\n"
        "Exits 1 if violations remain that cannot be fixed automatically."
    )
    harness.add_action(
        "check",
        "lint markdown files and report violations",
        handler=lambda args, logger: run_lint(args, logger, fix=False),
        detail=check_detail,
        usage_suffix="[{{path}}...] [options]",
        configure_parser=configure_check_parser,
    )
    harness.add_action(
        "fix",
        "fix safe formatting issues in-place, then lint",
        handler=lambda args, logger: run_lint(args, logger, fix=True),
        detail=fix_detail,
        usage_suffix="[{{path}}...] [options]",
        configure_parser=configure_fix_parser,
    )
    return harness


def main(argv: Optional[List[str]] = None) -> int:
    """Parse command-line arguments and execute the requested action."""
    return build_harness().run(argv, extra_startup={"Working directory": str(Path.cwd())})


if __name__ == "__main__":
    sys.exit(main())
