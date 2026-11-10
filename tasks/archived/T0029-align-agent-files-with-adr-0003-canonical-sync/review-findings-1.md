---
task: T0029
round: 1
verdict: rejected
reviewer: "@claude"
reviewed_at: 2026-11-09T22:46:52Z
reviewed_commit: "1e518c1"
base_commit: "f0e01fb"
branch: task/T0029-align-agent-files-with-adr-0003-canonical-sync
---
# Review Findings: Task T0029 (Round 1)

## Summary
Most goals are met.
`sync`, `check`, `list`, and `review` are canonical, and `update` and `diff` exit 2.
Help examples are fixed.
`list --format json` works, and `.agent-files.json` discovery falls back to the legacy name with a warning.
Verified on `1e518c1`:
- `pytest -q`: 710 passed, 3 skipped, exit 0.
- `ruff check .` and `ruff format --check .`: clean.
- `lint-markdown check --offline` on the changed docs: every reported issue already exists on `main`.
- Installed `agent-files` in a temporary project: legacy-config warning goes to stderr and JSON stdout parses.
- Installed `agent-files` in a temporary project: `sync` then `check` exits 0.

Rejected for three reasons:
- In one case, JSON `check` returns a different exit code than text `check`.
- `check --format json` never emits the `unavailable` status from the spec.
- The CHANGELOG and `pyproject.toml` versions disagree.

## Defects
1. **`check` exit code depends on `--format` (correctness).**
   `collect_tool_changes` (`src/support_python/tools/agent_files.py`) re-implements the diff logic.
   The spec asked for `changes` derived from the existing diff data.
   With `--no-prune`, it drops stale-file diffs.
   Text `check` goes through `sync_tool_skills`, which keeps them.
   Reproduction: after `sync`, add `extra.md` to an installed skill directory, then run:
   - `agent-files check --no-prune`: logs `stale file in target: extra.md` and exits 1.
   - `agent-files check --no-prune --format json`: returns `status: up-to-date` with an empty `changes` list and exits 0.
   Two parallel implementations can drift further, for example on legacy-dir handling and marker errors.
2. **The `unavailable` status is never emitted (spec deviation).**
   The spec defines `status` as `up-to-date`, `changes-pending`, or `unavailable`.
   The JSON path only produces the first two.
   Invalid guarded-block markers also show up as `changes-pending`, not as an error.
3. **Version mismatch (project convention).**
   The CHANGELOG top heading became `## v2.0.11-pre`, but `pyproject.toml` still says `version = "2.0.10-pre"`.
   CLAUDE.md requires them to match exactly.
   Earlier task commits (T0024 to T0028) bumped both together.
4. **Leftover legacy verb handling (minor).**
   The goal says the `update` and `diff` names are removed.
   Several functions still branch on them:
   - `ensure_digest`
   - `sync_tool`
   - `prune_skill_dirs`
   - `clean_legacy_skills_dir`
   - `sync_tool_skills`

   These branches are now dead and their docstrings mention the old verbs.
5. **Legacy-config warning skips the harness logger (minor).**
   `load_agent_files_config` warns through a new bare `CliLogger()`.
   So the deprecation warning never reaches `--log-file`.
6. **Redundant JSON keys (minor).**
   `list --format json` emits duplicate pairs:
   - `instructions_file`/`target`
   - `skills_dir`/`skills_target`
   - `available`/`status`

   The spec asked for the table columns as snake_case keys.
   Pick one name per column.

## Process Gaps
- No test checks that text and JSON `check` agree, including under `--no-prune`. That gap let defect 1 through.
- No test covers the `unavailable` status.
- The JSON-mode banner suppression in `SyncHarness.log_startup`/`log_completion` copies `ToolHarness.log_startup`.
  It also copies the same pattern in `git_repository_backup.py`.
  A shared harness hook would remove both copies. This is a recommendation, not blocking.
- In JSON mode, a failed `check` writes no failure line to stderr (`to_stderr=False`).
  `git-repository-backup` still reports failures.
  Align the two or record the choice.
- The Execution Log records validation error TF020 but never records how it was fixed.

## Required Rework
1. Make JSON `check` use the same logic as text `check`, so both return the same exit code for the same inputs.
   For example, collect the changes from the existing `sync_tool`/`sync_tool_skills` check path.
   Add a regression test for the `--no-prune` stale-file case.
2. Emit `status: unavailable` as the spec defines it, and add a test.
   Or record a `**[Decided]**` spec change with the user's agreement.
   Report marker errors as something other than plain `changes-pending`, or document how they map.
3. Make `pyproject.toml` `version` match the CHANGELOG top heading.
4. Remove the dead `update`/`diff` branches and refresh the docstrings that mention them.
5. Optional: send the legacy-config warning through the harness logger, and drop the duplicate JSON keys.
