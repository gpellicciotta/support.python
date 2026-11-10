#!/usr/bin/env python3
"""
Deterministically generate guidelines/agent-digest.md from core guideline files and extract
modular agent skills (skills/<name>/SKILL.md) from guidelines that define a 'skill:' YAML block.
All blockquote ('>') lines containing rationale, background, and templates are filtered out.
"""

from __future__ import annotations

import argparse
import difflib
import os
import re
import sys
from pathlib import Path
from typing import Dict, List, Tuple

from support_python.cli import PROJECT_VERSION, ToolHarness
from support_python.logging import CliLogger
from support_python.tools.agent_files import find_project_root

TOOL_NAME = "agent-digest"
TOOL_VERSION = PROJECT_VERSION

REPO_ROOT = find_project_root(Path.cwd())
GUIDELINES_DIR = REPO_ROOT / "guidelines"
DIGEST_PATH = GUIDELINES_DIR / "agent-digest.md"
SKILLS_DIR = REPO_ROOT / "skills"
_INITIAL_REPO_ROOT = REPO_ROOT
_INITIAL_GUIDELINES_DIR = GUIDELINES_DIR
_INITIAL_SKILLS_DIR = SKILLS_DIR


def _resolve_repo_root() -> Path:
    """Return REPO_ROOT if overridden by a caller, or resolve from the current working directory."""
    return REPO_ROOT if REPO_ROOT is not _INITIAL_REPO_ROOT else find_project_root(Path.cwd())


def _resolve_guidelines_dir() -> Path:
    """Return GUIDELINES_DIR if overridden by a caller, or resolve under the active repository root."""
    return GUIDELINES_DIR if GUIDELINES_DIR is not _INITIAL_GUIDELINES_DIR else _resolve_repo_root() / "guidelines"


def _resolve_skills_dir() -> Path:
    """Return SKILLS_DIR if overridden by a caller, or resolve under the active repository root."""
    return SKILLS_DIR if SKILLS_DIR is not _INITIAL_SKILLS_DIR else _resolve_repo_root() / "skills"


SOURCE_FILES = [
    "ai-agent-guidelines.md",
    "general-guidelines.md",
    "testing-guidelines.md",
    "process-management-guidelines.md",
    "change-management-guidelines.md",
    "cli-guidelines.md",
    "logging-guidelines.md",
    "database-guidelines.md",
    "project-setup-guidelines.md",
    "markdown-guidelines.md",
    "ui-guidelines.md",
    "javascript-guidelines.md",
    "java-guidelines.md",
    "python-guidelines.md",
]

MAX_DIGEST_BYTES = 20 * 1024  # 20 KiB (20,480 bytes) hard size budget
MAX_DIFF_LINES = 50
PLAN_OWNED_SKILLS = {"plan-task-usage-guidelines", "research-guidelines"}


def parse_frontmatter_yaml(raw_yaml: str) -> Dict:
    """Strict, dependency-free parser for supported frontmatter subset.

    Supported subset:
    - top-level mappings (e.g. 'skill:')
    - second-level scalar values (e.g. 'name: foo')
    - second-level folded block scalars (e.g. 'description: >-')
    - second-level string lists (e.g. 'globs:\\n    - "*.py"')
    """
    lines = raw_yaml.splitlines()
    result: Dict = {}
    current_top_key: str | None = None
    current_sub_key: str | None = None
    in_folded_scalar = False
    folded_lines: List[str] = []
    in_string_list = False
    list_items: List[str] = []

    def flush_sub_key() -> None:
        nonlocal in_folded_scalar, folded_lines, in_string_list, list_items, current_sub_key
        if current_top_key is None or current_sub_key is None:
            return
        if in_folded_scalar:
            desc = " ".join(line.strip() for line in folded_lines if line.strip())
            result[current_top_key][current_sub_key] = desc
            folded_lines = []
            in_folded_scalar = False
        elif in_string_list:
            result[current_top_key][current_sub_key] = list_items
            list_items = []
            in_string_list = False
        current_sub_key = None

    for line_no, line in enumerate(lines, 1):
        if not line.strip() or line.strip().startswith("#"):
            continue

        if in_folded_scalar:
            if line.startswith("    "):
                folded_lines.append(line.strip())
                continue
            else:
                flush_sub_key()

        if in_string_list:
            match_item = re.match(r"^\s{4,}-\s+(.*)$", line)
            if match_item:
                val = match_item.group(1).strip().strip("'\"")
                list_items.append(val)
                continue
            else:
                flush_sub_key()

        match_top = re.match(r"^([a-zA-Z0-9_-]+):\s*$", line)
        if match_top:
            flush_sub_key()
            current_top_key = match_top.group(1)
            result[current_top_key] = {}
            continue

        match_sub = re.match(r"^\s{2}([a-zA-Z0-9_-]+):\s*(.*)$", line)
        if match_sub and current_top_key is not None:
            flush_sub_key()
            sub_key = match_sub.group(1)
            val = match_sub.group(2).strip()
            current_sub_key = sub_key

            if val in (">-", ">", "|", "|-"):
                in_folded_scalar = True
                folded_lines = []
            elif not val:
                in_string_list = True
                list_items = []
            else:
                if val.startswith(("[", "{")):
                    raise ValueError(f"Inline collections not supported at line {line_no}: {line!r}")
                val = val.strip("'\"")
                result[current_top_key][current_sub_key] = val
                current_sub_key = None
            continue

        raise ValueError(f"Unsupported frontmatter syntax at line {line_no}: {line!r}")

    flush_sub_key()
    return result


def split_frontmatter(content: str) -> Tuple[Dict | None, str]:
    """Split YAML frontmatter from markdown body and return (parsed_frontmatter, body)."""
    if not content.startswith("---"):
        return None, content
    parts = content.split("---", 2)
    if len(parts) < 3:
        return None, content
    raw_yaml = parts[1]
    body = parts[2].lstrip("\r\n")

    data = parse_frontmatter_yaml(raw_yaml)
    return data if data else None, body


def get_skill_names_by_guideline(source_dir: Path | None = None) -> Dict[str, str]:
    """Return a mapping of guideline filename to skill name."""
    source_dir = _resolve_guidelines_dir() if source_dir is None else source_dir
    mapping: Dict[str, str] = {}
    for filename in SOURCE_FILES:
        filepath = source_dir / filename
        if not filepath.exists():
            continue
        try:
            content = filepath.read_text(encoding="utf-8")
            fm, _ = split_frontmatter(content)
            if fm and "skill" in fm and isinstance(fm["skill"], dict):
                skill_name = fm["skill"].get("name")
                if skill_name:
                    mapping[filename] = skill_name
        except Exception:
            pass
    return mapping


def rewrite_markdown_links(
    text: str,
    own_skill_name: str | None = None,
    source_dir: Path | None = None,
    skills_root: Path | None = None,
) -> str:
    """Apply link rewrite rules to text outside of code fences."""
    source_dir = _resolve_guidelines_dir() if source_dir is None else source_dir
    skills_root = _resolve_skills_dir() if skills_root is None else skills_root
    skill_names_by_guideline = get_skill_names_by_guideline(source_dir)

    lines = text.splitlines()
    rewritten_lines: List[str] = []
    in_code_block = False

    for line in lines:
        stripped = line.strip()
        if stripped.startswith("```"):
            in_code_block = not in_code_block
            rewritten_lines.append(line)
            continue

        if in_code_block:
            rewritten_lines.append(line)
            continue

        def replace_link(match: re.Match) -> str:
            link_text = match.group(1)
            raw_target = match.group(2).strip()

            if raw_target.startswith(("http://", "https://", "mailto:", "#")):
                return match.group(0)

            url_part = raw_target.split()[0]
            url_path, sep, fragment = url_part.partition("#")
            fragment_suffix = f"#{fragment}" if sep else ""

            # Plan owns these skills independently of this repository.
            for skill_name in PLAN_OWNED_SKILLS:
                if url_path.endswith(f"/plan/src/plan/skills/{skill_name}/SKILL.md"):
                    return f"the `{skill_name}` skill"

            # Rule 1: Link to a file inside the same skill directory
            if own_skill_name:
                prefix = f"../skills/{own_skill_name}/"
                if url_path.startswith(prefix):
                    rel_target = url_path[len(prefix) :]
                    return f"[{link_text}]({rel_target}{fragment_suffix})"

                own_skill_dir = skills_root / own_skill_name
                try:
                    resolved = (source_dir / url_path).resolve()
                    if own_skill_dir.exists() and resolved.is_relative_to(own_skill_dir.resolve()):
                        rel_target = resolved.relative_to(own_skill_dir.resolve()).as_posix()
                        return f"[{link_text}]({rel_target}{fragment_suffix})"
                except (ValueError, OSError):
                    pass

            # Rule 2: Link to sibling guideline defining a skill
            target_filename = Path(url_path).name
            is_sibling = False
            if url_path in skill_names_by_guideline or (url_path.startswith("./") and url_path[2:] in skill_names_by_guideline):
                is_sibling = True
            elif not url_path.startswith("../") and "/" not in url_path:
                is_sibling = True
            else:
                try:
                    resolved = (source_dir / url_path).resolve()
                    if resolved.parent == source_dir.resolve() and resolved.suffix == ".md":
                        is_sibling = True
                except (ValueError, OSError):
                    pass

            if is_sibling and target_filename in skill_names_by_guideline:
                target_skill = skill_names_by_guideline[target_filename]
                return f"the `{target_skill}` skill"

            # Rule 3: Link to sibling guideline WITHOUT a skill
            if is_sibling and (target_filename in SOURCE_FILES or target_filename.endswith(".md")):
                return link_text

            # Rule 4: Link to any other repository file
            repo_rel: str | None = None
            repo_root = _resolve_repo_root()
            try:
                resolved = (source_dir / url_path).resolve()
                if resolved.is_relative_to(repo_root.resolve()):
                    repo_rel = resolved.relative_to(repo_root.resolve()).as_posix()
            except (ValueError, OSError):
                pass

            if repo_rel is None:
                norm = os.path.normpath(os.path.join(source_dir.name, url_path)).replace("\\", "/")
                if not norm.startswith("../"):
                    repo_rel = norm
                elif url_path.startswith("../"):
                    norm_sub = os.path.normpath(url_path[3:]).replace("\\", "/")
                    if not norm_sub.startswith("../"):
                        repo_rel = norm_sub

            if repo_rel:
                return f"[{link_text}](https://github.com/gpellicciotta/dev-guidelines/blob/main/{repo_rel}{fragment_suffix})"

            return match.group(0)

        # Protect inline code spans from link replacement
        parts = re.split(r"(`+[^`]+`+)", line)
        for idx_p, part in enumerate(parts):
            if not part.startswith("`"):
                parts[idx_p] = re.sub(r"\[([^\]]+)\]\(([^)]+)\)", replace_link, part)
        rewritten_line = "".join(parts)
        rewritten_lines.append(rewritten_line)

    return "\n".join(rewritten_lines)


def strip_empty_headings(lines: List[str]) -> List[str]:
    """Remove headings that contain no content before EOF or next heading of <= level."""
    changed = True
    result = list(lines)
    while changed:
        changed = False
        new_lines: List[str] = []
        i = 0
        while i < len(result):
            line = result[i]
            stripped = line.strip()
            m = re.match(r"^(#{1,6})\s+", stripped)
            if m:
                level = len(m.group(1))
                has_content = False
                j = i + 1
                while j < len(result):
                    next_line = result[j].strip()
                    if not next_line:
                        j += 1
                        continue
                    next_m = re.match(r"^(#{1,6})\s+", next_line)
                    if next_m:
                        next_level = len(next_m.group(1))
                        if next_level <= level:
                            break
                        else:
                            has_content = True
                            break
                    else:
                        has_content = True
                        break
                if not has_content:
                    changed = True
                    i += 1
                    continue
            new_lines.append(line)
            i += 1
        result = new_lines
    return result


def clean_markdown_lines(lines: List[str]) -> List[str]:
    """Clean up multiple consecutive empty lines and blank lines after headings below H1."""
    cleaned: List[str] = []
    for line in lines:
        if not line.strip():
            if not cleaned or not cleaned[-1].strip():
                continue
            # Strip blank line after subheadings (H2-H6) per MD015
            if cleaned[-1].lstrip().startswith(("##", "###", "####", "#####", "######")):
                continue
        cleaned.append(line)
    return cleaned


def format_skill_frontmatter(name: str, description: str) -> str:
    """Format standard YAML frontmatter for an agent skill."""
    desc_clean = " ".join(description.split())
    words = desc_clean.split()
    lines: List[str] = []
    current = "  "
    for word in words:
        if len(current) + len(word) + 1 > 82:
            lines.append(current)
            current = "  " + word
        else:
            current = current + (" " if current.strip() else "") + word
    if current.strip():
        lines.append(current)
    desc_block = "\n".join(lines)
    return f"---\nname: {name}\ndescription: >-\n{desc_block}\n---\n\n"


def build_skill_content(
    name: str,
    description: str,
    body: str,
    source_dir: Path | None = None,
    skills_root: Path | None = None,
) -> str:
    """Construct SKILL.md content from frontmatter metadata and guideline body."""
    source_dir = _resolve_guidelines_dir() if source_dir is None else source_dir
    skills_root = _resolve_skills_dir() if skills_root is None else skills_root
    collected_lines: List[str] = []
    for line in body.splitlines():
        stripped = line.lstrip()
        # Omit all blockquote lines (rationale, templates, background notes)
        if stripped.startswith(">"):
            continue

        collected_lines.append(line)

    rewritten_body = rewrite_markdown_links(
        "\n".join(collected_lines),
        own_skill_name=name,
        source_dir=source_dir,
        skills_root=skills_root,
    )

    cleaned = clean_markdown_lines(rewritten_body.splitlines())
    body_text = "\n".join(cleaned).strip() + "\n"
    frontmatter = format_skill_frontmatter(name, description)
    return frontmatter + body_text


def build_skills(
    source_dir: Path | None = None,
    skills_root: Path | None = None,
) -> Dict[str, str]:
    """Extract all guidelines configured as skills and return mapping of skill_name -> content."""
    source_dir = _resolve_guidelines_dir() if source_dir is None else source_dir
    skills_root = _resolve_skills_dir() if skills_root is None else skills_root
    skills: Dict[str, str] = {}
    for filename in SOURCE_FILES:
        filepath = source_dir / filename
        if not filepath.exists():
            continue
        content = filepath.read_text(encoding="utf-8")
        fm, body = split_frontmatter(content)
        if fm and "skill" in fm and isinstance(fm["skill"], dict):
            skill_meta = fm["skill"]
            name = skill_meta.get("name")
            desc = skill_meta.get("description", "")
            if name and name not in PLAN_OWNED_SKILLS:
                skills[name] = build_skill_content(
                    name,
                    desc,
                    body,
                    source_dir=source_dir,
                    skills_root=skills_root,
                )
    return skills


def build_digest(
    source_dir: Path | None = None,
    skills_root: Path | None = None,
) -> str:
    """Extract directive lines from core (non-skill) source guideline files and assemble the digest."""
    default_guidelines_dir = _resolve_guidelines_dir()
    source_dir = default_guidelines_dir if source_dir is None else source_dir
    skills_root = _resolve_skills_dir() if skills_root is None else skills_root
    collected_lines: List[str] = []

    for filename in SOURCE_FILES:
        filepath = source_dir / filename
        if not filepath.exists():
            if source_dir == default_guidelines_dir:
                raise FileNotFoundError(f"Source guideline file not found: {filepath}")
            continue

        content = filepath.read_text(encoding="utf-8")
        fm, body = split_frontmatter(content)

        # Skip files that are exported as skills
        if fm and "skill" in fm and isinstance(fm["skill"], dict):
            continue

        for line in body.splitlines():
            stripped = line.lstrip()
            # Omit all blockquote lines (rationale, templates, background notes)
            if stripped.startswith(">"):
                continue

            # Bump Markdown heading levels by 1 (# -> ##, ## -> ###, etc.)
            if stripped.startswith("#"):
                indent = len(line) - len(stripped)
                line = line[:indent] + "#" + stripped

            collected_lines.append(line)

        collected_lines.append("")

    rewritten_digest = rewrite_markdown_links(
        "\n".join(collected_lines),
        own_skill_name=None,
        source_dir=source_dir,
        skills_root=skills_root,
    )

    without_empty_headings = strip_empty_headings(rewritten_digest.splitlines())
    cleaned = clean_markdown_lines(without_empty_headings)
    return "\n".join(cleaned).strip() + "\n"


def find_budget_violations(digest_content: str, max_words: int = 20) -> List[Tuple[int, int, str]]:
    """Find directive sentences exceeding the word limit."""
    violations: List[Tuple[int, int, str]] = []
    lines = digest_content.splitlines()
    in_code = False
    in_fm = False

    for idx, line in enumerate(lines, 1):
        stripped = line.strip()
        if idx == 1 and stripped == "---":
            in_fm = True
            continue
        if in_fm:
            if stripped == "---":
                in_fm = False
            continue
        if stripped.startswith("```"):
            in_code = not in_code
            continue
        if in_code:
            continue
        if not stripped or stripped.startswith("#") or stripped.startswith("|"):
            continue

        match = re.match(r"^\s*-\s+(.*)$", line)
        text = match.group(1).strip() if match else stripped

        # Split on sentence boundaries (. ! ?)
        sentences = re.split(r"(?<=[.!?])\s+", text)
        for sentence in sentences:
            clean = sentence.strip()
            if not clean or clean.startswith("*(Currently"):
                continue

            word_count = len(clean.split())
            if word_count > max_words:
                violations.append((idx, word_count, clean))

    return violations


def check_size_budget(digest_content: str, max_bytes: int = MAX_DIGEST_BYTES) -> Tuple[bool, int, int]:
    """Check if the UTF-8 encoded digest exceeds the hard byte budget.

    Returns (is_valid, byte_count, max_bytes).
    """
    byte_count = len(digest_content.encode("utf-8"))
    return (byte_count <= max_bytes, byte_count, max_bytes)


def display_path(path: Path) -> str:
    """Return path relative to the repository root when possible, using forward slashes."""
    try:
        return path.resolve().relative_to(_resolve_repo_root().resolve()).as_posix()
    except ValueError:
        return path.as_posix()


def format_stale_report(path: Path, current: str, expected: str, max_lines: int = MAX_DIFF_LINES) -> str:
    """Return a multi-line out-of-date message followed by a truncated unified diff."""
    diff = list(
        difflib.unified_diff(
            current.splitlines(),
            expected.splitlines(),
            fromfile=display_path(path),
            tofile="expected",
            lineterm="",
        )
    )
    lines = [f"{display_path(path)} is out of date:", *diff[:max_lines]]
    if len(diff) > max_lines:
        lines.append(f"... and {len(diff) - max_lines} more diff lines.")
    return "\n".join(lines)


def format_violations(violations: List[Tuple[int, int, str]], scope: str) -> str:
    """Return a multi-line message listing sentence word budget violations."""
    lines = [f"Found {len(violations)} sentence word budget violation(s) in {scope}:"]
    lines.extend(f"Line {line_num} ({word_count} words): {sentence}" for line_num, word_count, sentence in violations)
    return "\n".join(lines)


def action_generate(
    max_bytes: int = MAX_DIGEST_BYTES,
    source_dir: Path | None = None,
    skills_root: Path | None = None,
    logger: CliLogger | None = None,
) -> int:
    """Generate guidelines/agent-digest.md and all derived skills."""
    source_dir = _resolve_guidelines_dir() if source_dir is None else source_dir
    skills_root = _resolve_skills_dir() if skills_root is None else skills_root
    logger = logger or CliLogger()
    logger.debug_msg(f"Reading guidelines from {display_path(source_dir)} and writing skills to {display_path(skills_root)}.")
    skills = build_skills(source_dir=source_dir, skills_root=skills_root)
    for skill_name, skill_content in sorted(skills.items()):
        skill_dir = skills_root / skill_name
        skill_dir.mkdir(parents=True, exist_ok=True)
        skill_path = skill_dir / "SKILL.md"
        skill_path.write_text(skill_content, encoding="utf-8", newline="\n")
        logger.info(f"Generated {display_path(skill_path)} ({len(skill_content.splitlines())} lines).")

    digest_text = build_digest(source_dir=source_dir, skills_root=skills_root)
    digest_path = source_dir / "agent-digest.md"
    digest_path.write_text(digest_text, encoding="utf-8", newline="\n")
    is_valid, byte_count, limit = check_size_budget(digest_text, max_bytes)
    logger.info(f"Generated {display_path(digest_path)} ({len(digest_text.splitlines())} lines, {byte_count} bytes).")
    if not is_valid:
        logger.error(f"Digest size ({byte_count} bytes) exceeds the hard budget limit ({limit} bytes).")
        return 1
    return 0


def action_check(
    max_bytes: int = MAX_DIGEST_BYTES,
    source_dir: Path | None = None,
    skills_root: Path | None = None,
    logger: CliLogger | None = None,
) -> int:
    """Check if guidelines/agent-digest.md and all derived skills are up-to-date and within budget."""
    source_dir = _resolve_guidelines_dir() if source_dir is None else source_dir
    skills_root = _resolve_skills_dir() if skills_root is None else skills_root
    logger = logger or CliLogger()
    has_error = False

    # Check skills
    skills = build_skills(source_dir=source_dir, skills_root=skills_root)
    logger.debug_msg(f"Comparing {len(skills)} derived skill(s) under {display_path(skills_root)}.")
    stale_skills = 0
    for skill_name, expected_skill in sorted(skills.items()):
        skill_path = skills_root / skill_name / "SKILL.md"
        if not skill_path.exists():
            logger.error(f"{display_path(skill_path)} does not exist.")
            stale_skills += 1
            continue
        current_skill = skill_path.read_text(encoding="utf-8")
        if current_skill != expected_skill:
            logger.error(format_stale_report(skill_path, current_skill, expected_skill, max_lines=30))
            stale_skills += 1
        elif logger.verbose:
            logger.info(f"{display_path(skill_path)} is up to date.")
    if stale_skills:
        has_error = True
    else:
        logger.info(f"All {len(skills)} derived skill(s) are up to date.")

    # Check digest
    digest_path = source_dir / "agent-digest.md"
    if not digest_path.exists():
        logger.error(f"{display_path(digest_path)} does not exist.")
        return 1

    expected = build_digest(source_dir=source_dir, skills_root=skills_root)
    current = digest_path.read_text(encoding="utf-8")

    is_valid, byte_count, limit = check_size_budget(current, max_bytes)
    if not is_valid:
        logger.error(f"{display_path(digest_path)} ({byte_count} bytes) exceeds the hard budget limit ({limit} bytes).")
        has_error = True

    if current == expected:
        logger.info(f"{display_path(digest_path)} is up to date and within budget ({byte_count} bytes).")
    else:
        logger.error(format_stale_report(digest_path, current, expected))
        has_error = True

    return 1 if has_error else 0


def action_validate(
    max_words: int = 20,
    max_bytes: int = MAX_DIGEST_BYTES,
    source_dir: Path | None = None,
    skills_root: Path | None = None,
    logger: CliLogger | None = None,
) -> int:
    """Validate word, size budgets, frontmatter, and link integrity across digest and derived skills."""
    source_dir = _resolve_guidelines_dir() if source_dir is None else source_dir
    skills_root = _resolve_skills_dir() if skills_root is None else skills_root
    logger = logger or CliLogger()
    logger.debug_msg(
        f"Validating {display_path(source_dir)} and {display_path(skills_root)} ({max_words} words, {max_bytes} bytes)."
    )
    has_error = False

    # 1. Frontmatter unknown keys validation across all guidelines in source_dir
    if source_dir.exists():
        for filepath in sorted(source_dir.glob("*.md")):
            if filepath.name == "agent-digest.md":
                continue
            try:
                content = filepath.read_text(encoding="utf-8")
                fm, _ = split_frontmatter(content)
                if fm and "skill" in fm and isinstance(fm["skill"], dict):
                    allowed_keys = {"name", "description"}
                    unknown_keys = set(fm["skill"].keys()) - allowed_keys
                    if unknown_keys:
                        logger.error(f"Unknown key(s) under 'skill:' in {filepath.name}: {sorted(unknown_keys)}")
                        has_error = True
            except Exception as e:
                logger.error(f"Error parsing frontmatter in {filepath.name}: {e}")
                has_error = True

    # 2. Skill coverage in general-guidelines.md
    gen_path = source_dir / "general-guidelines.md"
    if gen_path.exists():
        gen_content = gen_path.read_text(encoding="utf-8")
        for filepath in sorted(source_dir.glob("*.md")):
            if filepath.name == "agent-digest.md" or filepath.name == "general-guidelines.md":
                continue
            try:
                content = filepath.read_text(encoding="utf-8")
                fm, _ = split_frontmatter(content)
                if fm and "skill" in fm and isinstance(fm["skill"], dict):
                    if f"({filepath.name})" not in gen_content and f"({filepath.name}#" not in gen_content:
                        logger.error(f"Skill guideline '{filepath.name}' is not linked from general-guidelines.md")
                        has_error = True
            except Exception:
                pass

    # 3. Orphan reference files and escaping links under skills_root
    if skills_root.exists():
        for skill_dir in sorted(skills_root.iterdir()):
            if not skill_dir.is_dir():
                continue
            skill_file = skill_dir / "SKILL.md"
            skill_text = skill_file.read_text(encoding="utf-8") if skill_file.exists() else ""
            for subfile in sorted(skill_dir.rglob("*")):
                if subfile.is_file() and subfile.name != "SKILL.md":
                    rel_subfile = subfile.relative_to(skill_dir).as_posix()
                    if f"]({rel_subfile})" not in skill_text and f"]({rel_subfile}#" not in skill_text:
                        logger.error(
                            f"Orphan reference file '{rel_subfile}' in skill '{skill_dir.name}' is not linked from SKILL.md"
                        )
                        has_error = True

            # Check escaping links in SKILL.md on disk
            in_code = False
            for line in skill_text.splitlines():
                if line.strip().startswith("```"):
                    in_code = not in_code
                    continue
                if in_code:
                    continue
                for m in re.finditer(r"\[([^\]]+)\]\(([^)]+)\)", line):
                    target = m.group(2).strip().split()[0]
                    if not target.startswith(("http://", "https://", "mailto:", "#")):
                        norm_target = os.path.normpath(target).replace("\\", "/")
                        if norm_target.startswith("../") or target.startswith(("/", "\\")):
                            logger.error(f"Escaping link in skill '{skill_dir.name}': {target}")
                            has_error = True

    # 4. Digest validation (size, sentence budget, relative links)
    digest_text = build_digest(source_dir=source_dir, skills_root=skills_root)
    digest_violations = find_budget_violations(digest_text, max_words=max_words)
    is_valid_size, byte_count, limit = check_size_budget(digest_text, max_bytes)

    if not is_valid_size:
        logger.error(f"Digest size ({byte_count} bytes) exceeds the hard budget limit ({limit} bytes).")
        has_error = True

    if digest_violations:
        logger.error(format_violations(digest_violations, "digest"))
        has_error = True

    # Check for relative links in digest
    in_code = False
    for line in digest_text.splitlines():
        if line.strip().startswith("```"):
            in_code = not in_code
            continue
        if in_code:
            continue
        for m in re.finditer(r"\[([^\]]+)\]\(([^)]+)\)", line):
            target = m.group(2).strip().split()[0]
            if not target.startswith(("http://", "https://", "mailto:", "#")):
                logger.error(f"Relative markdown link in digest: {target}")
                has_error = True

    # 5. Skills validation (sentence budget, escaping links)
    skills = build_skills(source_dir=source_dir, skills_root=skills_root)
    for skill_name, skill_content in sorted(skills.items()):
        violations = find_budget_violations(skill_content, max_words=max_words)
        if violations:
            logger.error(format_violations(violations, f"skill {skill_name}"))
            has_error = True

        # Check for escaping relative links in skill
        in_code = False
        for line in skill_content.splitlines():
            if line.strip().startswith("```"):
                in_code = not in_code
                continue
            if in_code:
                continue
            for m in re.finditer(r"\[([^\]]+)\]\(([^)]+)\)", line):
                target = m.group(2).strip().split()[0]
                if not target.startswith(("http://", "https://", "mailto:", "#")):
                    if target.startswith("../") or target.startswith("/") or target.startswith("\\"):
                        logger.error(f"Escaping link in skill '{skill_name}': {target}")
                        has_error = True

    if not has_error:
        logger.info(
            f"All directive sentences satisfy the {max_words}-word budget and digest size is within {limit} bytes ({byte_count} bytes)."
        )
        return 0

    return 1


class DigestHarness(ToolHarness):
    """Tool harness adding the digest size budget to the startup configuration banner."""

    max_bytes: int = MAX_DIGEST_BYTES

    def create_logger(self, args: argparse.Namespace) -> CliLogger:
        """Record the parsed size budget for the startup banner, then build the logger."""
        self.max_bytes = args.max_bytes
        return super().create_logger(args)

    def log_startup(self, logger: CliLogger, action: str, extra: dict | None = None) -> None:
        """Emit the standard startup banner including the size budget."""
        config = {"Max bytes": self.max_bytes, **(extra or {})}
        super().log_startup(logger, action, extra=config)


def build_harness() -> DigestHarness:
    """Construct the CLI harness with the generate, check, and validate actions."""
    harness = DigestHarness(
        name=TOOL_NAME,
        description="Deterministic generator for guidelines/agent-digest.md and derived skills.",
        version=TOOL_VERSION,
        exit_codes={
            0: "success (check: up to date and within budget; validate: no budget violations)",
            1: "check or validation failed, size budget exceeded, or runtime error",
            2: "invalid command-line arguments",
        },
        examples=[
            f"{TOOL_NAME} generate",
            f"{TOOL_NAME} check --verbose",
            f"{TOOL_NAME} validate --max-bytes 20480 --log-file logs/digest.log",
        ],
    )
    harness.add_global_argument(
        "--max-bytes",
        type=int,
        default=MAX_DIGEST_BYTES,
        help=f"maximum digest size budget in bytes (default: {MAX_DIGEST_BYTES})",
    )
    harness.add_action(
        "generate",
        "extract derived skills and assemble guidelines/agent-digest.md",
        handler=lambda args, logger: action_generate(max_bytes=args.max_bytes, logger=logger),
        detail="Extracts derived skills from guidelines defining a 'skill:' frontmatter block\n"
        "and compiles guidelines/agent-digest.md within the hard size budget.",
    )
    harness.add_action(
        "check",
        "check whether skills and guidelines/agent-digest.md are up to date and within budget",
        handler=lambda args, logger: action_check(max_bytes=args.max_bytes, logger=logger),
        detail="Compares derived skills and guidelines/agent-digest.md against freshly built content.\n"
        "Prints a truncated diff for each stale file; --verbose lists every up-to-date skill.",
    )
    harness.add_action(
        "validate",
        "validate word and size budgets across the digest and derived skills",
        handler=lambda args, logger: action_validate(max_bytes=args.max_bytes, logger=logger),
        detail="Validates 20-word directive sentence budgets, the digest size budget,\n"
        "skill frontmatter keys, skill coverage, orphan reference files, and link constraints.",
    )
    return harness


def main(argv: List[str] | None = None) -> int:
    """Run the command line and return its exit code."""
    return build_harness().run(argv)


if __name__ == "__main__":
    sys.exit(main())
