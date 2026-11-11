---
task: T0076
round: 1
verdict: rejected
reviewer: "@claude-2"
reviewed_at: 2026-11-11T01:36:10Z
reviewed_commit: "5267d23"
base_commit: "607f998"
branch: task/T0076-add-format-text-json-to-lint-markdown-fix
---
# Review Findings: Task T0076 (Round 1)

## Summary
The implementation is correct and meets the goals. `fix --format json` works, including `--dry-run`, empty, and failure cases. Exit codes and text output are unchanged. `tests/tools/test_lint_markdown.py` passes (56 passed), and ruff check and format are clean. Two small defects remain, one in the docs and one in the JSON key naming.

## Defects
1. `docs/tools/lint-markdown.md`: the diff adds a stray second `---` separator after the config bullet, just before "Built-In Profiles". The file now has two consecutive horizontal rules. The Markdown linter does not flag it, but it is an editing error.
2. Key naming is inconsistent. `check --format json` emits `files_checked`, but `fix --format json` emits `files-checked` (`_emit_json_fix`, `src/support_python/tools/lint_markdown.py`). The task goal says to reuse the `check` JSON shape, and the other fields (`rule_id`, `rule_name`) use underscores. The mix of dashed and underscored keys makes the two documents inconsistent for consumers.

## Process Gaps
None

## Required Rework
- Remove the duplicate `---` in `docs/tools/lint-markdown.md`.
- Use one key style across `check` and `fix` JSON. Either rename `files-checked` to `files_checked`, or justify `dry-run`/`files-checked` as the guideline convention. Then update the tests and the docs example to match.
