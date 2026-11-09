---
task: T0025
round: 1
verdict: rejected
reviewer: "@claude"
reviewed_at: 2026-11-09T20:32:41Z
reviewed_commit: "2265507"
base_commit: "8622534"
branch: task/T0025-move-the-processes-agent-files-and-backup-cli
---
# Review Findings: Task T0025 (Round 1)

## Summary
The moves themselves are correct and complete.
They match the spec table, use `git mv` history, and fix all relative and lazy imports.
Console scripts, test patch targets, docs links, and the old-module-gone test are in place.
Independent verification at `2265507`, all exit 0:
- `python -m pytest -q`: 695 passed, 3 skipped, 64 subtests passed.
- `python -m unittest discover -s tests`: 542 tests OK.
- `ruff check .` and `ruff format --check .` pass.
- `processes list --format json`, `agent-files list`, and `git-repository-backup version` all exit 0.

The work is rejected because it adds a behavior change, which the task title forbids.
It also leaves one stale module path in a mandatory doc.

## Defects
1. **New package-root re-exports add an import-time side effect.**
   - On `main`, `src/support_python/__init__.py` never imported `agent_files` or `agent_files_config`.
   - The spec's "keep the package root re-exports" therefore had nothing to keep.
   - The diff instead adds `SyncHarness`, `Tool`, `AgentFilesConfig`, `ToolRegistry`, and `load_agent_files_config` imports and `__all__` entries.
   - Effect: every `import support_python` now imports `support_python.tools.agent_files`.
     That runs `find_project_root()` at module level, walking the filesystem up from the CWD.
   - Verified: after `import support_python`, `support_python.tools.agent_files` is in `sys.modules`, with `REPO_ROOT` set to the CWD's repository.
   - This contradicts "without behavior changes" and the ADR-0003 split between library and tools.
     The library root now depends on a tool module.
   - The new public API is not mentioned in `CHANGELOG.md`.
   - The spec/codebase mismatch was not logged as a `**[Decide]**` entry or raised as a question.
2. **Stale module path in a mandatory doc.**
   - `docs/requirements.md:98` still names `support_python.agent_files_config`.
   - It should name `support_python.tools.agent_files_config`.

## Process Gaps
- The worker ran `pip install -e .` into the main checkout's shared `.venv`.
  - That editable install now points at this worktree's `src`.
  - The main checkout's environment now runs branch code, and it breaks once the worktree is removed.
  - Record this and reinstall from the main checkout after merge.
- Non-blocking: historical CHANGELOG entries for v1.3.0 (lines 31–34) now carry dead links.
  - `lint-markdown` flags them as MD014.
  - This matches the precedent T0034 set for `devops.py`, so no rework is required.

## Required Rework
1. Remove the five package-root imports and their `__all__` entries from `src/support_python/__init__.py`.
   Log a `**[Decide]**` entry explaining that `main` had no such re-exports.
   Alternative: keep them only with explicit user approval, a CHANGELOG entry, and lazy loading that avoids the import side effect.
2. If rework item 1 removes the re-exports, update `CLAUDE.md`'s Architecture intro.
   It says public symbols are re-exported from the package root, and it lists the agent-files symbols.
   Note that tool modules under `support_python.tools` are not re-exported.
3. Update `docs/requirements.md:98` to `support_python.tools.agent_files_config`.
4. Re-run `pytest`, `ruff check .`, and the three integration commands.
   Record the evidence in the validation proof.
