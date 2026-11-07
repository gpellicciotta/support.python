#!/usr/bin/env python3
"""
Automated markdown linter enforcing dev-guidelines markdown styling standards.
Validates file format, encoding, heading hierarchy, list formatting, URLs, code block languages,
and anti-patterns across repository markdown files.
"""

from __future__ import annotations

import argparse
import fnmatch
import os
import re
import subprocess
import sys
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass
from pathlib import Path
from typing import List, NoReturn, Optional, Set, Tuple

from support_python.cli import ToolHarness  # noqa: E402
from support_python.logging import ToolLogger  # noqa: E402

TOOL_NAME = "lint-markdown"
DESCRIPTION = """Automated markdown linter enforcing repository markdown styling guidelines.
Directory walks skip Git-ignored files; files named explicitly are always linted."""


def find_project_root(path: Path) -> Path:
    """Find the root of the project containing path by searching upward for repository or project markers."""
    resolved = path.resolve()
    current = resolved.parent if resolved.is_file() else resolved
    for directory in [current, *current.parents]:
        if (directory / ".git").exists():
            return directory
    for directory in [current, *current.parents]:
        if any(
            (directory / marker).exists()
            for marker in ("PLAN.md", "pyproject.toml", "package.json", "pom.xml", "build.gradle", "go.mod", "Cargo.toml")
        ):
            return directory
    return current


def _resolve_workspace_root(project_root: Path) -> Path:
    """Resolve the workspace parent directory containing sibling repositories, handling .plan/work worktrees."""
    parts = project_root.parts
    for idx in range(len(parts) - 1):
        if parts[idx] == ".plan" and parts[idx + 1] == "work" and idx >= 1:
            return Path(*parts[:idx]).parent
    return project_root.parent


REPO_ROOT = find_project_root(Path.cwd())

DEFAULT_EXCLUDES = [
    ".git",
    "node_modules",
    ".venv",
    "venv",
    "work",
    "build",
    "dist",
    ".idea",
    ".vscode",
    "__pycache__",
    ".plan/work",
]

SHORT_USAGE = f"{TOOL_NAME} {{check|fix|help|version}} [{{{{path}}}}...] [options]"


@dataclass
class LintIssue:
    file_path: Path
    line_number: int
    column_number: int
    rule_id: str
    rule_name: str
    message: str
    severity: str = "ERROR"
    fixable: bool = False

    def format(self, relative_to: Optional[Path] = None) -> str:
        path_str = str(self.file_path)
        if relative_to:
            try:
                path_str = str(self.file_path.relative_to(relative_to))
            except ValueError:
                pass
        return f"{path_str}:{self.line_number}:{self.column_number}: {self.rule_id} [{self.rule_name}] {self.message}"


def normalize_alignment(align: Optional[str]) -> str:
    """Normalize alignment specifier to 'left', 'center', or 'right'."""
    if not align:
        return "left"
    clean = align.strip().lower()
    if clean in ("center", "c", ":center:") or (clean.startswith(":") and clean.endswith(":") and len(clean) >= 3):
        return "center"
    if clean in ("right", "r", ":right:") or (clean.endswith(":") and len(clean) >= 2):
        return "right"
    return "left"


def find_delimiter_pipes(line: str) -> List[int]:
    """Find character indices of unescaped, non-code-span table pipe delimiters."""
    pipes: List[int] = []
    in_code = False
    code_ticks = 0
    i = 0
    n = len(line)
    while i < n:
        ch = line[i]
        if ch == "`":
            start = i
            while i < n and line[i] == "`":
                i += 1
            tick_count = i - start
            if not in_code:
                in_code = True
                code_ticks = tick_count
            elif tick_count == code_ticks:
                in_code = False
                code_ticks = 0
            continue
        elif ch == "\\" and not in_code:
            i += 2
            continue
        elif ch == "|" and not in_code:
            pipes.append(i)
        i += 1
    return pipes


def split_table_row(line: str) -> List[str]:
    """Split a table line into stripped cell strings based on unescaped pipe delimiters."""
    pipes = find_delimiter_pipes(line)
    if len(pipes) < 2:
        return []
    cells: List[str] = []
    for start, end in zip(pipes[:-1], pipes[1:]):
        cells.append(line[start + 1 : end].strip())
    return cells


def is_table_delimiter_row(line: str) -> bool:
    """Check whether a line is a valid Markdown table separator/delimiter row."""
    cells = split_table_row(line)
    if not cells:
        return False
    return all(bool(re.match(r"^:?-+:?$", cell)) for cell in cells)


def format_table(
    headers: List[str],
    rows: List[List[str]],
    alignments: Optional[List[str]] = None,
) -> str:
    """Format a GitHub Flavored Markdown table with vertically aligned columns and padded separators."""
    if not headers:
        return ""

    num_cols = len(headers)
    norm_alignments = [normalize_alignment(alignments[i] if alignments and i < len(alignments) else None) for i in range(num_cols)]

    col_widths = [max(3, len(str(h))) for h in headers]
    str_rows: List[List[str]] = []
    for row in rows:
        row_cells = [str(cell) for cell in row]
        while len(row_cells) < num_cols:
            row_cells.append("")
        str_rows.append(row_cells[:num_cols])
        for i, cell in enumerate(row_cells[:num_cols]):
            col_widths[i] = max(col_widths[i], len(cell))

    # Header line
    header_cells: List[str] = []
    for h, w, align in zip(headers, col_widths, norm_alignments):
        if align == "center":
            header_cells.append(str(h).center(w))
        elif align == "right":
            header_cells.append(str(h).rjust(w))
        else:
            header_cells.append(str(h).ljust(w))
    header_line = "| " + " | ".join(header_cells) + " |"

    # Separator line
    sep_cells: List[str] = []
    for align, w in zip(norm_alignments, col_widths):
        if align == "center":
            sep_cells.append(":" + "-" * max(1, w - 2) + ":")
        elif align == "right":
            sep_cells.append("-" * max(2, w - 1) + ":")
        else:
            sep_cells.append(":" + "-" * max(2, w - 1))
    sep_line = "| " + " | ".join(sep_cells) + " |"

    # Data row lines
    lines = [header_line, sep_line]
    for row in str_rows:
        formatted_cells: List[str] = []
        for cell, w, align in zip(row, col_widths, norm_alignments):
            if align == "center":
                formatted_cells.append(cell.center(w))
            elif align == "right":
                formatted_cells.append(cell.rjust(w))
            else:
                formatted_cells.append(cell.ljust(w))
        lines.append("| " + " | ".join(formatted_cells) + " |")

    return "\n".join(lines)


def format_markdown_table_block(table_lines: List[str]) -> List[str]:
    """Reformat a sequence of table lines into vertically aligned Markdown table lines."""
    if len(table_lines) < 2:
        return list(table_lines)

    prefix_match = re.match(r"^(\s*(?:>\s*)*)", table_lines[0])
    prefix = prefix_match.group(1) if prefix_match else ""

    headers = split_table_row(table_lines[0])
    delim_cells = split_table_row(table_lines[1])
    alignments = [normalize_alignment(cell) for cell in delim_cells]

    data_rows = [split_table_row(line) for line in table_lines[2:]]

    formatted_table_str = format_table(headers, data_rows, alignments=alignments)
    formatted_lines = formatted_table_str.split("\n")

    if prefix:
        return [f"{prefix}{line}" for line in formatted_lines]
    return formatted_lines


def check_table_alignment(
    lines: List[str],
    file_path: Optional[Path] = None,
    rule_id: str = "MD017",
    rule_name: str = "aligned-tables",
) -> List[LintIssue]:
    """Scan markdown lines for table blocks and report vertical alignment / padding violations."""
    target_path = file_path if file_path is not None else Path("<unknown>")
    issues: List[LintIssue] = []
    in_code_block = False
    code_fence_char = ""
    code_fence_len = 0
    in_html_comment = False
    in_frontmatter = False

    re_code_fence = re.compile(r"^(\s*)(`{3,}|~{3,})(.*)$")

    i = 0
    num_lines = len(lines)

    while i < num_lines:
        line = lines[i]
        unquoted = re.sub(r"^\s*(?:>\s*)+", "", line)

        # Frontmatter
        if i == 0 and unquoted.strip() == "---":
            in_frontmatter = True
            i += 1
            continue
        if in_frontmatter:
            if unquoted.strip() == "---":
                in_frontmatter = False
            i += 1
            continue

        # Code block tracking
        fence_match = re_code_fence.match(unquoted)
        if fence_match:
            _, fence, _ = fence_match.groups()
            fence_char = fence[0]
            fence_count = len(fence)
            if not in_code_block:
                in_code_block = True
                code_fence_char = fence_char
                code_fence_len = fence_count
            else:
                if fence_char == code_fence_char and fence_count >= code_fence_len:
                    in_code_block = False
                    code_fence_char = ""
                    code_fence_len = 0
            i += 1
            continue

        if in_code_block:
            i += 1
            continue

        # HTML comment tracking
        if "<!--" in unquoted and "-->" not in unquoted:
            in_html_comment = True
            i += 1
            continue
        if in_html_comment:
            if "-->" in unquoted:
                in_html_comment = False
            i += 1
            continue

        # Table detection
        pipes = find_delimiter_pipes(line)
        if len(pipes) >= 2 and i + 1 < num_lines:
            next_line = lines[i + 1]
            if is_table_delimiter_row(next_line):
                table_line_indices = [i, i + 1]
                k = i + 2
                while k < num_lines:
                    k_line = lines[k]
                    k_unquoted = re.sub(r"^\s*(?:>\s*)+", "", k_line)
                    if not k_unquoted.strip():
                        break
                    if len(find_delimiter_pipes(k_line)) < 2:
                        break
                    table_line_indices.append(k)
                    k += 1

                expected_pipes = pipes
                for row_idx in table_line_indices:
                    row_line = lines[row_idx]
                    row_pipes = find_delimiter_pipes(row_line)
                    if row_pipes != expected_pipes:
                        col = row_pipes[0] + 1 if row_pipes else 1
                        issues.append(
                            LintIssue(
                                file_path=target_path,
                                line_number=row_idx + 1,
                                column_number=col,
                                rule_id=rule_id,
                                rule_name=rule_name,
                                message="Markdown table columns and delimiter pipes are not vertically aligned",
                                fixable=True,
                            )
                        )

                i = k
                continue

        i += 1

    return issues


class MarkdownLinter:
    """Linter implementing dev-guidelines markdown styling checks."""

    # Rule definitions
    RULES = {
        "MD001": ("heading-increment", "Heading levels should only increment by 1 level at a time"),
        "MD002": ("single-h1", "Document should contain at most one top-level H1 heading"),
        "MD003": ("no-numbered-headings", "Headings must not start with numbering prefixes"),
        "MD004": ("no-bold-heading", "Bold text on its own line must not be used as a heading substitute"),
        "MD005": ("dash-bullets", "Unordered list items must use dash '-' bullets"),
        "MD006": ("no-fully-bold-bullet", "Bullet items should not bold the entire sentence or clause"),
        "MD007": ("code-block-language", "Fenced code blocks must specify a language identifier"),
        "MD008": ("no-raw-urls", "Raw unformatted URLs in prose must use markdown links or code spans"),
        "MD009": ("no-file-uri", "Local file:/// URIs must not be used for repository references"),
        "MD010": ("no-tabs", "Hard tabs must not be used for indentation"),
        "MD011": ("trailing-whitespace", "Lines must not contain trailing whitespace"),
        "MD012": ("line-endings", "Files should use LF line endings"),
        "MD013": ("no-task-ids-in-changelog", "Changelog bullets must not contain task identifiers (Tnnnn or Annnn)"),
        "MD014": ("valid-relative-links", "Relative markdown links must resolve to existing files on disk"),
        "MD015": ("no-blank-line-after-subheading", "Headings below H1 (H2 through H6) must not be followed by a blank line"),
        "MD016": ("no-blank-line-before-list", "Sentences introducing a list must not be followed by a blank line"),
        "MD017": ("aligned-tables", "Markdown table columns must be vertically aligned with padding spaces"),
        "MD018": ("valid-external-links", "External markdown links must return HTTP 200/OK"),
        "MD019": ("file-references-as-links", "File references in prose must be formatted as markdown links"),
    }

    FILE_EXTENSIONS = {"py", "md", "sh", "json", "yaml", "yml", "ts", "js", "java", "gradle", "toml"}
    TECH_NAMES = {"node.js", "next.js", "vue.js", "three.js", "react.js", "express.js", "nest.js"}
    GENERIC_FILES = {
        "readme.md",
        "license.md",
        "changelog.md",
        "plan.md",
        "package.json",
        "package-lock.json",
        "pnpm-lock.yaml",
        "pyproject.toml",
        "pom.xml",
        "build.gradle",
        "settings.gradle",
        "__init__.py",
        "package-info.java",
        "docs/index.md",
        "docs/requirements.md",
        "docs/devops.md",
        "bootstrap-dev-environment.py",
        "devops.py",
        "run-checks.py",
        "test-service.py",
    }
    RE_BARE_PATH = re.compile(r"(?<![a-zA-Z0-9_/-])(?:\.{1,2}/|[a-zA-Z0-9_-]+/)+[a-zA-Z0-9_.-]+\.([a-zA-Z0-9]+)(?![a-zA-Z0-9_/-])")
    RE_BARE_NAME = re.compile(r"\b([a-zA-Z0-9_-]+\.([a-zA-Z0-9]+))\b")

    def __init__(
        self,
        enabled_rules: Optional[Set[str]] = None,
        offline: bool = False,
        timeout: float = 10.0,
        project_root: Optional[Path] = None,
    ) -> None:
        self.enabled_rules = enabled_rules if enabled_rules is not None else set(self.RULES.keys())
        if offline:
            self.enabled_rules.discard("MD018")
        self.offline = offline
        self.timeout = timeout
        self.project_root = project_root.resolve() if project_root is not None else None
        self._url_cache: dict[str, Optional[str]] = {}
        self._file_headings_cache: dict[Path, Set[str]] = {}
        self._project_root_cache: dict[Path, Path] = {}

    def _resolve_project_root(self, file_path: Path) -> Path:
        """Resolve the project root for the given file path."""
        if self.project_root is not None:
            return self.project_root
        parent = file_path.resolve().parent
        if parent in self._project_root_cache:
            return self._project_root_cache[parent]
        root = find_project_root(file_path)
        self._project_root_cache[parent] = root
        return root

    def is_rule_enabled(self, rule_id: str) -> bool:
        return rule_id in self.enabled_rules

    @staticmethod
    def _slugify(text: str) -> str:
        cleaned = re.sub(r"`[^`]+`", lambda m: m.group(0)[1:-1], text)
        cleaned = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", cleaned)
        slug = re.sub(r"[^\w\s-]", "", cleaned.lower()).strip()
        slug = re.sub(r"[\s_]+", "-", slug)
        return re.sub(r"-+", "-", slug)

    def _get_file_headings(self, path: Path) -> Set[str]:
        if path in self._file_headings_cache:
            return self._file_headings_cache[path]
        slugs: Set[str] = set()
        if path.exists() and path.is_file():
            try:
                content = path.read_text(encoding="utf-8", errors="replace")
                re_h = re.compile(r"^(#{1,6})\s+(.*)$")
                for line in content.splitlines():
                    uq = re.sub(r"^\s*(?:>\s*)+", "", line)
                    m = re_h.match(uq)
                    if m:
                        slugs.add(self._slugify(m.group(2)))
            except Exception:
                pass
        self._file_headings_cache[path] = slugs
        return slugs

    def _validate_external_url(self, url: str, project_root: Optional[Path] = None) -> Optional[str]:
        if url in self._url_cache:
            return self._url_cache[url]

        parsed = urllib.parse.urlparse(url)
        netloc = parsed.netloc.lower()
        if (
            not netloc
            or netloc in ("localhost", "127.0.0.1")
            or netloc.endswith((".example.com", ".example.org", ".example.net", ".test", ".invalid", ".localhost"))
            or netloc in ("example.com", "example.org", "example.net")
            or "..." in url
            or "appengine.google.com/ns" in url
        ):
            self._url_cache[url] = None
            return None

        m_repo = re.match(
            r"^https?://github\.com/gpellicciotta/([^/]+?)(?:\.git)?(?:/(?:blob|tree)/[^/]+/(.+)|/?)$",
            url,
        )
        if m_repo:
            repo_name = m_repo.group(1)
            subpath = m_repo.group(2)
            base_root = project_root if project_root is not None else REPO_ROOT
            workspace_root = _resolve_workspace_root(base_root)
            target_repo = base_root if repo_name == base_root.name else (workspace_root / repo_name).resolve()
            if target_repo.exists():
                if not subpath:
                    self._url_cache[url] = None
                    return None
                else:
                    repo_rel = subpath.split("#")[0].split("?")[0]
                    repo_file = (target_repo / urllib.parse.unquote(repo_rel)).resolve()
                    if repo_file.exists():
                        self._url_cache[url] = None
                        return None
                    else:
                        err = f"Repository file '{repo_rel}' does not exist on disk in '{repo_name}'"
                        self._url_cache[url] = err
                        return err

        headers = {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36"
            )
        }

        check_url = url
        if check_url.endswith(".git") and "github.com" in netloc:
            check_url = check_url[:-4]

        status: Optional[str] = None
        try:
            req = urllib.request.Request(check_url, headers=headers, method="HEAD")
            with urllib.request.urlopen(req, timeout=self.timeout) as resp:
                if resp.status >= 400:
                    status = f"HTTP {resp.status}"
        except urllib.error.HTTPError as e:
            if e.code in (401, 403, 405):
                try:
                    req_get = urllib.request.Request(check_url, headers=headers, method="GET")
                    with urllib.request.urlopen(req_get, timeout=self.timeout) as resp:
                        if resp.status >= 400:
                            status = f"HTTP {resp.status}"
                except urllib.error.HTTPError as e2:
                    status = f"HTTP {e2.code}"
                except Exception as e2:
                    status = str(e2)
            else:
                status = f"HTTP {e.code}"
        except Exception:
            # Fallback to GET on timeout or connection errors
            try:
                req_get = urllib.request.Request(check_url, headers=headers, method="GET")
                with urllib.request.urlopen(req_get, timeout=self.timeout) as resp:
                    if resp.status >= 400:
                        status = f"HTTP {resp.status}"
            except urllib.error.HTTPError as e2:
                status = f"HTTP {e2.code}"
            except Exception as e2:
                status = str(e2)

        self._url_cache[url] = status
        return status

    def lint_content(
        self,
        file_path: Path,
        raw_bytes: bytes,
        project_root: Optional[Path] = None,
    ) -> List[LintIssue]:
        issues: List[LintIssue] = []
        current_project_root = project_root.resolve() if project_root is not None else self._resolve_project_root(file_path)
        actual_file_path = file_path if file_path.is_absolute() else (current_project_root / file_path).resolve()

        # Check line endings (MD012)
        if self.is_rule_enabled("MD012"):
            has_crlf = b"\r\n" in raw_bytes
            has_bare_lf = b"\n" in raw_bytes.replace(b"\r\n", b"")
            if has_crlf and has_bare_lf:
                issues.append(
                    LintIssue(
                        file_path=file_path,
                        line_number=1,
                        column_number=1,
                        rule_id="MD012",
                        rule_name=self.RULES["MD012"][0],
                        message="File contains mixed line endings (both CRLF and LF); standardize on LF",
                        fixable=True,
                    )
                )

        text = raw_bytes.decode("utf-8", errors="replace")
        lines = text.splitlines(keepends=False)

        in_frontmatter = False
        in_code_block = False
        code_fence_char = ""
        code_fence_len = 0
        in_html_comment = False

        h1_count = 0
        last_heading_level = 0
        is_changelog = file_path.name.lower() == "changelog.md"
        in_released_changelog = False

        is_taskfile = ".plan" in file_path.parts and "tasks" in file_path.parts
        is_historical_task = False
        if is_taskfile:
            for header_line in lines[:30]:
                m_status = re.match(r"^status:\s*['\"]?(\w+)", header_line.strip(), re.IGNORECASE)
                if m_status and m_status.group(1).lower() in ("completed", "cancelled", "failed"):
                    is_historical_task = True
                    break
                m_date = re.match(r"^(?:date|started|ended):\s*['\"]?(\d{4}-\d{2}-\d{2})", header_line.strip(), re.IGNORECASE)
                if m_date and m_date.group(1) < "2026-10-11":
                    is_historical_task = True
                    break
            if not is_historical_task:
                m_tid = re.search(r"^T(\d{4})", file_path.name)
                if m_tid and int(m_tid.group(1)) < 125:
                    is_historical_task = True

        # Pattern matches
        re_code_fence = re.compile(r"^(\s*)(`{3,}|~{3,})(.*)$")
        re_heading = re.compile(r"^(#{1,6})\s+(.*)$")
        re_numbered_heading = re.compile(r"^(#{1,6})\s+(?:\d+(?:\.\d+)*[\.\)]?|\d+\s*[-–—])\s+(.*)$")
        re_bold_heading = re.compile(r"^\s*\*\*([^*]+)\*\*[:\s]*$")
        re_bullet = re.compile(r"^(\s*)([\*\+\-])\s+(.*)$")
        re_raw_url = re.compile(r"https?://[^\s)\]>`\"']+")
        re_file_uri = re.compile(r"file:///[^\s)\]>`\"']+")
        re_task_id = re.compile(r"\b[AT]\d{4}\b")
        re_markdown_link = re.compile(r"!?\[((?:[^\[\]]|\[[^\[\]]*\])*)\]\((.*?)\)")
        re_ref_def = re.compile(r"^\s*\[([^\]]+)\]:\s*(\S+)")
        re_list_item = re.compile(r"^(\s*)(?:[-*+]|\d+\.)\s+")

        local_heading_slugs: Set[str] = set()
        for raw_line in lines:
            uq = re.sub(r"^\s*(?:>\s*)+", "", raw_line)
            m_h = re_heading.match(uq)
            if m_h:
                local_heading_slugs.add(self._slugify(m_h.group(2)))

        for idx, line in enumerate(lines, start=1):
            # Check trailing whitespace (MD011)
            if self.is_rule_enabled("MD011") and (line.endswith(" ") or line.endswith("\t")):
                issues.append(
                    LintIssue(
                        file_path=file_path,
                        line_number=idx,
                        column_number=len(line),
                        rule_id="MD011",
                        rule_name=self.RULES["MD011"][0],
                        message="Line contains trailing whitespace",
                        fixable=True,
                    )
                )

            # Check tabs (MD010)
            if self.is_rule_enabled("MD010") and "\t" in line:
                col = line.index("\t") + 1
                issues.append(
                    LintIssue(
                        file_path=file_path,
                        line_number=idx,
                        column_number=col,
                        rule_id="MD010",
                        rule_name=self.RULES["MD010"][0],
                        message="Line contains hard tab character; indent with spaces",
                        fixable=True,
                    )
                )

            # Strip blockquote prefix (e.g. "  > ", "> ", ">>> ") for semantic structure checking
            unquoted_line = re.sub(r"^\s*(?:>\s*)+", "", line)

            # Handle frontmatter at start of file
            if idx == 1 and unquoted_line.strip() == "---":
                in_frontmatter = True
                continue
            if in_frontmatter:
                if unquoted_line.strip() == "---":
                    in_frontmatter = False
                continue

            # Handle fenced code blocks (both unquoted and inside blockquotes)
            fence_match = re_code_fence.match(unquoted_line)
            if fence_match:
                indent, fence, rest = fence_match.groups()
                fence_char = fence[0]
                fence_count = len(fence)

                if not in_code_block:
                    in_code_block = True
                    code_fence_char = fence_char
                    code_fence_len = fence_count
                    lang = rest.strip()
                    # Check MD007
                    if self.is_rule_enabled("MD007") and not lang:
                        issues.append(
                            LintIssue(
                                file_path=file_path,
                                line_number=idx,
                                column_number=len(indent) + 1,
                                rule_id="MD007",
                                rule_name=self.RULES["MD007"][0],
                                message="Fenced code block lacks a language identifier",
                            )
                        )
                    continue
                else:
                    if fence_char == code_fence_char and fence_count >= code_fence_len:
                        in_code_block = False
                        code_fence_char = ""
                        code_fence_len = 0
                        continue

            if in_code_block:
                continue

            # Handle HTML comments
            if "<!--" in unquoted_line and "-->" not in unquoted_line:
                in_html_comment = True
                continue
            if in_html_comment:
                if "-->" in unquoted_line:
                    in_html_comment = False
                continue

            # Check Headings
            heading_match = re_heading.match(unquoted_line)
            if heading_match:
                hashes, title = heading_match.groups()
                level = len(hashes)

                if is_changelog and level == 2:
                    m_date = re.search(r"\[(?:released:\s*)?(\d{4}-\d{2}-\d{2})\]", title, re.IGNORECASE)
                    if m_date and m_date.group(1) < "2026-10-11":
                        in_released_changelog = True
                    else:
                        in_released_changelog = False

                if level == 1:
                    h1_count += 1
                    if self.is_rule_enabled("MD002") and h1_count > 1:
                        issues.append(
                            LintIssue(
                                file_path=file_path,
                                line_number=idx,
                                column_number=1,
                                rule_id="MD002",
                                rule_name=self.RULES["MD002"][0],
                                message=f"Multiple H1 headings found (H1 #{h1_count})",
                            )
                        )

                if self.is_rule_enabled("MD001"):
                    if last_heading_level > 0 and level > last_heading_level + 1:
                        issues.append(
                            LintIssue(
                                file_path=file_path,
                                line_number=idx,
                                column_number=1,
                                rule_id="MD001",
                                rule_name=self.RULES["MD001"][0],
                                message=f"Heading level skipped from H{last_heading_level} to H{level}",
                            )
                        )
                last_heading_level = level

                if self.is_rule_enabled("MD003"):
                    num_match = re_numbered_heading.match(unquoted_line)
                    if num_match:
                        issues.append(
                            LintIssue(
                                file_path=file_path,
                                line_number=idx,
                                column_number=1,
                                rule_id="MD003",
                                rule_name=self.RULES["MD003"][0],
                                message=f"Numbered heading prefix found: '{title.strip()}'",
                            )
                        )

                if self.is_rule_enabled("MD015") and not is_historical_task and level >= 2:
                    if idx < len(lines):
                        next_line = lines[idx]
                        next_unquoted = re.sub(r"^\s*(?:>\s*)+", "", next_line)
                        if next_unquoted.strip() == "":
                            k = idx
                            while k < len(lines):
                                k_unquoted = re.sub(r"^\s*(?:>\s*)+", "", lines[k])
                                if k_unquoted.strip() == "":
                                    k += 1
                                else:
                                    break
                            if k < len(lines):
                                target_unquoted = re.sub(r"^\s*(?:>\s*)+", "", lines[k])
                                if not re_heading.match(target_unquoted) and not target_unquoted.strip().startswith(
                                    ("---", "***", "___")
                                ):
                                    issues.append(
                                        LintIssue(
                                            file_path=file_path,
                                            line_number=idx,
                                            column_number=1,
                                            rule_id="MD015",
                                            rule_name=self.RULES["MD015"][0],
                                            message=f"Heading '{title.strip()}' (H{level}) must not be followed by a blank line before content",
                                            fixable=True,
                                        )
                                    )
                continue

            # Check bold text on its own line masquerading as heading (MD004)
            # Only flag outside blockquotes (blockquotes often use > **Lead-in:** for notes/examples)
            if self.is_rule_enabled("MD004") and not line.strip().startswith(">"):
                if not unquoted_line.startswith("- ") and not unquoted_line.startswith("|"):
                    bold_match = re_bold_heading.match(unquoted_line)
                    if bold_match and len(bold_match.group(1).split()) < 8:
                        issues.append(
                            LintIssue(
                                file_path=file_path,
                                line_number=idx,
                                column_number=1,
                                rule_id="MD004",
                                rule_name=self.RULES["MD004"][0],
                                message=f"Bold text on own line used as heading: '{unquoted_line.strip()}'",
                            )
                        )

            # Check sentence introducing a list (MD016)
            if self.is_rule_enabled("MD016"):
                if (
                    unquoted_line.rstrip().endswith(":")
                    and not re_heading.match(unquoted_line)
                    and not unquoted_line.strip().startswith("|")
                    and not unquoted_line.strip().startswith("<!--")
                ):
                    if idx < len(lines):
                        next_line = lines[idx]
                        next_unquoted = re.sub(r"^\s*(?:>\s*)+", "", next_line)
                        if next_unquoted.strip() == "":
                            k = idx
                            while k < len(lines):
                                k_unquoted = re.sub(r"^\s*(?:>\s*)+", "", lines[k])
                                if k_unquoted.strip() == "":
                                    k += 1
                                else:
                                    break
                            if k < len(lines):
                                target_unquoted = re.sub(r"^\s*(?:>\s*)+", "", lines[k])
                                if re_list_item.match(target_unquoted):
                                    issues.append(
                                        LintIssue(
                                            file_path=file_path,
                                            line_number=idx,
                                            column_number=1,
                                            rule_id="MD016",
                                            rule_name=self.RULES["MD016"][0],
                                            message="Sentence introducing a list must not be followed by a blank line",
                                            fixable=True,
                                        )
                                    )

            # Check List items (MD005, MD006)
            bullet_match = re_bullet.match(unquoted_line)
            if bullet_match:
                indent_ws, bullet_char, item_body = bullet_match.groups()
                col = len(line) - len(unquoted_line) + len(indent_ws) + 1

                if self.is_rule_enabled("MD005") and bullet_char in ("*", "+"):
                    issues.append(
                        LintIssue(
                            file_path=file_path,
                            line_number=idx,
                            column_number=col,
                            rule_id="MD005",
                            rule_name=self.RULES["MD005"][0],
                            message=f"Non-dash bullet indicator '{bullet_char}' used; use '-' instead",
                            fixable=True,
                        )
                    )

                if self.is_rule_enabled("MD006"):
                    body_stripped = item_body.strip()
                    if body_stripped.startswith("**") and body_stripped.endswith("**"):
                        inner = body_stripped[2:-2]
                        if "**" not in inner and not inner.endswith(":"):
                            issues.append(
                                LintIssue(
                                    file_path=file_path,
                                    line_number=idx,
                                    column_number=col,
                                    rule_id="MD006",
                                    rule_name=self.RULES["MD006"][0],
                                    message="Entire bullet item is bolded; bold only terms/glossaries",
                                )
                            )

                if is_changelog and self.is_rule_enabled("MD013"):
                    task_match = re_task_id.search(item_body)
                    if task_match:
                        task_col = line.find(task_match.group(0)) + 1
                        issues.append(
                            LintIssue(
                                file_path=file_path,
                                line_number=idx,
                                column_number=task_col if task_col > 0 else col,
                                rule_id="MD013",
                                rule_name=self.RULES["MD013"][0],
                                message=f"Task identifier '{task_match.group(0)}' found in changelog bullet; release notes must not contain task IDs",
                            )
                        )

            # Check for raw URLs (MD008) and file:/// URIs (MD009)
            # Strip inline code spans first so code examples aren't flagged
            sanitized = re.sub(r"`[^`]+`", "", unquoted_line)
            # Strip HTML comments
            sanitized = re.sub(r"<!--.*?-->", "", sanitized)

            if self.is_rule_enabled("MD009"):
                file_uri_match = re_file_uri.search(sanitized)
                if file_uri_match:
                    issues.append(
                        LintIssue(
                            file_path=file_path,
                            line_number=idx,
                            column_number=line.find(file_uri_match.group(0)) + 1,
                            rule_id="MD009",
                            rule_name=self.RULES["MD009"][0],
                            message="Local file:/// URI used; use relative repository markdown links",
                        )
                    )

            if self.is_rule_enabled("MD008"):
                # Strip out markdown links [text](url)
                sanitized_urls = re.sub(r"\[[^\]]*\]\([^\)]*\)", "", sanitized)
                # Strip out markdown reference definitions [id]: url
                sanitized_urls = re.sub(r"^\s*\[[^\]]+\]:\s*\S+", "", sanitized_urls)
                # Strip out autolinks <http://...>
                sanitized_urls = re.sub(r"<https?://[^>]+>", "", sanitized_urls)

                raw_match = re_raw_url.search(sanitized_urls)
                if raw_match:
                    issues.append(
                        LintIssue(
                            file_path=file_path,
                            line_number=idx,
                            column_number=line.find(raw_match.group(0)) + 1,
                            rule_id="MD008",
                            rule_name=self.RULES["MD008"][0],
                            message=f"Raw URL found in prose: '{raw_match.group(0)}'; enclose in markdown link",
                        )
                    )

            # Check for invalid relative links (MD014)
            if self.is_rule_enabled("MD014") and not is_historical_task and not in_released_changelog:
                candidate_targets: List[Tuple[str, str, int]] = []
                for link_match in re_markdown_link.finditer(sanitized):
                    raw_target = link_match.group(2).strip()
                    if raw_target.startswith("<"):
                        angle_match = re.match(r"^<([^>]+)>", raw_target)
                        target = angle_match.group(1).strip() if angle_match else raw_target
                    else:
                        target = raw_target.split()[0] if raw_target else ""
                    if target:
                        candidate_targets.append((target, raw_target, link_match.start()))

                ref_match = re_ref_def.match(sanitized)
                if ref_match:
                    raw_target = ref_match.group(2).strip()
                    target = raw_target.strip("<>")
                    if target:
                        candidate_targets.append((target, raw_target, ref_match.start(2)))

                for target, raw_target, match_start in candidate_targets:
                    if target.startswith(
                        ("http://", "https://", "ftp://", "mailto:", "tel:", "data:", "javascript:", "irc:", "news:")
                    ):
                        continue
                    if target.startswith("file://"):
                        continue
                    if re.match(r"^[a-zA-Z][a-zA-Z0-9+.-]*://", target):
                        continue

                    col = line.find(target) + 1
                    if col <= 0:
                        col = line.find(raw_target) + 1
                    if col <= 0:
                        col = match_start + 1

                    if target.startswith("#"):
                        anchor = urllib.parse.unquote(target[1:].split("?")[0]).lower()
                        if (
                            anchor
                            and anchor not in ("top", "")
                            and not re.match(r"^l\d+(?:-l?\d+)?$", anchor)
                            and not re.match(r"^line-\d+$", anchor)
                            and anchor not in local_heading_slugs
                        ):
                            issues.append(
                                LintIssue(
                                    file_path=file_path,
                                    line_number=idx,
                                    column_number=col,
                                    rule_id="MD014",
                                    rule_name=self.RULES["MD014"][0],
                                    message=f"Intra-document anchor '{target}' does not match any heading in the document",
                                )
                            )
                        continue

                    path_part = target.split("#", 1)[0].split("?", 1)[0]
                    anchor_part = target.split("#", 1)[1].split("?", 1)[0] if "#" in target else ""
                    if not path_part:
                        continue

                    unquoted_path = urllib.parse.unquote(path_part)
                    target_path = Path(unquoted_path)
                    if target_path.is_absolute():
                        continue

                    if unquoted_path.startswith("/") or unquoted_path.startswith("\\"):
                        resolved = (current_project_root / unquoted_path.lstrip("/\\")).resolve()
                    else:
                        resolved = (file_path.parent / target_path).resolve()

                    if not resolved.exists():
                        issues.append(
                            LintIssue(
                                file_path=file_path,
                                line_number=idx,
                                column_number=col,
                                rule_id="MD014",
                                rule_name=self.RULES["MD014"][0],
                                message=f"Relative link '{target}' does not resolve to an existing file on disk",
                            )
                        )
                    elif anchor_part and resolved.suffix.lower() == ".md":
                        target_slugs = self._get_file_headings(resolved)
                        anchor_slug = urllib.parse.unquote(anchor_part).lower()
                        if (
                            anchor_slug
                            and anchor_slug not in ("top", "")
                            and not re.match(r"^l\d+(?:-l?\d+)?$", anchor_slug)
                            and not re.match(r"^line-\d+$", anchor_slug)
                            and anchor_slug not in target_slugs
                        ):
                            issues.append(
                                LintIssue(
                                    file_path=file_path,
                                    line_number=idx,
                                    column_number=col,
                                    rule_id="MD014",
                                    rule_name=self.RULES["MD014"][0],
                                    message=f"Relative link '{target}' anchor '#{anchor_part}' does not match any heading in '{path_part}'",
                                )
                            )

            # Check for invalid external links (MD018)
            if self.is_rule_enabled("MD018") and not self.offline:
                external_targets: List[Tuple[str, str, int]] = []
                for link_match in re_markdown_link.finditer(sanitized):
                    raw_target = link_match.group(2).strip()
                    if raw_target.startswith("<"):
                        angle_match = re.match(r"^<([^>]+)>", raw_target)
                        target = angle_match.group(1).strip() if angle_match else raw_target
                    else:
                        target = raw_target.split()[0] if raw_target else ""
                    if target.startswith(("http://", "https://")):
                        external_targets.append((target, raw_target, link_match.start()))

                ref_match = re_ref_def.match(sanitized)
                if ref_match:
                    raw_target = ref_match.group(2).strip()
                    target = raw_target.strip("<>")
                    if target.startswith(("http://", "https://")):
                        external_targets.append((target, raw_target, ref_match.start(2)))

                for target, raw_target, match_start in external_targets:
                    err = self._validate_external_url(target, project_root=current_project_root)
                    if err:
                        col = line.find(target) + 1
                        if col <= 0:
                            col = line.find(raw_target) + 1
                        if col <= 0:
                            col = match_start + 1
                        issues.append(
                            LintIssue(
                                file_path=file_path,
                                line_number=idx,
                                column_number=col,
                                rule_id="MD018",
                                rule_name=self.RULES["MD018"][0],
                                message=f"External link '{target}' failed validation: {err}",
                            )
                        )

            # Check for file references that should be markdown links (MD019)
            if self.is_rule_enabled("MD019"):
                if not is_historical_task and not in_released_changelog:
                    lower_unquoted = unquoted_line.lower()
                    if "avoid " not in lower_unquoted and "anti-pattern" not in lower_unquoted and "e.g. " not in lower_unquoted:
                        no_links = re_markdown_link.sub("", unquoted_line)
                        no_links = re_ref_def.sub("", no_links)
                        no_links = re.sub(r"<[^>]+>", "", no_links)

                        # Check bare paths in prose (outside backticks)
                        no_code = re.sub(r"`[^`]+`", "", no_links)
                        for match in self.RE_BARE_PATH.finditer(no_code):
                            ext = match.group(1).lower()
                            val = match.group(0)
                            if (
                                ext in self.FILE_EXTENSIONS
                                and "{{" not in val
                                and val.lower() not in self.TECH_NAMES
                                and val.lower() not in self.GENERIC_FILES
                            ):
                                col = line.find(val) + 1
                                issues.append(
                                    LintIssue(
                                        file_path=file_path,
                                        line_number=idx,
                                        column_number=col if col > 0 else 1,
                                        rule_id="MD019",
                                        rule_name=self.RULES["MD019"][0],
                                        message=f"Bare file path '{val}' found in prose; format as markdown link [filename](path)",
                                    )
                                )

                        # Check backticked file references in prose
                        for match in re.finditer(r"`([^`]+)`", no_links):
                            val = match.group(1).strip()
                            if " " in val or "{{" in val or "}}" in val or "*" in val or "~" in val:
                                continue
                            if val.lower() in self.TECH_NAMES or val.lower() in self.GENERIC_FILES:
                                continue
                            if val.startswith("http://") or val.startswith("https://") or val.startswith("file:"):
                                continue
                            if re.match(r"^[a-zA-Z]:[/\\]", val) or val.startswith("/") or val.startswith("\\"):
                                continue

                            parts = val.replace("\\", "/").split("/")
                            name = parts[-1]
                            if "." in name:
                                ext = name.rsplit(".", 1)[1].lower()
                                if ext in self.FILE_EXTENSIONS:
                                    repo_file = (current_project_root / val).resolve()
                                    local_file = (actual_file_path.parent / val).resolve()
                                    is_repo_match = repo_file.is_relative_to(current_project_root) and repo_file.exists()
                                    is_local_match = local_file.is_relative_to(current_project_root) and local_file.exists()
                                    if is_repo_match or is_local_match:
                                        col = line.find(f"`{val}`") + 1
                                        issues.append(
                                            LintIssue(
                                                file_path=file_path,
                                                line_number=idx,
                                                column_number=col if col > 0 else 1,
                                                rule_id="MD019",
                                                rule_name=self.RULES["MD019"][0],
                                                message=f"Repository file reference '{val}' in prose must be formatted as markdown link [filename](path)",
                                            )
                                        )

        # Check table alignment (MD017)
        if self.is_rule_enabled("MD017"):
            table_issues = check_table_alignment(
                lines,
                file_path=file_path,
                rule_id="MD017",
                rule_name=self.RULES["MD017"][0],
            )
            issues.extend(table_issues)

        return issues

    def fix_content(self, file_path: Path, raw_bytes: bytes) -> bytes:
        """Apply safe automatic fixes to markdown content."""
        text = raw_bytes.decode("utf-8", errors="replace")
        # Normalize CRLF to LF
        text = text.replace("\r\n", "\n")

        lines = text.split("\n")
        fixed_lines: List[str] = []
        in_code_block = False
        code_fence_char = ""
        code_fence_len = 0

        re_code_fence = re.compile(r"^(\s*)(`{3,}|~{3,})(.*)$")
        re_bullet = re.compile(r"^(\s*)([\*\+])\s+(.*)$")

        for line in lines:
            unquoted = re.sub(r"^\s*(?:>\s*)+", "", line)
            fence_match = re_code_fence.match(unquoted)
            if fence_match:
                indent, fence, rest = fence_match.groups()
                fence_char = fence[0]
                fence_count = len(fence)

                if not in_code_block:
                    in_code_block = True
                    code_fence_char = fence_char
                    code_fence_len = fence_count
                else:
                    if fence_char == code_fence_char and fence_count >= code_fence_len:
                        in_code_block = False
                        code_fence_char = ""
                        code_fence_len = 0

            fixed_line = line
            # Fix bullet indicators outside code blocks
            if not in_code_block and self.is_rule_enabled("MD005"):
                bullet_match = re_bullet.match(unquoted)
                if bullet_match:
                    indent_ws, bullet_char, item_body = bullet_match.groups()
                    quote_prefix = line[: len(line) - len(unquoted)]
                    fixed_line = f"{quote_prefix}{indent_ws}- {item_body}"

            # Fix hard tabs (outside or inside code blocks, convert tab to 4 spaces)
            if self.is_rule_enabled("MD010"):
                fixed_line = fixed_line.replace("\t", "    ")

            # Fix trailing whitespace
            if self.is_rule_enabled("MD011"):
                fixed_line = fixed_line.rstrip(" \t")

            fixed_lines.append(fixed_line)

        # Multi-line structural fixes (MD015, MD016, MD017)
        if not self.is_rule_enabled("MD015") and not self.is_rule_enabled("MD016") and not self.is_rule_enabled("MD017"):
            fixed_text = "\n".join(fixed_lines)
            if raw_bytes.endswith(b"\n") and not fixed_text.endswith("\n"):
                fixed_text += "\n"
            return fixed_text.encode("utf-8")

        result_lines: List[str] = []
        i = 0
        in_code_block = False
        code_fence_char = ""
        code_fence_len = 0
        in_frontmatter = False

        re_heading = re.compile(r"^(#{2,6})\s+(.*)$")
        re_list_item = re.compile(r"^(\s*)(?:[-*+]|\d+\.)\s+")

        while i < len(fixed_lines):
            line = fixed_lines[i]
            unquoted = re.sub(r"^\s*(?:>\s*)+", "", line)

            # Track frontmatter
            if i == 0 and unquoted.strip() == "---":
                in_frontmatter = True
                result_lines.append(line)
                i += 1
                continue
            if in_frontmatter:
                if unquoted.strip() == "---":
                    in_frontmatter = False
                result_lines.append(line)
                i += 1
                continue

            # Track code fences
            fence_match = re_code_fence.match(unquoted)
            if fence_match:
                indent, fence, rest = fence_match.groups()
                fence_char = fence[0]
                fence_count = len(fence)

                if not in_code_block:
                    in_code_block = True
                    code_fence_char = fence_char
                    code_fence_len = fence_count
                else:
                    if fence_char == code_fence_char and fence_count >= code_fence_len:
                        in_code_block = False
                        code_fence_char = ""
                        code_fence_len = 0
                result_lines.append(line)
                i += 1
                continue

            if in_code_block:
                result_lines.append(line)
                i += 1
                continue

            # Check table block formatting (MD017)
            if self.is_rule_enabled("MD017"):
                pipes = find_delimiter_pipes(line)
                if len(pipes) >= 2 and i + 1 < len(fixed_lines):
                    if is_table_delimiter_row(fixed_lines[i + 1]):
                        k = i + 2
                        while k < len(fixed_lines):
                            k_unquoted = re.sub(r"^\s*(?:>\s*)+", "", fixed_lines[k])
                            if not k_unquoted.strip():
                                break
                            if len(find_delimiter_pipes(fixed_lines[k])) < 2:
                                break
                            k += 1
                        table_lines = fixed_lines[i:k]
                        aligned_table = format_markdown_table_block(table_lines)
                        result_lines.extend(aligned_table)
                        i = k
                        continue

            result_lines.append(line)

            # Check if current line is a subheading (MD015)
            if self.is_rule_enabled("MD015") and re_heading.match(unquoted):
                k = i + 1
                while k < len(fixed_lines):
                    k_unquoted = re.sub(r"^\s*(?:>\s*)+", "", fixed_lines[k])
                    if k_unquoted.strip() == "":
                        k += 1
                    else:
                        break
                if k < len(fixed_lines) and k > i + 1:
                    target_unquoted = re.sub(r"^\s*(?:>\s*)+", "", fixed_lines[k])
                    if not re_heading.match(target_unquoted) and not target_unquoted.strip().startswith(("---", "***", "___")):
                        i = k - 1
                i += 1
                continue

            # Check if current line is a list-intro sentence (MD016)
            if (
                self.is_rule_enabled("MD016")
                and unquoted.rstrip().endswith(":")
                and not re_heading.match(unquoted)
                and not unquoted.strip().startswith("|")
                and not unquoted.strip().startswith("<!--")
            ):
                k = i + 1
                while k < len(fixed_lines):
                    k_unquoted = re.sub(r"^\s*(?:>\s*)+", "", fixed_lines[k])
                    if k_unquoted.strip() == "":
                        k += 1
                    else:
                        break
                if k < len(fixed_lines) and k > i + 1:
                    target_unquoted = re.sub(r"^\s*(?:>\s*)+", "", fixed_lines[k])
                    if re_list_item.match(target_unquoted):
                        i = k
                        continue

            i += 1

        fixed_text = "\n".join(result_lines)
        if raw_bytes.endswith(b"\n") and not fixed_text.endswith("\n"):
            fixed_text += "\n"
        return fixed_text.encode("utf-8")


def should_exclude(path: Path, base_dir: Path, excludes: List[str]) -> bool:
    try:
        rel_path = path.relative_to(base_dir)
    except ValueError:
        rel_path = path

    parts = rel_path.parts
    for part in parts:
        for excl in excludes:
            if fnmatch.fnmatch(part, excl):
                return True

    rel_str = str(rel_path).replace("\\", "/")
    for excl in excludes:
        if fnmatch.fnmatch(rel_str, excl) or fnmatch.fnmatch(f"*/{rel_str}", excl):
            return True

    return False


def find_git_ignored(paths: List[Path], cwd: Path) -> Set[Path]:
    """Return the subset of paths, relative to cwd, that Git ignores, asking Git once per call.

    Returns an empty set outside a Git work tree or when Git is unavailable.
    """
    if not paths:
        return set()
    stdin = "\0".join(path.as_posix() for path in paths) + "\0"
    try:
        result = subprocess.run(
            ["git", "check-ignore", "--stdin", "-z"],
            cwd=cwd,
            input=stdin.encode("utf-8"),
            capture_output=True,
            check=False,
        )
    except OSError:
        return set()
    # Exit code 0 means some paths are ignored, 1 means none, anything else is a Git error.
    if result.returncode != 0:
        return set()
    ignored = result.stdout.decode("utf-8", errors="replace").split("\0")
    return {Path(name) for name in ignored if name}


def discover_markdown_files(paths: List[Path], base_dir: Path, excludes: List[str]) -> List[Path]:
    results: List[Path] = []
    seen: Set[Path] = set()

    for p in paths:
        target = p.resolve()
        if not target.exists():
            continue

        if target.is_file():
            if target.suffix.lower() == ".md" and not should_exclude(target, base_dir, excludes):
                if target not in seen:
                    seen.add(target)
                    results.append(target)
        elif target.is_dir():
            # Pairs of walk path relative to target (for Git) and resolved path (for linting)
            candidates: List[Tuple[Path, Path]] = []
            for root, dirs, files in os.walk(target):
                # Prune excluded directories in-place
                dirs[:] = [d for d in dirs if not should_exclude(Path(root) / d, base_dir, excludes)]
                for file in files:
                    if file.lower().endswith(".md"):
                        walk_path = Path(root) / file
                        file_path = walk_path.resolve()
                        if not should_exclude(file_path, base_dir, excludes) and file_path not in seen:
                            candidates.append((walk_path.relative_to(target), file_path))
            # Skip Git-ignored files found by walking; explicitly named files are always linted.
            # Symlinks may resolve outside target, so Git is asked about the unresolved walk paths.
            ignored = find_git_ignored([rel for rel, _ in candidates], target)
            for rel, file_path in candidates:
                if rel not in ignored and file_path not in seen:
                    seen.add(file_path)
                    results.append(file_path)

    return sorted(results)


def report_argument_error(message: str) -> NoReturn:
    """Log an argument error with the standard severity indicator, then exit with code 2."""
    early_logger = ToolHarness(name=TOOL_NAME, description=DESCRIPTION)._extract_early_logger(sys.argv[1:])
    early_logger.error(f"{message}\nUsage: {SHORT_USAGE}; run '{TOOL_NAME} help' for details.")
    early_logger.close()
    sys.exit(2)


def configure_lint_parser(parser: argparse.ArgumentParser) -> None:
    """Add the path arguments and standard error reporting to the 'check' and 'fix' parsers."""
    parser.add_argument("paths", nargs="*", type=Path)
    # Accept paths before, between, and after options, as the original parser did
    parser.parse_args = parser.parse_intermixed_args  # type: ignore[method-assign]
    parser.error = report_argument_error  # type: ignore[method-assign]


def parse_rule_codes(value: Optional[str]) -> Optional[Set[str]]:
    """Parse a comma-separated rule code list, returning None to enable every rule."""
    if value is None:
        return None
    return {code.strip().upper() for code in value.split(",") if code.strip()}


def plural(count: int, noun: str) -> str:
    """Return the count followed by the noun, pluralized when the count is not one."""
    return f"{count} {noun}{'s' if count != 1 else ''}"


def run_lint(args: argparse.Namespace, logger: ToolLogger, fix: bool) -> int:
    """Lint the markdown files under the requested paths, fixing safe issues first when asked."""
    repo_root = Path.cwd()
    for p in args.paths:
        if not p.resolve().exists():
            logger.error(f"Path does not exist: {p}")
            return 2
    input_paths = list(args.paths) or [repo_root]

    excludes = DEFAULT_EXCLUDES + (args.exclude or [])
    files = discover_markdown_files(input_paths, repo_root, excludes)
    linter = MarkdownLinter(enabled_rules=parse_rule_codes(args.rules), offline=args.offline, timeout=args.timeout)
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
            try:
                rel = file_path.relative_to(repo_root)
            except ValueError:
                rel = file_path
            logger.info(f"OK: {rel}")

    # Report issues as plain command output
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
    lines = ["Rules:"]
    for rule_id, (name, description) in MarkdownLinter.RULES.items():
        lines.append(f"  {rule_id}  {name:<{width}}  {description}")
    lines.extend(
        [
            "",
            "Path selection:",
            "  Without paths, lints every markdown file under the current directory.",
            "  Directory walks skip Git-ignored files; files named explicitly are always linted.",
            f"  Default excludes: {', '.join(DEFAULT_EXCLUDES)}",
        ]
    )
    return "\n".join(lines)


def build_harness() -> ToolHarness:
    """Build the command-line harness exposing the 'check' and 'fix' actions."""

    def handle_check(args: argparse.Namespace, logger: ToolLogger) -> int:
        return run_lint(args, logger, fix=args.fix)

    def handle_fix(args: argparse.Namespace, logger: ToolLogger) -> int:
        return run_lint(args, logger, fix=True)

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
    harness.add_global_argument("--offline", action="store_true", help="skip external link checks (rule MD018)")
    harness.add_global_argument(
        "--timeout", type=float, default=10.0, metavar="SECONDS", help="external link timeout in seconds (default: 10.0)"
    )
    harness.add_action(
        "check",
        "lint markdown files and report violations",
        handler=handle_check,
        detail="\n".join(
            [
                "Lints the markdown files under each path, or under the current directory when no",
                "path is given, and prints one line per violation. Exits 1 if any violation is found.",
                "With --fix, applies safe fixes first, exactly like the 'fix' action.",
            ]
        ),
        usage_suffix="[{{path}}...] [options]",
        configure_parser=configure_lint_parser,
    )
    harness.add_action(
        "fix",
        "fix safe formatting issues in-place, then lint",
        handler=handle_fix,
        detail="\n".join(
            [
                "Rewrites files in-place to normalize line endings, bullet markers, tabs, trailing",
                "whitespace, blank lines after subheadings and before lists, and table alignment,",
                "then lints the result like 'check'.",
                "Exits 1 if violations remain that cannot be fixed automatically.",
            ]
        ),
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
