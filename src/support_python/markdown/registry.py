"""Rule base class, lint execution context, and rule registry for Markdown linting."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
import re
from typing import TYPE_CHECKING, Any, Iterable, Iterator, Sequence

if TYPE_CHECKING:
    from support_python.markdown_lint import LintIssue


@dataclass
class LintContext:
    """Shared document and line state passed to registered Markdown lint rules."""

    file_path: Path
    actual_file_path: Path
    project_root: Path
    raw_bytes: bytes
    lines: list[str]
    is_changelog: bool = False
    in_released_changelog: bool = False
    is_historical_task: bool = False
    local_heading_slugs: set[str] = field(default_factory=set)
    linter: Any = None
    line_number: int = 1
    line: str = ""
    unquoted_line: str = ""
    sanitized: str = ""
    fence_indent: str = ""
    fence_lang: str = ""
    heading_level: int = 0
    heading_title: str = ""
    prev_heading_level: int = 0
    h1_count: int = 0
    bullet_match: re.Match[str] | None = None


class Rule:
    """Base class for a registered Markdown lint rule."""

    rule_id: str = ""
    name: str = ""
    description: str = ""
    scope: str = "prose"
    fixable: bool = False

    def issue(
        self,
        ctx: LintContext,
        message: str,
        *,
        line_number: int | None = None,
        column_number: int = 1,
    ) -> LintIssue:
        """Construct a LintIssue for this rule at the given location."""
        from support_python.markdown_lint import LintIssue

        return LintIssue(
            file_path=ctx.file_path,
            line_number=ctx.line_number if line_number is None else line_number,
            column_number=column_number,
            rule_id=self.rule_id,
            rule_name=self.name,
            message=message,
            fixable=self.fixable,
        )

    def check(self, ctx: LintContext) -> list[LintIssue]:
        """Evaluate this rule against the current LintContext state."""
        return []

    def lint(
        self,
        content: bytes | str,
        file_path: Path = Path("test.md"),
        *,
        project_root: Path | None = None,
        offline: bool = False,
    ) -> list[LintIssue]:
        """Run only this rule against raw Markdown content and return reported issues."""
        from support_python.markdown_lint import MarkdownLinter

        raw_bytes = content.encode("utf-8") if isinstance(content, str) else content
        registry = RuleRegistry([self])
        linter = MarkdownLinter(
            enabled_rules={self.rule_id},
            offline=offline,
            project_root=project_root,
            registry=registry,
        )
        return linter.lint_content(file_path, raw_bytes, project_root=project_root)


class RuleRegistry:
    """Ordered registry of Markdown lint rules supporting lookup by ID or name."""

    def __init__(self, rules: Sequence[Rule] | None = None) -> None:
        """Initialize the registry with the given rules, or the built-in default rules when None."""
        if rules is None:
            from support_python.markdown.rules import DEFAULT_RULES

            rules = DEFAULT_RULES
        self._rules: dict[str, Rule] = {}
        for rule in rules:
            self.register(rule)

    def register(self, rule: Rule) -> None:
        """Register or replace a Rule instance by its uppercase rule_id."""
        if not isinstance(rule, Rule) or not rule.rule_id.strip() or not rule.name.strip():
            raise ValueError("Rule must define non-empty 'rule_id' and 'name'")
        self._rules[rule.rule_id.strip().upper()] = rule

    def get(self, rule_id_or_name: str) -> Rule | None:
        """Return the rule matching rule_id (case-insensitive) or rule name, or None."""
        key = rule_id_or_name.strip()
        by_id = self._rules.get(key.upper())
        if by_id is not None:
            return by_id
        lower_name = key.lower()
        for rule in self._rules.values():
            if rule.name.lower() == lower_name:
                return rule
        return None

    def __contains__(self, rule_id_or_name: object) -> bool:
        """Return True if rule_id_or_name is registered in this registry."""
        return isinstance(rule_id_or_name, str) and self.get(rule_id_or_name) is not None

    def __iter__(self) -> Iterator[Rule]:
        """Iterate over registered rules in registration order."""
        return iter(self._rules.values())

    def __len__(self) -> int:
        """Return the number of registered rules."""
        return len(self._rules)

    def list(self) -> list[Rule]:
        """Return all registered rules in registration order."""
        return list(self._rules.values())

    def rule_ids(self) -> list[str]:
        """Return all registered rule IDs in registration order."""
        return list(self._rules.keys())

    def as_rules_dict(self) -> dict[str, tuple[str, str]]:
        """Return mapping of rule_id to (name, description) tuples."""
        return {rule.rule_id: (rule.name, rule.description) for rule in self._rules.values()}

    def select(self, rule_ids: Iterable[str] | None = None) -> list[Rule]:
        """Return registered rules matching rule_ids in registry order, raising ValueError on unknown IDs."""
        if rule_ids is None:
            return list(self._rules.values())
        selected_ids: set[str] = set()
        for raw_id in rule_ids:
            rule = self.get(raw_id) if isinstance(raw_id, str) else None
            if rule is None:
                raise ValueError(f"Unknown rule ID: '{raw_id}'")
            selected_ids.add(rule.rule_id)
        return [rule for rule in self._rules.values() if rule.rule_id in selected_ids]


__all__ = ["LintContext", "Rule", "RuleRegistry"]
