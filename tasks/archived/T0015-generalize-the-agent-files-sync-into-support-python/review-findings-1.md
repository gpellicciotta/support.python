---
task: T0015
round: 1
verdict: approved
reviewer: "@claude"
reviewed_at: 2026-11-07T17:39:27Z
reviewed_commit: "4133650"
base_commit: "d9f4c53"
branch: task/T0015-generalize-the-agent-files-sync-into-support-python
---
# Review Findings: Task T0015 (Round 1)

## Summary
The work meets the task goals.
`support_python.agent_files` is a near-verbatim copy of dev-guidelines `update-global-agent-files.py`.
The diff against the original is limited to imports, repository-root resolution, and the `sync`/`check` aliases.
`support-python agent-files list|sync|check|review` dispatches correctly.

Verification run in the worktree:
- `pytest`: 741 passed, 3 skipped.
- `tests/test_agent_files.py`: 87 passed.
- `ruff check .` and `ruff format --check .`: clean.
- Dry-run comparison: `update --dry-run` from the original script and `agent-files sync --dry-run` from the port, both run in dev-guidelines. The outputs differ only in the version banner (and the `python -m` runpy warning). Exit codes match (1 and 1).

The ported test file differs from the original only in its import/bootstrap lines and a `PYTHONPATH` entry for its subprocess test. It adds two tests: repository-root resolution and CLI dispatch.

## Defects
None blocking.

Minor observations, not required for approval:
- `src/support_python/cli.py` adds a `PROJECT_VERSION` fallback chain (package directory, then `get_package_version`). The task file does not declare it or log it as a decision. It is harmless but outside the stated scope.
- Deviations from "unchanged" go beyond imports and root resolution: the `ToolLogger` subclass, `create_logger` re-wrapping, `main()` stream reconfiguration, and the `sync`/`check` aliases. The Execution Log records the aliases and the stream move. It does not mention the logger changes.

## Process Gaps
- The Execution Log gives no command lines or captured output for the dry-run comparison. It states the result only.
- The log says "Bumped active version to v1.0.21-pre". This is consistent across `CHANGELOG.md` and `pyproject.toml`, so it is not an issue.

## Required Rework
None.
