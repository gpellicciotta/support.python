"""Sample lint-markdown plugin registering rule X001, which flags TODO markers in prose."""

from __future__ import annotations

import re

from support_python.markdown import LintContext, LintIssue, Rule, RuleRegistry


class NoTodo(Rule):
    """Report TODO markers left in Markdown prose."""

    rule_id = "X001"
    name = "no-todo"
    description = "Disallow TODO markers in prose."

    def check(self, ctx: LintContext) -> list[LintIssue]:
        """Report the first TODO marker on the current prose line."""
        match = re.search(r"\bTODO\b", ctx.sanitized)
        if match is None:
            return []
        return [self.issue(ctx, "TODO marker found in prose", column_number=match.start() + 1)]


def register(registry: RuleRegistry) -> None:
    """Register the plugin rules with the active lint-markdown rule registry."""
    registry.register(NoTodo())
