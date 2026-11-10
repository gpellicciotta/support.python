"""
Automated markdown linter enforcing dev-guidelines markdown styling standards.
Validates file format, encoding, heading hierarchy, list formatting, URLs, code block languages,
and anti-patterns across repository markdown files.
"""

from __future__ import annotations

import fnmatch
import os
import re
import subprocess
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, List, Optional, Set, Tuple, Union


from support_python.markdown.profiles import LintProfile, get_profile
from support_python.markdown.registry import LintContext, Rule, RuleRegistry
from support_python.markdown.rules import DEFAULT_REGISTRY


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

    def to_dict(self, relative_to: Optional[Path] = None) -> dict[str, object]:
        """Serialize this issue as a JSON-compatible dictionary."""
        path_str = str(self.file_path)
        if relative_to:
            try:
                path_str = str(self.file_path.relative_to(relative_to))
            except ValueError:
                pass
        return {
            "path": path_str,
            "line": self.line_number,
            "column": self.column_number,
            "rule_id": self.rule_id,
            "rule_name": self.rule_name,
            "message": self.message,
            "fixable": self.fixable,
        }


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
        "MD011": ("trailing-whitespace", "Lines must not end in a tab or in more than two spaces"),
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
        "agents.md",
        "claude.md",
        "gemini.md",
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
        ".lint-markdown.json",
        ".markdown-lint.json",
    }

    RE_BARE_PATH = re.compile(r"(?<![a-zA-Z0-9_/-])(?:\.{1,2}/|[a-zA-Z0-9_-]+/)+[a-zA-Z0-9_.-]+\.([a-zA-Z0-9]+)(?![a-zA-Z0-9_/-])")
    RE_BARE_NAME = re.compile(r"\b([a-zA-Z0-9_-]+\.([a-zA-Z0-9]+))\b")

    _SCOPE_RULE_ORDER: dict[str, Tuple[str, ...]] = {
        "document_pre": ("MD012",),
        "raw_line": ("MD011", "MD010"),
        "code_fence": ("MD007",),
        "heading": ("MD002", "MD001", "MD003", "MD015"),
        "prose": ("MD004", "MD016", "MD005", "MD006", "MD013", "MD009", "MD008", "MD014", "MD018", "MD019"),
        "document_post": ("MD017",),
    }

    def __init__(
        self,
        enabled_rules: Optional[Set[str]] = None,
        offline: bool = False,
        timeout: float = 10.0,
        project_root: Optional[Path] = None,
        profile: Optional[Union[str, LintProfile]] = None,
        registry: Optional[RuleRegistry] = None,
        github_owners: Optional[Iterable[str]] = None,
    ) -> None:
        self.registry: RuleRegistry = registry if registry is not None else DEFAULT_REGISTRY
        resolved_profile = get_profile(profile, self.registry) if isinstance(profile, str) else profile
        self.profile: Optional[LintProfile] = resolved_profile
        self.historical_task_exemptions: bool = (
            resolved_profile.historical_task_exemptions if resolved_profile is not None else True
        )
        if github_owners is not None:
            self.github_owners: tuple[str, ...] = tuple(github_owners)
        elif resolved_profile is not None:
            self.github_owners = resolved_profile.github_owners
        else:
            self.github_owners = ()
        if self.github_owners:
            owners_pattern = "|".join(re.escape(o) for o in self.github_owners)
            self._github_repo_re: Optional[re.Pattern[str]] = re.compile(
                rf"^https?://github\.com/(?:{owners_pattern})/([^/]+?)(?:\.git)?(?:/(?:blob|tree)/[^/]+/(.+)|/?)$",
                re.IGNORECASE,
            )
        else:
            self._github_repo_re = None
        if enabled_rules is not None:
            self.enabled_rules = {r.rule_id for r in self.registry.select(enabled_rules)}
        elif resolved_profile is not None:
            self.enabled_rules = {r.rule_id for r in self.registry.select(resolved_profile.enabled_rules)}
        else:
            self.enabled_rules = set(self.registry.rule_ids())
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

        if self._github_repo_re is not None:
            m_repo = self._github_repo_re.match(url)
            if m_repo:
                repo_name = m_repo.group(1)
                subpath = m_repo.group(2)
                base_root = project_root or self.project_root or find_project_root(Path.cwd())
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

        def _get() -> Optional[str]:
            try:
                req_get = urllib.request.Request(check_url, headers=headers, method="GET")
                with urllib.request.urlopen(req_get, timeout=self.timeout) as resp:
                    if resp.status >= 400:
                        return f"HTTP {resp.status}"
                    return None
            except urllib.error.HTTPError as e:
                return f"HTTP {e.code}"
            except Exception as e:
                return str(e)

        status: Optional[str] = None
        try:
            req = urllib.request.Request(check_url, headers=headers, method="HEAD")
            with urllib.request.urlopen(req, timeout=self.timeout) as resp:
                if resp.status in (401, 403, 404, 405):
                    status = _get()
                elif resp.status >= 400:
                    status = f"HTTP {resp.status}"
        except urllib.error.HTTPError as e:
            if e.code in (401, 403, 404, 405):
                status = _get()
            else:
                status = f"HTTP {e.code}"
        except Exception:
            # Fallback to GET on timeout or connection errors
            status = _get()

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

        is_taskfile = self.historical_task_exemptions and ".plan" in file_path.parts and "tasks" in file_path.parts
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

        re_code_fence = re.compile(r"^(\s*)(`{3,}|~{3,})(.*)$")
        re_heading = re.compile(r"^(#{1,6})\s+(.*)$")
        re_bullet = re.compile(r"^(\s*)([\*\+\-])\s+(.*)$")

        local_heading_slugs: Set[str] = set()
        for raw_line in lines:
            uq = re.sub(r"^\s*(?:>\s*)+", "", raw_line)
            m_h = re_heading.match(uq)
            if m_h:
                local_heading_slugs.add(self._slugify(m_h.group(2)))

        active_by_id = {rule.rule_id: rule for rule in self.registry if rule.rule_id in self.enabled_rules}
        scoped_rules: dict[str, List[Rule]] = {scope: [] for scope in self._SCOPE_RULE_ORDER}
        seen_ids: Set[str] = set()
        for scope, ordered_ids in self._SCOPE_RULE_ORDER.items():
            for rid in ordered_ids:
                if rid in active_by_id:
                    scoped_rules[scope].append(active_by_id[rid])
                    seen_ids.add(rid)
        for rule in active_by_id.values():
            if rule.rule_id not in seen_ids:
                scoped_rules.setdefault(rule.scope, []).append(rule)

        ctx = LintContext(
            file_path=file_path,
            actual_file_path=actual_file_path,
            project_root=current_project_root,
            raw_bytes=raw_bytes,
            lines=lines,
            is_changelog=is_changelog,
            in_released_changelog=in_released_changelog,
            is_historical_task=is_historical_task,
            is_task_file=".plan" in file_path.parts and "tasks" in file_path.parts,
            local_heading_slugs=local_heading_slugs,
            linter=self,
        )

        for rule in scoped_rules["document_pre"]:
            issues.extend(rule.check(ctx))

        for idx, line in enumerate(lines, start=1):
            ctx.line_number = idx
            ctx.line = line
            for rule in scoped_rules["raw_line"]:
                issues.extend(rule.check(ctx))

            # Strip blockquote prefix (e.g. "  > ", "> ", ">>> ") for semantic structure checking
            unquoted_line = re.sub(r"^\s*(?:>\s*)+", "", line)
            ctx.unquoted_line = unquoted_line

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
                    ctx.fence_indent = indent
                    ctx.fence_lang = rest.strip()
                    for rule in scoped_rules["code_fence"]:
                        issues.extend(rule.check(ctx))
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
                    in_released_changelog = bool(m_date and m_date.group(1) < "2026-10-11")
                    ctx.in_released_changelog = in_released_changelog

                if level == 1:
                    h1_count += 1
                ctx.heading_level = level
                ctx.heading_title = title
                ctx.prev_heading_level = last_heading_level
                ctx.h1_count = h1_count
                for rule in scoped_rules["heading"]:
                    issues.extend(rule.check(ctx))
                last_heading_level = level
                continue

            ctx.bullet_match = re_bullet.match(unquoted_line)
            sanitized = re.sub(r"`[^`]+`", "", unquoted_line)
            ctx.sanitized = re.sub(r"<!--.*?-->", "", sanitized)
            for rule in scoped_rules["prose"]:
                issues.extend(rule.check(ctx))

        for rule in scoped_rules["document_post"]:
            issues.extend(rule.check(ctx))

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

            # Fix trailing whitespace
            if self.is_rule_enabled("MD011"):
                stripped = fixed_line.rstrip(" \t")
                trailing = fixed_line[len(stripped) :]
                if "\t" in trailing:
                    fixed_line = stripped
                elif len(trailing) > 2:
                    fixed_line = stripped + "  "

            # Fix hard tabs (outside or inside code blocks, convert tab to 4 spaces)
            if self.is_rule_enabled("MD010"):
                fixed_line = fixed_line.replace("\t", "    ")

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


def parse_rule_codes(value: Optional[str]) -> Optional[Set[str]]:
    """Parse a comma-separated rule code list, returning None to enable every rule."""
    if value is None:
        return None
    return {code.strip().upper() for code in value.split(",") if code.strip()}
