"""Registered Markdown lint rule classes (MD001 through MD019)."""

from __future__ import annotations

from pathlib import Path
import re
from typing import TYPE_CHECKING
import urllib.parse

from support_python.markdown.registry import LintContext, Rule, RuleRegistry

if TYPE_CHECKING:
    from support_python.markdown_lint import LintIssue

_RE_HEADING = re.compile(r"^(#{1,6})\s+(.*)$")
_RE_NUMBERED_HEADING = re.compile(r"^(#{1,6})\s+(?:\d+(?:\.\d+)*[\.\)]?|\d+\s*[-–—])\s+(.*)$")
_RE_BOLD_HEADING = re.compile(r"^\s*\*\*([^*]+)\*\*[:\s]*$")
_RE_RAW_URL = re.compile(r"https?://[^\s)\]>`\"']+")
_RE_FILE_URI = re.compile(r"file:///[^\s)\]>`\"']+")
_RE_TASK_ID = re.compile(r"\b[AT]\d{4}\b")
_RE_MARKDOWN_LINK = re.compile(r"!?\[((?:[^\[\]]|\[[^\[\]]*\])*)\]\((.*?)\)")
_RE_REF_DEF = re.compile(r"^\s*\[([^\]]+)\]:\s*(\S+)")
_RE_LIST_ITEM = re.compile(r"^(\s*)(?:[-*+]|\d+\.)\s+")
_RE_UNQUOTE = re.compile(r"^\s*(?:>\s*)+")


def _extract_links(sanitized: str, external_only: bool = False) -> list[tuple[str, str, int]]:
    """Extract (target, raw_target, match_start) tuples from inline links and reference definitions."""
    targets: list[tuple[str, str, int]] = []
    for m in _RE_MARKDOWN_LINK.finditer(sanitized):
        raw = m.group(2).strip()
        if raw.startswith("<"):
            am = re.match(r"^<([^>]+)>", raw)
            target = am.group(1).strip() if am else raw
        else:
            target = raw.split()[0] if raw else ""
        if target and (not external_only or target.startswith(("http://", "https://"))):
            targets.append((target, raw, m.start()))
    ref_m = _RE_REF_DEF.match(sanitized)
    if ref_m:
        raw = ref_m.group(2).strip()
        target = raw.strip("<>")
        if target and (not external_only or target.startswith(("http://", "https://"))):
            targets.append((target, raw, ref_m.start(2)))
    return targets


class MD001HeadingIncrement(Rule):
    """Rule MD001: Heading levels should only increment by 1 level at a time."""

    rule_id, name, scope = "MD001", "heading-increment", "heading"
    description = "Heading levels should only increment by 1 level at a time"

    def check(self, ctx: LintContext) -> list[LintIssue]:
        if ctx.prev_heading_level > 0 and ctx.heading_level > ctx.prev_heading_level + 1:
            return [self.issue(ctx, f"Heading level skipped from H{ctx.prev_heading_level} to H{ctx.heading_level}")]
        return []


class MD002SingleH1(Rule):
    """Rule MD002: Document should contain at most one top-level H1 heading."""

    rule_id, name, scope = "MD002", "single-h1", "heading"
    description = "Document should contain at most one top-level H1 heading"

    def check(self, ctx: LintContext) -> list[LintIssue]:
        if ctx.heading_level == 1 and ctx.h1_count > 1:
            return [self.issue(ctx, f"Multiple H1 headings found (H1 #{ctx.h1_count})")]
        return []


class MD003NoNumberedHeadings(Rule):
    """Rule MD003: Headings must not start with numbering prefixes."""

    rule_id, name, scope = "MD003", "no-numbered-headings", "heading"
    description = "Headings must not start with numbering prefixes"

    def check(self, ctx: LintContext) -> list[LintIssue]:
        if _RE_NUMBERED_HEADING.match(ctx.unquoted_line):
            return [self.issue(ctx, f"Numbered heading prefix found: '{ctx.heading_title.strip()}'")]
        return []


class MD004NoBoldHeading(Rule):
    """Rule MD004: Bold text on its own line must not be used as a heading substitute."""

    rule_id, name, scope = "MD004", "no-bold-heading", "prose"
    description = "Bold text on its own line must not be used as a heading substitute"

    def check(self, ctx: LintContext) -> list[LintIssue]:
        if not ctx.line.strip().startswith(">") and not ctx.unquoted_line.startswith(("- ", "|")):
            m = _RE_BOLD_HEADING.match(ctx.unquoted_line)
            if m and len(m.group(1).split()) < 8:
                return [self.issue(ctx, f"Bold text on own line used as heading: '{ctx.unquoted_line.strip()}'")]
        return []


class MD005DashBullets(Rule):
    """Rule MD005: Unordered list items must use dash '-' bullets."""

    rule_id, name, scope, fixable = "MD005", "dash-bullets", "prose", True
    description = "Unordered list items must use dash '-' bullets"

    def check(self, ctx: LintContext) -> list[LintIssue]:
        if ctx.bullet_match and ctx.bullet_match.group(2) in ("*", "+"):
            indent_ws, bullet_char, _ = ctx.bullet_match.groups()
            col = len(ctx.line) - len(ctx.unquoted_line) + len(indent_ws) + 1
            return [self.issue(ctx, f"Non-dash bullet indicator '{bullet_char}' used; use '-' instead", column_number=col)]
        return []


class MD006NoFullyBoldBullet(Rule):
    """Rule MD006: Bullet items should not bold the entire sentence or clause."""

    rule_id, name, scope = "MD006", "no-fully-bold-bullet", "prose"
    description = "Bullet items should not bold the entire sentence or clause"

    def check(self, ctx: LintContext) -> list[LintIssue]:
        if ctx.bullet_match:
            indent_ws, _, item_body = ctx.bullet_match.groups()
            body = item_body.strip()
            if body.startswith("**") and body.endswith("**"):
                inner = body[2:-2]
                if "**" not in inner and not inner.endswith(":"):
                    col = len(ctx.line) - len(ctx.unquoted_line) + len(indent_ws) + 1
                    return [self.issue(ctx, "Entire bullet item is bolded; bold only terms/glossaries", column_number=col)]
        return []


class MD007CodeBlockLanguage(Rule):
    """Rule MD007: Fenced code blocks must specify a language identifier."""

    rule_id, name, scope = "MD007", "code-block-language", "code_fence"
    description = "Fenced code blocks must specify a language identifier"

    def check(self, ctx: LintContext) -> list[LintIssue]:
        if not ctx.fence_lang:
            return [self.issue(ctx, "Fenced code block lacks a language identifier", column_number=len(ctx.fence_indent) + 1)]
        return []


class MD008NoRawUrls(Rule):
    """Rule MD008: Raw unformatted URLs in prose must use markdown links or code spans."""

    rule_id, name, scope = "MD008", "no-raw-urls", "prose"
    description = "Raw unformatted URLs in prose must use markdown links or code spans"

    def check(self, ctx: LintContext) -> list[LintIssue]:
        cleaned = re.sub(r"\[[^\]]*\]\([^\)]*\)", "", ctx.sanitized)
        cleaned = re.sub(r"^\s*\[[^\]]+\]:\s*\S+", "", cleaned)
        cleaned = re.sub(r"<https?://[^>]+>", "", cleaned)
        m = _RE_RAW_URL.search(cleaned)
        if m:
            return [
                self.issue(
                    ctx,
                    f"Raw URL found in prose: '{m.group(0)}'; enclose in markdown link",
                    column_number=ctx.line.find(m.group(0)) + 1,
                )
            ]
        return []


class MD009NoFileUri(Rule):
    """Rule MD009: Local file:/// URIs must not be used for repository references."""

    rule_id, name, scope = "MD009", "no-file-uri", "prose"
    description = "Local file:/// URIs must not be used for repository references"

    def check(self, ctx: LintContext) -> list[LintIssue]:
        m = _RE_FILE_URI.search(ctx.sanitized)
        if m:
            return [
                self.issue(
                    ctx,
                    "Local file:/// URI used; use relative repository markdown links",
                    column_number=ctx.line.find(m.group(0)) + 1,
                )
            ]
        return []


class MD010NoTabs(Rule):
    """Rule MD010: Hard tabs must not be used for indentation."""

    rule_id, name, scope, fixable = "MD010", "no-tabs", "raw_line", True
    description = "Hard tabs must not be used for indentation"

    def check(self, ctx: LintContext) -> list[LintIssue]:
        if "\t" in ctx.line:
            return [self.issue(ctx, "Line contains hard tab character; indent with spaces", column_number=ctx.line.index("\t") + 1)]
        return []


class MD011TrailingWhitespace(Rule):
    """Rule MD011: Lines must not contain trailing whitespace."""

    rule_id, name, scope, fixable = "MD011", "trailing-whitespace", "raw_line", True
    description = "Lines must not contain trailing whitespace"

    def check(self, ctx: LintContext) -> list[LintIssue]:
        if ctx.line.endswith((" ", "\t")):
            return [self.issue(ctx, "Line contains trailing whitespace", column_number=len(ctx.line))]
        return []


class MD012LineEndings(Rule):
    """Rule MD012: Files should use LF line endings."""

    rule_id, name, scope, fixable = "MD012", "line-endings", "document_pre", True
    description = "Files should use LF line endings"

    def check(self, ctx: LintContext) -> list[LintIssue]:
        if b"\r\n" in ctx.raw_bytes and b"\n" in ctx.raw_bytes.replace(b"\r\n", b""):
            return [
                self.issue(
                    ctx, "File contains mixed line endings (both CRLF and LF); standardize on LF", line_number=1, column_number=1
                )
            ]
        return []


class MD013NoTaskIdsInChangelog(Rule):
    """Rule MD013: Changelog bullets must not contain task identifiers (Tnnnn or Annnn)."""

    rule_id, name, scope = "MD013", "no-task-ids-in-changelog", "prose"
    description = "Changelog bullets must not contain task identifiers (Tnnnn or Annnn)"

    def check(self, ctx: LintContext) -> list[LintIssue]:
        if ctx.is_changelog and ctx.bullet_match:
            indent_ws, _, item_body = ctx.bullet_match.groups()
            m = _RE_TASK_ID.search(item_body)
            if m:
                col = len(ctx.line) - len(ctx.unquoted_line) + len(indent_ws) + 1
                t_col = ctx.line.find(m.group(0)) + 1
                msg = f"Task identifier '{m.group(0)}' found in changelog bullet; release notes must not contain task IDs"
                return [self.issue(ctx, msg, column_number=t_col if t_col > 0 else col)]
        return []


class MD014ValidRelativeLinks(Rule):
    """Rule MD014: Relative markdown links must resolve to existing files on disk."""

    rule_id, name, scope = "MD014", "valid-relative-links", "prose"
    description = "Relative markdown links must resolve to existing files on disk"

    @staticmethod
    def _is_missing_anchor(anchor: str, slugs: set[str]) -> bool:
        return bool(
            anchor
            and anchor not in ("top", "")
            and not re.match(r"^l\d+(?:-l?\d+)?$", anchor)
            and not re.match(r"^line-\d+$", anchor)
            and anchor not in slugs
        )

    def check(self, ctx: LintContext) -> list[LintIssue]:
        if ctx.is_historical_task or ctx.in_released_changelog:
            return []
        issues: list[LintIssue] = []
        for target, raw_target, match_start in _extract_links(ctx.sanitized):
            if target.startswith(
                ("http://", "https://", "ftp://", "mailto:", "tel:", "data:", "javascript:", "irc:", "news:", "file://")
            ):
                continue
            if re.match(r"^[a-zA-Z][a-zA-Z0-9+.-]*://", target):
                continue
            col = ctx.line.find(target) + 1 or ctx.line.find(raw_target) + 1 or (match_start + 1)
            if target.startswith("#"):
                anchor = urllib.parse.unquote(target[1:].split("?")[0]).lower()
                if self._is_missing_anchor(anchor, ctx.local_heading_slugs):
                    issues.append(
                        self.issue(
                            ctx, f"Intra-document anchor '{target}' does not match any heading in the document", column_number=col
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
            resolved = (
                (ctx.project_root / unquoted_path.lstrip("/\\")).resolve()
                if unquoted_path.startswith(("/", "\\"))
                else (ctx.file_path.parent / target_path).resolve()
            )
            if not resolved.exists():
                issues.append(
                    self.issue(ctx, f"Relative link '{target}' does not resolve to an existing file on disk", column_number=col)
                )
            elif anchor_part and resolved.suffix.lower() == ".md":
                slugs = ctx.linter._get_file_headings(resolved) if ctx.linter else set()
                if self._is_missing_anchor(urllib.parse.unquote(anchor_part).lower(), slugs):
                    msg = f"Relative link '{target}' anchor '#{anchor_part}' does not match any heading in '{path_part}'"
                    issues.append(self.issue(ctx, msg, column_number=col))
        return issues


class MD015NoBlankLineAfterSubheading(Rule):
    """Rule MD015: Headings below H1 (H2 through H6) must not be followed by a blank line."""

    rule_id, name, scope, fixable = "MD015", "no-blank-line-after-subheading", "heading", True
    description = "Headings below H1 (H2 through H6) must not be followed by a blank line"

    def check(self, ctx: LintContext) -> list[LintIssue]:
        if not ctx.is_historical_task and ctx.heading_level >= 2 and ctx.line_number < len(ctx.lines):
            if _RE_UNQUOTE.sub("", ctx.lines[ctx.line_number]).strip() == "":
                k = ctx.line_number
                while k < len(ctx.lines) and _RE_UNQUOTE.sub("", ctx.lines[k]).strip() == "":
                    k += 1
                if k < len(ctx.lines):
                    target_uq = _RE_UNQUOTE.sub("", ctx.lines[k])
                    if not _RE_HEADING.match(target_uq) and not target_uq.strip().startswith(("---", "***", "___")):
                        msg = f"Heading '{ctx.heading_title.strip()}' (H{ctx.heading_level}) must not be followed by a blank line before content"
                        return [self.issue(ctx, msg)]
        return []


class MD016NoBlankLineBeforeList(Rule):
    """Rule MD016: Sentences introducing a list must not be followed by a blank line."""

    rule_id, name, scope, fixable = "MD016", "no-blank-line-before-list", "prose", True
    description = "Sentences introducing a list must not be followed by a blank line"

    def check(self, ctx: LintContext) -> list[LintIssue]:
        uq = ctx.unquoted_line
        if uq.rstrip().endswith(":") and not _RE_HEADING.match(uq) and not uq.strip().startswith(("|", "<!--")):
            if ctx.line_number < len(ctx.lines) and _RE_UNQUOTE.sub("", ctx.lines[ctx.line_number]).strip() == "":
                k = ctx.line_number
                while k < len(ctx.lines) and _RE_UNQUOTE.sub("", ctx.lines[k]).strip() == "":
                    k += 1
                if k < len(ctx.lines) and _RE_LIST_ITEM.match(_RE_UNQUOTE.sub("", ctx.lines[k])):
                    return [self.issue(ctx, "Sentence introducing a list must not be followed by a blank line")]
        return []


class MD017AlignedTables(Rule):
    """Rule MD017: Markdown table columns must be vertically aligned with padding spaces."""

    rule_id, name, scope, fixable = "MD017", "aligned-tables", "document_post", True
    description = "Markdown table columns must be vertically aligned with padding spaces"

    def check(self, ctx: LintContext) -> list[LintIssue]:
        from support_python.markdown_lint import check_table_alignment

        return check_table_alignment(ctx.lines, file_path=ctx.file_path, rule_id=self.rule_id, rule_name=self.name)


class MD018ValidExternalLinks(Rule):
    """Rule MD018: External markdown links must return HTTP 200/OK."""

    rule_id, name, scope = "MD018", "valid-external-links", "prose"
    description = "External markdown links must return HTTP 200/OK"

    def check(self, ctx: LintContext) -> list[LintIssue]:
        if ctx.linter is None or ctx.linter.offline:
            return []
        issues: list[LintIssue] = []
        for target, raw_target, match_start in _extract_links(ctx.sanitized, external_only=True):
            err = ctx.linter._validate_external_url(target, project_root=ctx.project_root)
            if err:
                col = ctx.line.find(target) + 1 or ctx.line.find(raw_target) + 1 or (match_start + 1)
                issues.append(self.issue(ctx, f"External link '{target}' failed validation: {err}", column_number=col))
        return issues


class MD019FileReferencesAsLinks(Rule):
    """Rule MD019: File references in prose must be formatted as markdown links."""

    rule_id, name, scope = "MD019", "file-references-as-links", "prose"
    description = "File references in prose must be formatted as markdown links"

    def check(self, ctx: LintContext) -> list[LintIssue]:
        from support_python.markdown_lint import MarkdownLinter

        if ctx.is_historical_task or ctx.in_released_changelog:
            return []
        lower_uq = ctx.unquoted_line.lower()
        if "avoid " in lower_uq or "anti-pattern" in lower_uq or "e.g. " in lower_uq:
            return []
        no_links = re.sub(r"<[^>]+>", "", _RE_REF_DEF.sub("", _RE_MARKDOWN_LINK.sub("", ctx.unquoted_line)))
        issues: list[LintIssue] = []
        for m in MarkdownLinter.RE_BARE_PATH.finditer(re.sub(r"`[^`]+`", "", no_links)):
            ext, val = m.group(1).lower(), m.group(0)
            if (
                ext in MarkdownLinter.FILE_EXTENSIONS
                and "{{" not in val
                and val.lower() not in MarkdownLinter.TECH_NAMES
                and val.lower() not in MarkdownLinter.GENERIC_FILES
            ):
                col = ctx.line.find(val) + 1
                issues.append(
                    self.issue(
                        ctx,
                        f"Bare file path '{val}' found in prose; format as markdown link [filename](path)",
                        column_number=col if col > 0 else 1,
                    )
                )
        for m in re.finditer(r"`([^`]+)`", no_links):
            val = m.group(1).strip()
            if (
                any(tok in val for tok in (" ", "{{", "}}", "*", "~"))
                or val.lower() in MarkdownLinter.TECH_NAMES
                or val.lower() in MarkdownLinter.GENERIC_FILES
            ):
                continue
            if val.startswith(("http://", "https://", "file:", "/", "\\")) or re.match(r"^[a-zA-Z]:[/\\]", val):
                continue
            name = val.replace("\\", "/").split("/")[-1]
            if "." in name and name.rsplit(".", 1)[1].lower() in MarkdownLinter.FILE_EXTENSIONS:
                repo_f = (ctx.project_root / val).resolve()
                local_f = (ctx.actual_file_path.parent / val).resolve()
                if (repo_f.is_relative_to(ctx.project_root) and repo_f.exists()) or (
                    local_f.is_relative_to(ctx.project_root) and local_f.exists()
                ):
                    col = ctx.line.find(f"`{val}`") + 1
                    issues.append(
                        self.issue(
                            ctx,
                            f"Repository file reference '{val}' in prose must be formatted as markdown link [filename](path)",
                            column_number=col if col > 0 else 1,
                        )
                    )
        return issues


ALL_RULE_CLASSES: tuple[type[Rule], ...] = (
    MD001HeadingIncrement,
    MD002SingleH1,
    MD003NoNumberedHeadings,
    MD004NoBoldHeading,
    MD005DashBullets,
    MD006NoFullyBoldBullet,
    MD007CodeBlockLanguage,
    MD008NoRawUrls,
    MD009NoFileUri,
    MD010NoTabs,
    MD011TrailingWhitespace,
    MD012LineEndings,
    MD013NoTaskIdsInChangelog,
    MD014ValidRelativeLinks,
    MD015NoBlankLineAfterSubheading,
    MD016NoBlankLineBeforeList,
    MD017AlignedTables,
    MD018ValidExternalLinks,
    MD019FileReferencesAsLinks,
)

DEFAULT_RULES: tuple[Rule, ...] = tuple(cls() for cls in ALL_RULE_CLASSES)
RULES_BY_ID: dict[str, Rule] = {rule.rule_id: rule for rule in DEFAULT_RULES}
DEFAULT_REGISTRY: RuleRegistry = RuleRegistry(DEFAULT_RULES)
