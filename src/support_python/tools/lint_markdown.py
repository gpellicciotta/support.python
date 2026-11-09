#!/usr/bin/env python3
"""Command-line interface for the lint-markdown standalone tool."""

from __future__ import annotations

import argparse
from pathlib import Path
import sys
from typing import List, NoReturn, Optional

from support_python.cli import ToolHarness
from support_python.logging import ToolLogger
from support_python.markdown.lint import DEFAULT_EXCLUDES, LintIssue, MarkdownLinter
from support_python.markdown.lint import discover_markdown_files, find_project_root, parse_rule_codes
from support_python.markdown.profiles import DEFAULT_CONFIG_FILENAME, load_profile

TOOL_NAME = "lint-markdown"
DESCRIPTION = """Automated markdown linter enforcing repository markdown styling guidelines.
Directory walks skip Git-ignored files; files named explicitly are always linted."""
SHORT_USAGE = f"{TOOL_NAME} {{check|fix|help|version}} [{{{{path}}}}...] [options]"


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


def plural(count: int, noun: str) -> str:
    """Return the count followed by the noun, pluralized when the count is not one."""
    return f"{count} {noun}{'s' if count != 1 else ''}"


def _discover_config_path(input_paths: List[Path], repo_root: Path) -> Optional[Path]:
    """Locate a '.markdown-lint.json' file in the target path or project root if present."""
    for base in (*input_paths, find_project_root(input_paths[0]), repo_root):
        cand_dir = base.resolve().parent if base.resolve().is_file() else base.resolve()
        candidate = cand_dir / DEFAULT_CONFIG_FILENAME
        if candidate.is_file():
            return candidate
    return None


def run_lint(args: argparse.Namespace, logger: ToolLogger, fix: bool) -> int:
    """Lint the markdown files under the requested paths, fixing safe issues first when asked."""
    repo_root = Path.cwd()
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
    resolved_cfg = Path(cfg_arg).resolve() if cfg_arg is not None else _discover_config_path(input_paths, repo_root)
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
        logger.info("No markdown files found to lint.")
        return 0

    total_issues: List[LintIssue] = []
    files_fixed = 0
    for file_path in files:
        try:
            raw_bytes = file_path.read_bytes()
        except OSError as e:
            logger.error(f"Failed to read {file_path}: {e}")
            return 1
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
    harness = ToolHarness(
        name=TOOL_NAME,
        description=DESCRIPTION,
        exit_codes={
            1: "lint violations found, or an operational error occurred",
            2: "invalid arguments, syntax errors, or nonexistent paths",
        },
        examples=[
            f"{TOOL_NAME} check",
            f"{TOOL_NAME} check --offline README.md docs",
            f"{TOOL_NAME} check --profile dev-guidelines docs",
            f"{TOOL_NAME} check --rules MD001,MD017 guidelines",
            f"{TOOL_NAME} check --exclude 'archive/*' --log-file lint.log",
            f"{TOOL_NAME} fix docs",
        ],
        detailed_help=get_rules_help(),
    )
    harness.add_global_argument("--fix", action="store_true", help="apply safe fixes in-place, like the 'fix' action")
    harness.add_global_argument(
        "--exclude", action="append", metavar="GLOB", help="exclude paths matching the glob pattern (repeatable)"
    )
    harness.add_global_argument("--rules", metavar="RULES", help="comma-separated rule codes to check (default: all)")
    harness.add_global_argument("--profile", metavar="PROFILE", help="named lint profile (default or dev-guidelines)")
    harness.add_global_argument("--config", type=Path, metavar="PATH", help="path to .markdown-lint.json config file")
    harness.add_global_argument("--offline", action="store_true", help="skip external link checks (rule MD018)")
    harness.add_global_argument(
        "--timeout", type=float, default=10.0, metavar="SECONDS", help="external link timeout in seconds (default: 10.0)"
    )
    check_detail = (
        "Lints the markdown files under each path, or under the current directory when no\n"
        "path is given, and prints one line per violation. Exits 1 if any violation is found.\n"
        "With --fix, applies safe fixes first, exactly like the 'fix' action."
    )
    fix_detail = (
        "Rewrites files in-place to normalize line endings, bullet markers, tabs, trailing\n"
        "whitespace, blank lines after subheadings and before lists, and table alignment,\n"
        "then lints the result like 'check'.\n"
        "Exits 1 if violations remain that cannot be fixed automatically."
    )
    harness.add_action(
        "check",
        "lint markdown files and report violations",
        handler=lambda args, logger: run_lint(args, logger, fix=args.fix),
        detail=check_detail,
        usage_suffix="[{{path}}...] [options]",
        configure_parser=configure_lint_parser,
    )
    harness.add_action(
        "fix",
        "fix safe formatting issues in-place, then lint",
        handler=lambda args, logger: run_lint(args, logger, fix=True),
        detail=fix_detail,
        usage_suffix="[{{path}}...] [options]",
        configure_parser=configure_lint_parser,
    )
    return harness


def main(argv: Optional[List[str]] = None) -> int:
    """Parse command-line arguments and execute the requested action."""
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    if hasattr(sys.stderr, "reconfigure"):
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    return build_harness().run(argv, extra_startup={"Working directory": str(Path.cwd())})


if __name__ == "__main__":
    sys.exit(main())
