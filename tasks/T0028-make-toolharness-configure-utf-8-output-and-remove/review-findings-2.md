---
task: T0028
round: 2
verdict: approved
reviewer: "@claude"
reviewed_at: 2026-11-09T22:19:56Z
reviewed_commit: "ed15b12"
base_commit: "887e11a"
branch: task/T0028-make-toolharness-configure-utf-8-output-and-remove
---
# Review Findings: Task T0028 (Round 2)

## Summary
Approved. The round-1 rework resolves all required items.
- `src/support_python/processes.py:377` and `:417` no longer repeat `CliLogger`.
- `CLAUDE.md:35` and `docs/index.md:12` no longer mention the removed aliases.
- The `agent_files` subclass is now `StderrRoutingLogger`. Tests and `SyncHarness.create_logger` use the new name.
- `technical-spec.md` declares all 17 touched files and documents the `python -c` integration-test mechanism.

The `CliLogger().error(...)` calls at `src/support_python/tools/agent_files.py:984`, `:1010`, and `:1059` now use the base class.
Behavior is unchanged: base `CliLogger.error` already passes `to_stderr=True` explicitly.
The only remaining alias mentions are in `CHANGELOG.md`: the new breaking-change note and the historical v2.0.0 entry. Both are correct.

Reviewer verification on `ed15b12`:
- `ruff check .` passed. `ruff format --check .` reported 97 files already formatted.
- `PYTHONPATH=src python -m pytest -q`: 705 passed, 3 skipped, 64 subtests passed.
- Installed `processes`, `agent-files`, `lint-markdown`, and `git-repository-backup` `help` exit 0 when piped with `PYTHONIOENCODING=cp1252`.
- A cp1252-piped `lint-markdown` `main(['version'])` followed by printing `✓ →` exits 0 and prints the characters.
- `git diff --stat main...HEAD` shows 17 files, 149 insertions, 118 deletions. This matches the logged 17 files and 267 lines.

## Defects
None.

## Process Gaps
None blocking.
- The work exceeded its 11-file, 150-line estimate (17 files, 267 lines). It stays under three times the estimate, and the spec's size note explains why.

## Required Rework
None.
