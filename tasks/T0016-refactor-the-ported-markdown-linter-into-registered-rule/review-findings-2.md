---
task: T0016
round: 2
verdict: approved
reviewer: "@claude"
reviewed_at: 2026-11-07T19:07:23Z
reviewed_commit: "bcee7b3"
base_commit: "98420d2"
branch: task/T0016-refactor-the-ported-markdown-linter-into-registered-rule
---
# Review Findings: Task T0016 (Round 2)

## Summary
Both Round 1 defects are fixed.
- `markdown.py` moved to `markdown/tables.py` (rename, 100% similar). The `importlib`/`sys.modules` hack is gone, and `markdown/__init__.py` re-exports through a normal import.
- README.md, CLAUDE.md, CHANGELOG.md, and docs/index.md now reference the new layout.
- `run_lint` now always calls `load_profile`, so the no-config path and the config-without-`profile`-key path both resolve to `default`.
- Manual CLI check on a file with `## Sub`, a blank line, then body text: no config gives no `MD015`; `--profile dev-guidelines` gives `MD015`; a config of only `{"disable": ["MD018"]}` gives no `MD015`. The paths agree.
- docs/markdown-lint.md states the fallback rules, including that `MarkdownLinter(profile=None)` keeps the legacy all-rules behavior.
- New tests cover no-config, `--profile default`, and config without a `profile` key.
- Verified in the worktree: `ruff check` clean, `ruff format --check` clean (91 files), full pytest 752 passed, 3 skipped.
- I did not re-run the dev-guidelines T0014 output parity check. I rely on the Execution Log and `validation-proof.md`. The Round 2 commit changed only the file location and the CLI default resolution.

## Defects
None

## Process Gaps
None

## Required Rework
None
