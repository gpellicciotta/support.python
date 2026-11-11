---
task: T0069
round: 1
verdict: approved
reviewer: "@claude-2"
reviewed_at: 2026-11-11T01:17:33Z
reviewed_commit: "0a636a9"
base_commit: "c2db699"
branch: task/T0069-move-lint-markdown-settings-onto-the-shared-resolver
---
# Review Findings: Task T0069 (Round 1)

## Summary
The work meets the goals. `lint-markdown` resolves settings through `SettingsSchema` and `resolve_settings`. It adds the `config` group through `add_config_actions`, and the legacy `.markdown-lint.json` discovery is kept. `Setting.aliases` and the `profile_from_settings` helpers are small, documented additions. `load_profile` still works for library callers.

Verification run in the worktree, using the main checkout's venv with `PYTHONPATH=src` because the worktree has no `.venv`:
- Full suite: 1171 passed, 5 skipped.
- `ruff check src tests`: clean.
- `config list` shows all eight settings with their sources.
- `lint-markdown check --offline` reports 7 issues, all in `tests/fixtures/agent_digest/`. They are unresolved relative links that point outside the worktree. This is an artifact of the worktree location, not of this change.

## Defects
None.

## Process Gaps
- The red-phase and green-phase proof is recorded in `validation-proof.md`.
- The slow tests need `PYTHONPATH=src` in a worktree. The proof notes this.

## Required Rework
None.
