#!/usr/bin/env python3
"""
Deterministically generate an agent digest Markdown file from input Markdown files and directories,
and extract modular agent skills (<skills-dir>/<name>/SKILL.md) from files that define a 'skill:'
YAML front-matter mapping. All blockquote ('>') lines containing rationale, background, and
templates are filtered out.
"""

from __future__ import annotations

import argparse
import difflib
import os
import re
import subprocess
import sys
from pathlib import Path
from typing import Dict, List, Sequence, Set, Tuple

from support_python.cli import PROJECT_VERSION, ToolHarness
from support_python.git import get_current_branch, get_repo_root, run_git_command
from support_python.logging import CliLogger
from support_python.tools.agent_files import find_project_root

TOOL_NAME = "agent-digest"
TOOL_VERSION = PROJECT_VERSION

DEFAULT_DIGEST_PATH = Path("agent-digest.md")
DEFAULT_SKILLS_DIR = Path("agent-skills")
DEFAULT_MAX_WORDS = 20
MAX_DIGEST_BYTES = 20 * 1024  # 20 KiB (20,480 bytes) hard size budget
MAX_DIFF_LINES = 50


class PathArgumentError(ValueError):
    """Raised when a CLI path argument is missing, nonexistent, or not a Markdown file."""


class FrontmatterError(ValueError):
    """Raised when a Markdown file has invalid front-matter syntax or a non-integer index."""


def parse_frontmatter_yaml(raw_yaml: str) -> Dict:
    """Strict, dependency-free parser for the supported YAML front-matter subset.

    Supported subset:
    - top-level scalar values (e.g. 'index: 2')
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
            flush_sub_key()

        if in_string_list:
            match_item = re.match(r"^\s{4,}-\s+(.*)$", line)
            if match_item:
                val = match_item.group(1).strip().strip("'\"")
                list_items.append(val)
                continue
            flush_sub_key()

        match_top = re.match(r"^([a-zA-Z0-9_-]+):\s*(.*)$", line)
        if match_top:
            flush_sub_key()
            top_key = match_top.group(1)
            raw_val = match_top.group(2).strip()
            if not raw_val:
                current_top_key = top_key
                result[current_top_key] = {}
            else:
                current_top_key = None
                if raw_val.startswith(("[", "{")):
                    raise ValueError(f"Inline collections not supported at line {line_no}: {line!r}")
                if re.match(r"^-?\d+$", raw_val):
                    result[top_key] = int(raw_val)
                else:
                    result[top_key] = raw_val.strip("'\"")
            continue

        match_sub = re.match(r"^\s{2}([a-zA-Z0-9_-]+):\s*(.*)$", line)
        if match_sub and current_top_key is not None and isinstance(result.get(current_top_key), dict):
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
    """Split YAML front-matter from Markdown body and return (parsed_frontmatter, body)."""
    if not content.startswith("---"):
        return None, content
    parts = content.split("---", 2)
    if len(parts) < 3:
        return None, content
    raw_yaml = parts[1]
    body = parts[2].lstrip("\r\n")

    data = parse_frontmatter_yaml(raw_yaml)
    return data if data else None, body


def collect_input_files(
    paths: Sequence[Path | str],
    digest_path: Path | str = DEFAULT_DIGEST_PATH,
    skills_dir: Path | str = DEFAULT_SKILLS_DIR,
) -> List[Path]:
    """Collect, deduplicate, filter, and order input Markdown files from CLI path arguments.

    Raises:
        PathArgumentError: When no paths are supplied, a path does not exist, or a file path does not end in '.md'.
        FrontmatterError: When front-matter cannot be parsed or 'index' is not an integer.
    """
    if not paths:
        raise PathArgumentError("At least one PATH argument is required.")

    digest_resolved = Path(digest_path).resolve()
    skills_resolved = Path(skills_dir).resolve()
    candidates: List[Path] = []
    seen: Set[Path] = set()

    def _add_candidate(resolved_file: Path) -> None:
        if resolved_file == digest_resolved or resolved_file.is_relative_to(skills_resolved):
            return
        if resolved_file not in seen:
            seen.add(resolved_file)
            candidates.append(resolved_file)

    for raw_path in paths:
        path = Path(raw_path)
        if not path.exists():
            raise PathArgumentError(f"Path does not exist: {path}")
        if path.is_file():
            if path.suffix.lower() != ".md":
                raise PathArgumentError(f"Path is not a Markdown (.md) file: {path}")
            _add_candidate(path.resolve())
        elif path.is_dir():
            if path.name not in (".", "..") and path.name.startswith("."):
                continue
            target_dir = path.resolve()
            rel_files: List[Tuple[str, Path]] = []
            for root, dirs, files in os.walk(target_dir):
                dirs[:] = sorted(d for d in dirs if not d.startswith("."))
                for fname in files:
                    if fname.lower().endswith(".md"):
                        full_path = (Path(root) / fname).resolve()
                        rel_posix = full_path.relative_to(target_dir).as_posix()
                        rel_files.append((rel_posix, full_path))
            rel_files.sort(key=lambda item: item[0])
            for _, resolved_file in rel_files:
                _add_candidate(resolved_file)

    indexed: List[Tuple[int, int, Path]] = []
    unindexed: List[Path] = []
    for pos, filepath in enumerate(candidates):
        content = filepath.read_text(encoding="utf-8")
        try:
            fm, _ = split_frontmatter(content)
        except ValueError as exc:
            raise FrontmatterError(f"Invalid front-matter in {filepath.name}: {exc}") from exc
        if fm and "index" in fm:
            idx_val = fm["index"]
            if isinstance(idx_val, bool) or not isinstance(idx_val, int):
                raise FrontmatterError(f"Non-integer front-matter 'index' in {filepath.name}: {idx_val!r}")
            indexed.append((idx_val, pos, filepath))
        else:
            unindexed.append(filepath)

    indexed.sort(key=lambda item: (item[0], item[1]))
    return [filepath for _, _, filepath in indexed] + unindexed


def derive_link_base(repo_root: Path) -> str | None:
    """Derive the GitHub blob base URL from the repository's origin remote and current branch."""
    top = get_repo_root(repo_root)
    if top is None or top.resolve() != repo_root.resolve():
        return None
    try:
        res = run_git_command(repo_root, "remote", "get-url", "origin")
        remote_url = res.stdout.strip()
    except (OSError, subprocess.SubprocessError):
        return None
    if not remote_url:
        return None

    match = re.match(
        r"^(?:https?://github\.com/|ssh://git@github\.com/|git@github\.com:)([^/\s]+)/([^/\s]+?)(?:\.git)?/?$",
        remote_url,
    )
    if not match:
        return None
    owner, repo = match.group(1), match.group(2)

    branch = get_current_branch(repo_root)
    if not branch or branch == "(detached)":
        return None
    return f"https://github.com/{owner}/{repo}/blob/{branch}/"


def _classify_inputs(input_files: Sequence[Path]) -> Tuple[Dict[Path, str], Dict[str, str], Set[Path]]:
    """Classify input files into skill mappings (by resolved Path and by filename) and digest files."""
    skill_by_path: Dict[Path, str] = {}
    skill_by_name: Dict[str, str] = {}
    digest_files: Set[Path] = set()
    for filepath in input_files:
        resolved = filepath.resolve()
        try:
            content = resolved.read_text(encoding="utf-8")
            fm, _ = split_frontmatter(content)
        except Exception:
            fm = None
        if fm and "skill" in fm and isinstance(fm["skill"], dict):
            skill_name = fm["skill"].get("name")
            if skill_name:
                skill_by_path[resolved] = skill_name
                skill_by_name[resolved.name] = skill_name
                continue
        digest_files.add(resolved)
    return skill_by_path, skill_by_name, digest_files


def rewrite_markdown_links(
    text: str,
    own_skill_name: str | None = None,
    source_dir: Path | None = None,
    skills_root: Path | None = None,
    skill_names_by_path: Dict[Path, str] | None = None,
    skill_names_by_name: Dict[str, str] | None = None,
    digest_files: Set[Path] | None = None,
    link_base: str | None = None,
    repo_root: Path | None = None,
) -> str:
    """Apply link rewrite rules to Markdown text outside of code fences."""
    base_dir = (source_dir or Path.cwd()).resolve()
    skills_dir = (skills_root or DEFAULT_SKILLS_DIR).resolve()
    resolved_repo_root = (repo_root or find_project_root(base_dir)).resolve()
    effective_link_base = link_base if link_base is not None else derive_link_base(resolved_repo_root)

    if skill_names_by_path is None or skill_names_by_name is None or digest_files is None:
        md_files = sorted(base_dir.glob("*.md")) if base_dir.is_dir() else []
        s_path, s_name, d_files = _classify_inputs(md_files)
        skill_names_by_path = skill_names_by_path if skill_names_by_path is not None else s_path
        skill_names_by_name = skill_names_by_name if skill_names_by_name is not None else s_name
        digest_files = digest_files if digest_files is not None else d_files

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
            url_part = raw_target.split()[0]
            url_path, sep, fragment = url_part.partition("#")
            fragment_suffix = f"#{fragment}" if sep else ""

            # Rewrite any link whose target ends in /skills/<name>/SKILL.md (relative or GitHub URL)
            skill_ref = re.search(r"(?:^|/)skills/([^/]+)/SKILL\.md$", url_path)
            if skill_ref and (
                not raw_target.startswith(("http://", "https://", "mailto:", "#"))
                or raw_target.startswith(("https://github.com/", "http://github.com/"))
            ):
                return f"the `{skill_ref.group(1)}` skill"

            if raw_target.startswith(("http://", "https://", "mailto:", "#")):
                return match.group(0)

            # Rule 1: Link to a file inside the same skill directory
            if own_skill_name:
                for prefix in (f"../skills/{own_skill_name}/", f"../{skills_dir.name}/{own_skill_name}/"):
                    if url_path.startswith(prefix):
                        rel_target = url_path[len(prefix) :]
                        return f"[{link_text}]({rel_target}{fragment_suffix})"

                own_skill_dir = skills_dir / own_skill_name
                try:
                    resolved = (base_dir / url_path).resolve()
                    if own_skill_dir.exists() and resolved.is_relative_to(own_skill_dir.resolve()):
                        rel_target = resolved.relative_to(own_skill_dir.resolve()).as_posix()
                        return f"[{link_text}]({rel_target}{fragment_suffix})"
                except (ValueError, OSError):
                    pass

            # Rule 2 & 3: Link to another input guideline (with or without a skill)
            target_filename = Path(url_path).name
            resolved_target: Path | None = None
            try:
                resolved_target = (base_dir / url_path).resolve()
            except (ValueError, OSError):
                resolved_target = None

            is_sibling = False
            if url_path in skill_names_by_name or (url_path.startswith("./") and url_path[2:] in skill_names_by_name):
                is_sibling = True
            elif not url_path.startswith("../") and "/" not in url_path:
                is_sibling = True
            elif resolved_target is not None and resolved_target.parent == base_dir and resolved_target.suffix == ".md":
                is_sibling = True

            if resolved_target is not None and resolved_target in skill_names_by_path:
                return f"the `{skill_names_by_path[resolved_target]}` skill"
            if is_sibling and target_filename in skill_names_by_name:
                return f"the `{skill_names_by_name[target_filename]}` skill"

            if (resolved_target is not None and resolved_target in digest_files) or (
                is_sibling and target_filename.endswith(".md")
            ):
                return link_text

            # Rule 4: Link to any other repository file
            repo_rel: str | None = None
            if resolved_target is not None:
                try:
                    if resolved_target.is_relative_to(resolved_repo_root):
                        repo_rel = resolved_target.relative_to(resolved_repo_root).as_posix()
                except ValueError:
                    pass

            if repo_rel is None:
                norm = os.path.normpath(os.path.join(base_dir.name, url_path)).replace("\\", "/")
                if not norm.startswith("../"):
                    repo_rel = norm
                elif url_path.startswith("../"):
                    norm_sub = os.path.normpath(url_path[3:]).replace("\\", "/")
                    if not norm_sub.startswith("../"):
                        repo_rel = norm_sub

            if repo_rel and effective_link_base:
                return f"[{link_text}]({effective_link_base.rstrip('/')}/{repo_rel}{fragment_suffix})"

            return match.group(0)

        parts = re.split(r"(`+[^`]+`+)", line)
        for idx_p, part in enumerate(parts):
            if not part.startswith("`"):
                parts[idx_p] = re.sub(r"\[([^\]]+)\]\(([^)]+)\)", replace_link, part)
        rewritten_lines.append("".join(parts))

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
                        has_content = True
                        break
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
    skill_names_by_path: Dict[Path, str] | None = None,
    skill_names_by_name: Dict[str, str] | None = None,
    digest_files: Set[Path] | None = None,
    link_base: str | None = None,
    repo_root: Path | None = None,
) -> str:
    """Construct SKILL.md content from frontmatter metadata and guideline body."""
    collected_lines: List[str] = []
    for line in body.splitlines():
        if line.lstrip().startswith(">"):
            continue
        collected_lines.append(line)

    rewritten_body = rewrite_markdown_links(
        "\n".join(collected_lines),
        own_skill_name=name,
        source_dir=source_dir,
        skills_root=skills_root,
        skill_names_by_path=skill_names_by_path,
        skill_names_by_name=skill_names_by_name,
        digest_files=digest_files,
        link_base=link_base,
        repo_root=repo_root,
    )

    cleaned = clean_markdown_lines(rewritten_body.splitlines())
    body_text = "\n".join(cleaned).strip() + "\n"
    frontmatter = format_skill_frontmatter(name, description)
    return frontmatter + body_text


def build_skills(
    paths: Sequence[Path | str],
    digest_path: Path | str = DEFAULT_DIGEST_PATH,
    skills_dir: Path | str = DEFAULT_SKILLS_DIR,
    link_base: str | None = None,
    repo_root: Path | None = None,
) -> Dict[str, str]:
    """Extract all input files configured as skills and return a mapping of skill_name -> content."""
    input_files = collect_input_files(paths, digest_path=digest_path, skills_dir=skills_dir)
    resolved_repo_root = (repo_root or find_project_root(Path(paths[0]))).resolve()
    effective_link_base = link_base if link_base is not None else (derive_link_base(resolved_repo_root) or "")
    skills_root = Path(skills_dir)
    skill_by_path, skill_by_name, digest_files = _classify_inputs(input_files)

    skills: Dict[str, str] = {}
    for filepath in input_files:
        content = filepath.read_text(encoding="utf-8")
        fm, body = split_frontmatter(content)
        if fm and "skill" in fm and isinstance(fm["skill"], dict):
            skill_meta = fm["skill"]
            name = skill_meta.get("name")
            desc = skill_meta.get("description", "")
            if name:
                skills[name] = build_skill_content(
                    name,
                    desc,
                    body,
                    source_dir=filepath.parent,
                    skills_root=skills_root,
                    skill_names_by_path=skill_by_path,
                    skill_names_by_name=skill_by_name,
                    digest_files=digest_files,
                    link_base=effective_link_base,
                    repo_root=resolved_repo_root,
                )
    return skills


def build_digest(
    paths: Sequence[Path | str],
    digest_path: Path | str = DEFAULT_DIGEST_PATH,
    skills_dir: Path | str = DEFAULT_SKILLS_DIR,
    link_base: str | None = None,
    repo_root: Path | None = None,
) -> str:
    """Extract directive lines from non-skill input Markdown files and assemble the digest."""
    input_files = collect_input_files(paths, digest_path=digest_path, skills_dir=skills_dir)
    resolved_repo_root = (repo_root or find_project_root(Path(paths[0]))).resolve()
    effective_link_base = link_base if link_base is not None else (derive_link_base(resolved_repo_root) or "")
    skills_root = Path(skills_dir)
    skill_by_path, skill_by_name, digest_files = _classify_inputs(input_files)

    rewritten_chunks: List[str] = []
    for filepath in input_files:
        content = filepath.read_text(encoding="utf-8")
        fm, body = split_frontmatter(content)
        if fm and "skill" in fm and isinstance(fm["skill"], dict):
            continue

        file_lines: List[str] = []
        for line in body.splitlines():
            stripped = line.lstrip()
            if stripped.startswith(">"):
                continue
            if stripped.startswith("#"):
                indent = len(line) - len(stripped)
                line = line[:indent] + "#" + stripped
            file_lines.append(line)

        file_lines.append("")
        rewritten_chunks.append(
            rewrite_markdown_links(
                "\n".join(file_lines),
                own_skill_name=None,
                source_dir=filepath.parent,
                skills_root=skills_root,
                skill_names_by_path=skill_by_path,
                skill_names_by_name=skill_by_name,
                digest_files=digest_files,
                link_base=effective_link_base,
                repo_root=resolved_repo_root,
            )
        )

    combined = "\n".join(rewritten_chunks)
    without_empty_headings = strip_empty_headings(combined.splitlines())
    cleaned = clean_markdown_lines(without_empty_headings)
    text = "\n".join(cleaned).strip()
    return (text + "\n") if text else "\n"


def find_budget_violations(digest_content: str, max_words: int = DEFAULT_MAX_WORDS) -> List[Tuple[int, int, str]]:
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
    """Check if the UTF-8 encoded digest exceeds the hard byte budget."""
    byte_count = len(digest_content.encode("utf-8"))
    return (byte_count <= max_bytes, byte_count, max_bytes)


def display_path(path: Path, repo_root: Path | None = None) -> str:
    """Return path relative to repo_root (or cwd) when possible, using forward slashes."""
    base = (repo_root or Path.cwd()).resolve()
    try:
        return path.resolve().relative_to(base).as_posix()
    except ValueError:
        return path.as_posix()


def format_stale_report(
    path: Path,
    current: str,
    expected: str,
    max_lines: int = MAX_DIFF_LINES,
    repo_root: Path | None = None,
) -> str:
    """Return a multi-line out-of-date message followed by a truncated unified diff."""
    shown = display_path(path, repo_root)
    diff = list(
        difflib.unified_diff(
            current.splitlines(),
            expected.splitlines(),
            fromfile=shown,
            tofile="expected",
            lineterm="",
        )
    )
    lines = [f"{shown} is out of date:", *diff[:max_lines]]
    if len(diff) > max_lines:
        lines.append(f"... and {len(diff) - max_lines} more diff lines.")
    return "\n".join(lines)


def format_violations(violations: List[Tuple[int, int, str]], scope: str) -> str:
    """Return a multi-line message listing sentence word budget violations."""
    lines = [f"Found {len(violations)} sentence word budget violation(s) in {scope}:"]
    lines.extend(f"Line {line_num} ({word_count} words): {sentence}" for line_num, word_count, sentence in violations)
    return "\n".join(lines)


def action_generate(
    paths: Sequence[Path | str],
    digest_path: Path | str = DEFAULT_DIGEST_PATH,
    skills_dir: Path | str = DEFAULT_SKILLS_DIR,
    link_base: str | None = None,
    max_words: int = DEFAULT_MAX_WORDS,
    max_bytes: int = MAX_DIGEST_BYTES,
    logger: CliLogger | None = None,
) -> int:
    """Generate the digest file and all derived skills from the given input paths."""
    logger = logger or CliLogger()
    digest_out = Path(digest_path)
    skills_out = Path(skills_dir)

    try:
        input_files = collect_input_files(paths, digest_path=digest_out, skills_dir=skills_out)
    except PathArgumentError as exc:
        logger.error(str(exc))
        return 2
    except FrontmatterError as exc:
        logger.error(str(exc))
        return 1

    repo_root = find_project_root(Path(paths[0]))
    logger.debug_msg(
        f"Collected {len(input_files)} input file(s); writing digest to {display_path(digest_out, repo_root)} "
        f"and skills to {display_path(skills_out, repo_root)} (max_words={max_words}, max_bytes={max_bytes})."
    )

    skills = build_skills(
        input_files,
        digest_path=digest_out,
        skills_dir=skills_out,
        link_base=link_base,
        repo_root=repo_root,
    )
    for skill_name, skill_content in sorted(skills.items()):
        skill_dir = skills_out / skill_name
        skill_dir.mkdir(parents=True, exist_ok=True)
        skill_path = skill_dir / "SKILL.md"
        skill_path.write_text(skill_content, encoding="utf-8", newline="\n")
        logger.info(f"Generated {display_path(skill_path, repo_root)} ({len(skill_content.splitlines())} lines).")

    digest_text = build_digest(
        input_files,
        digest_path=digest_out,
        skills_dir=skills_out,
        link_base=link_base,
        repo_root=repo_root,
    )
    digest_out.parent.mkdir(parents=True, exist_ok=True)
    digest_out.write_text(digest_text, encoding="utf-8", newline="\n")
    is_valid, byte_count, limit = check_size_budget(digest_text, max_bytes)
    logger.info(f"Generated {display_path(digest_out, repo_root)} ({len(digest_text.splitlines())} lines, {byte_count} bytes).")
    if not is_valid:
        logger.error(f"Digest size ({byte_count} bytes) exceeds the hard budget limit ({limit} bytes).")
        return 1
    return 0


def action_check(
    paths: Sequence[Path | str],
    digest_path: Path | str = DEFAULT_DIGEST_PATH,
    skills_dir: Path | str = DEFAULT_SKILLS_DIR,
    link_base: str | None = None,
    max_words: int = DEFAULT_MAX_WORDS,
    max_bytes: int = MAX_DIGEST_BYTES,
    skill_index: Path | str | None = None,
    logger: CliLogger | None = None,
) -> int:
    """Check digest and derived skills freshness, front-matter, skill coverage, budgets, and links."""
    logger = logger or CliLogger()
    digest_out = Path(digest_path)
    skills_out = Path(skills_dir)

    try:
        input_files = collect_input_files(paths, digest_path=digest_out, skills_dir=skills_out)
    except PathArgumentError as exc:
        logger.error(str(exc))
        return 2
    except FrontmatterError as exc:
        logger.error(str(exc))
        return 1

    repo_root = find_project_root(Path(paths[0]))
    logger.debug_msg(
        f"Checking {len(input_files)} input file(s), digest {display_path(digest_out, repo_root)}, "
        f"and skills under {display_path(skills_out, repo_root)} ({max_words} words, {max_bytes} bytes)."
    )
    has_error = False

    # 1. Front-matter validation across all collected input files
    allowed_top_keys = {"index", "skill"}
    allowed_skill_keys = {"name", "description"}
    for filepath in input_files:
        try:
            content = filepath.read_text(encoding="utf-8")
            fm, _ = split_frontmatter(content)
            if fm:
                unknown_top = set(fm.keys()) - allowed_top_keys
                if unknown_top:
                    logger.error(f"Unknown front-matter key(s) in {filepath.name}: {sorted(unknown_top)}")
                    has_error = True
                if "skill" in fm:
                    if not isinstance(fm["skill"], dict):
                        logger.error(f"Invalid 'skill:' front-matter in {filepath.name}: expected mapping")
                        has_error = True
                    else:
                        unknown_skill = set(fm["skill"].keys()) - allowed_skill_keys
                        if unknown_skill:
                            logger.error(f"Unknown key(s) under 'skill:' in {filepath.name}: {sorted(unknown_skill)}")
                            has_error = True
        except Exception as exc:
            logger.error(f"Error parsing frontmatter in {filepath.name}: {exc}")
            has_error = True

    # 2. Skill coverage check when --skill-index FILE is given
    if skill_index is not None:
        idx_path = Path(skill_index)
        if not idx_path.is_file():
            logger.error(f"Skill index file does not exist: {idx_path}")
            has_error = True
        else:
            idx_content = idx_path.read_text(encoding="utf-8")
            idx_resolved = idx_path.resolve()
            for filepath in input_files:
                if filepath.resolve() == idx_resolved:
                    continue
                try:
                    fm, _ = split_frontmatter(filepath.read_text(encoding="utf-8"))
                except Exception:
                    fm = None
                if fm and "skill" in fm and isinstance(fm["skill"], dict):
                    fname = filepath.name
                    if not any(token in idx_content for token in (f"({fname})", f"({fname}#", f"/{fname})", f"/{fname}#")):
                        logger.error(f"Skill guideline '{fname}' is not linked from {display_path(idx_path, repo_root)}")
                        has_error = True

    # 3. Check skills freshness against disk
    skills = build_skills(
        input_files,
        digest_path=digest_out,
        skills_dir=skills_out,
        link_base=link_base,
        repo_root=repo_root,
    )
    logger.debug_msg(f"Comparing {len(skills)} derived skill(s) under {display_path(skills_out, repo_root)}.")
    stale_skills = 0
    for skill_name, expected_skill in sorted(skills.items()):
        skill_path = skills_out / skill_name / "SKILL.md"
        if not skill_path.exists():
            logger.error(f"{display_path(skill_path, repo_root)} does not exist.")
            stale_skills += 1
            continue
        current_skill = skill_path.read_text(encoding="utf-8")
        if current_skill != expected_skill:
            logger.error(format_stale_report(skill_path, current_skill, expected_skill, max_lines=30, repo_root=repo_root))
            stale_skills += 1
        elif logger.verbose:
            logger.info(f"{display_path(skill_path, repo_root)} is up to date.")
    if stale_skills:
        has_error = True
    else:
        logger.info(f"All {len(skills)} derived skill(s) are up to date.")

    # 4. Orphan reference files and escaping links under skills_out
    reported_escaping: Set[Tuple[str, str]] = set()
    if skills_out.exists():
        for skill_dir in sorted(skills_out.iterdir()):
            if not skill_dir.is_dir() or skill_dir.name.startswith("."):
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
                            reported_escaping.add((skill_dir.name, target))
                            logger.error(f"Escaping link in skill '{skill_dir.name}': {target}")
                            has_error = True

    # 5. Digest freshness, size budget, sentence word budget, and relative links
    expected_digest = build_digest(
        input_files,
        digest_path=digest_out,
        skills_dir=skills_out,
        link_base=link_base,
        repo_root=repo_root,
    )
    is_valid_size, byte_count, limit = check_size_budget(expected_digest, max_bytes)
    if not is_valid_size:
        logger.error(f"Digest size ({byte_count} bytes) exceeds the hard budget limit ({limit} bytes).")
        has_error = True

    if not digest_out.exists():
        logger.error(f"{display_path(digest_out, repo_root)} does not exist.")
        has_error = True
    else:
        current_digest = digest_out.read_text(encoding="utf-8")
        current_valid_size, current_bytes, _ = check_size_budget(current_digest, max_bytes)
        if not current_valid_size and is_valid_size:
            logger.error(
                f"{display_path(digest_out, repo_root)} ({current_bytes} bytes) exceeds the hard budget limit ({limit} bytes)."
            )
            has_error = True
        if current_digest != expected_digest:
            logger.error(format_stale_report(digest_out, current_digest, expected_digest, repo_root=repo_root))
            has_error = True
        elif is_valid_size:
            logger.info(f"{display_path(digest_out, repo_root)} is up to date and within budget ({byte_count} bytes).")

    digest_violations = find_budget_violations(expected_digest, max_words=max_words)
    if digest_violations:
        logger.error(format_violations(digest_violations, "digest"))
        has_error = True

    in_code = False
    for line in expected_digest.splitlines():
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

    # 6. Derived skills word budget and escaping links
    for skill_name, skill_content in sorted(skills.items()):
        violations = find_budget_violations(skill_content, max_words=max_words)
        if violations:
            logger.error(format_violations(violations, f"skill {skill_name}"))
            has_error = True

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
                    if target.startswith(("../", "/", "\\")) and (skill_name, target) not in reported_escaping:
                        logger.error(f"Escaping link in skill '{skill_name}': {target}")
                        has_error = True

    if not has_error:
        logger.info(
            f"All directive sentences satisfy the {max_words}-word budget and digest size is within {limit} bytes ({byte_count} bytes)."
        )
        return 0
    return 1


def configure_paths_parser(parser: argparse.ArgumentParser) -> None:
    """Configure positional PATH arguments and require at least one path unless --help/--version is set."""
    parser.add_argument("paths", nargs="*", metavar="PATH", type=Path, help="input Markdown files or directories")
    orig_parse_args = parser.parse_intermixed_args

    def parse_args(args=None, namespace=None):
        ns = orig_parse_args(args, namespace)
        if not getattr(ns, "help", False) and not getattr(ns, "version", False) and not ns.paths:
            parser.error("the following arguments are required: PATH")
        return ns

    parser.parse_args = parse_args  # type: ignore[method-assign]


class DigestHarness(ToolHarness):
    """Tool harness adding digest configuration options to the startup banner."""

    args: argparse.Namespace | None = None

    def create_logger(self, args: argparse.Namespace) -> CliLogger:
        """Record the parsed arguments for the startup banner, then build the logger."""
        self.args = args
        return super().create_logger(args)

    def log_startup(self, logger: CliLogger, action: str, extra: dict | None = None) -> None:
        """Emit the standard startup banner including the digest configuration."""
        config: dict[str, object] = {}
        if self.args is not None:
            config["Digest"] = Path(self.args.digest).as_posix()
            config["Skills dir"] = Path(self.args.skills_dir).as_posix()
            config["Max words"] = self.args.max_words
            config["Max bytes"] = self.args.max_bytes
        super().log_startup(logger, action, extra={**config, **(extra or {})})

    def run(self, argv: Sequence[str] | None = None, extra_startup: dict | None = None) -> int:
        """Validate path arguments before emitting the startup banner so invalid paths exit 2 cleanly."""
        raw_args = list(sys.argv[1:] if argv is None else argv)
        if raw_args and raw_args[0] in self._actions:
            action_name = raw_args[0]
            action = self._actions[action_name]
            parser = self._build_parser(action_name)
            try:
                old_err = parser.error
                parser.error = lambda msg: (_ for _ in ()).throw(ValueError(msg))  # type: ignore[method-assign]
                ns = parser.parse_args(raw_args[1:])
                parser.error = old_err  # type: ignore[method-assign]
            except ValueError:
                pass
            else:
                if not getattr(ns, "help", False) and not getattr(ns, "version", False):
                    for p in getattr(ns, "paths", []):
                        path = Path(p)
                        if not path.exists():
                            early = self._extract_early_logger(raw_args)
                            early.error(f"Path does not exist: {path}\nUsage: {self.name} {action_name} {action.usage_suffix}")
                            early.close()
                            return 2
                        if path.is_file() and path.suffix.lower() != ".md":
                            early = self._extract_early_logger(raw_args)
                            early.error(
                                f"Path is not a Markdown (.md) file: {path}\nUsage: {self.name} {action_name} {action.usage_suffix}"
                            )
                            early.close()
                            return 2
        return super().run(argv, extra_startup=extra_startup)


def build_harness() -> DigestHarness:
    """Construct the CLI harness with the generate and check actions."""
    harness = DigestHarness(
        name=TOOL_NAME,
        description="Deterministic generator and validator for agent digest Markdown files and derived skills.",
        version=TOOL_VERSION,
        exit_codes={
            0: "success (generate: written within budget; check: up to date and all validations passed)",
            1: "stale digest or skill, validation or budget failure, invalid front-matter, or runtime error",
            2: "invalid command-line arguments, missing PATH, or non-Markdown file argument",
        },
        examples=[
            f"{TOOL_NAME} generate guidelines",
            f"{TOOL_NAME} generate guidelines --digest guidelines/agent-digest.md --skills-dir skills",
            f"{TOOL_NAME} check guidelines --digest guidelines/agent-digest.md --skills-dir skills --skill-index guidelines/general-guidelines.md",
        ],
    )
    harness.add_global_argument(
        "--digest",
        type=Path,
        default=DEFAULT_DIGEST_PATH,
        metavar="PATH",
        help=f"output digest Markdown file path (default: ./{DEFAULT_DIGEST_PATH.as_posix()})",
    )
    harness.add_global_argument(
        "--skills-dir",
        type=Path,
        default=DEFAULT_SKILLS_DIR,
        metavar="PATH",
        help=f"output directory for derived skills (default: ./{DEFAULT_SKILLS_DIR.as_posix()})",
    )
    harness.add_global_argument(
        "--link-base",
        type=str,
        default=None,
        metavar="URL",
        help="base URL for rewriting relative repository links (default: derived from origin remote)",
    )
    harness.add_global_argument(
        "--max-words",
        type=int,
        default=DEFAULT_MAX_WORDS,
        metavar="N",
        help=f"maximum words per directive sentence (default: {DEFAULT_MAX_WORDS})",
    )
    harness.add_global_argument(
        "--max-bytes",
        type=int,
        default=MAX_DIGEST_BYTES,
        metavar="N",
        help=f"maximum digest size budget in bytes (default: {MAX_DIGEST_BYTES})",
    )
    harness.add_global_argument(
        "--skill-index",
        type=Path,
        default=None,
        metavar="FILE",
        help="Markdown file that must link every skill source file (checked by 'check')",
    )
    harness.add_action(
        "generate",
        "extract derived skills and assemble the digest from Markdown paths",
        handler=lambda args, logger: action_generate(
            paths=args.paths,
            digest_path=args.digest,
            skills_dir=args.skills_dir,
            link_base=args.link_base,
            max_words=args.max_words,
            max_bytes=args.max_bytes,
            logger=logger,
        ),
        detail="Collects Markdown files from each PATH, orders them by front-matter 'index' then\n"
        "argument and path order, writes derived skills to --skills-dir, and writes the digest to --digest.",
        usage_suffix="<PATH>... [options]",
        configure_parser=configure_paths_parser,
    )
    harness.add_action(
        "check",
        "verify that the digest and derived skills are up to date and pass all validations",
        handler=lambda args, logger: action_check(
            paths=args.paths,
            digest_path=args.digest,
            skills_dir=args.skills_dir,
            link_base=args.link_base,
            max_words=args.max_words,
            max_bytes=args.max_bytes,
            skill_index=args.skill_index,
            logger=logger,
        ),
        detail="Regenerates the digest and derived skills in memory and compares them against --digest\n"
        "and --skills-dir on disk, while validating front-matter keys, word and byte budgets,\n"
        "orphan reference files, link constraints, and optional --skill-index coverage.",
        usage_suffix="<PATH>... [options]",
        configure_parser=configure_paths_parser,
    )
    return harness


def main(argv: Sequence[str] | None = None) -> int:
    """Run the command line and return its exit code."""
    return build_harness().run(argv)


if __name__ == "__main__":
    sys.exit(main())
