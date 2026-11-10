---
task: T0029
round: 2
verdict: approved
reviewer: "@claude"
reviewed_at: 2026-11-09T23:24:03Z
reviewed_commit: "9e0044f"
base_commit: "f0e01fb"
branch: task/T0029-align-agent-files-with-adr-0003-canonical-sync
---
# Review Findings: Task T0029 (Round 2)

## Summary
Approved.
Commit `9e0044f` fixes all four required items from round 1, plus both optional ones.
- JSON `check` now uses the same `sync_tool`/`sync_tool_skills` path as text `check`, collecting a `changes` list.
  `collect_tool_changes` is gone.
- `status: unavailable` is emitted when a target cannot be read or has invalid markers.
  The docs describe this mapping.
- `pyproject.toml` and the CHANGELOG heading both read `2.0.11-pre`.
- The dead `update`/`diff` branches and docstrings are removed.
- The legacy-config warning goes through the harness early logger and reaches `--log-file`.
- `list --format json` emits one key per column.
- JSON-mode banners now rely on `StderrRoutingLogger(json_mode=True)` instead of copied banner code.
  A failed JSON `check` now writes its failure line to stderr.

Verified on `9e0044f`:
- `pytest -q`: 710 passed, 3 skipped, 66 subtests passed, exit 0.
- `ruff check .` and `ruff format --check .`: clean, 97 files formatted.
- Installed `agent-files` in a temporary Git project.
  `.agent-files.json` used `replace_tools` to route two tools into temporary directories:
  - `list --format json`: exit 0, documented keys only.
  - `check --format json` before sync: both tools `changes-pending`, exit 1.
  - `sync`: exit 0. Then text `check` and JSON `check` each exit 0, both tools `up-to-date`, stderr empty.
  - After hand-editing a target: text and JSON `check` both exit 1, and JSON reports `changes-pending` for that tool only.
  - `--no-prune` plus a stale `extra.md` in an installed skill: text and JSON both exit 1.
    JSON lists `stale file in target: extra.md`. This was round 1's defect 1, and it is fixed.
  - Directory in place of a target file: text and JSON both exit 1, JSON `status: unavailable`.
  - Legacy `agent-files.json` with `check --format json --log-file`: stdout parses as JSON.
    The WARN appears on stderr and in the log file.
  - `update` and `diff` exit 2. Help lists `list`, `sync`, `check`, `review`, `version`, and `help`.

## Defects
None blocking. Minor observations:
1. `action_sync` picks `unavailable` by matching the `"invalid target "` string prefix produced in `sync_tool`.
   This couples two functions through a message string.
   A structured flag, such as a return tuple or a separate list, would be sturdier.
2. In the log file, the legacy-config WARN comes before the `Starting agent-files ...` banner.
   That is because config loads before the harness logger exists. Cosmetic only.
3. Config-discovery case 2 now runs through `_run_main(["list", ...])`.
   It dropped the earlier `cfg2.marker == "legacy-marker"` assertion.
   So no test now asserts that legacy-only discovery actually reads the legacy file's values.

## Process Gaps
- The Execution Log has no red-phase proof for the round 2 regression tests:
  - text and JSON agreement under `--no-prune`
  - `unavailable` on invalid markers
  - legacy warning reaching `--log-file`

  `validation-proof.md` still shows only the round 1 red run.
- Pre-existing and outside this task: tool `target_file`/`skills_dir` values in `.agent-files.json` are only `expanduser()`-ed.
  They are not resolved against `repo_root`, although the docs say all relative paths resolve against it.
  The integration run shows the relative `out\a\AGENTS.md` resolving against the CWD.
  Recommend a backlog task.
- Pre-existing: `SyncHarness._build_parser` and the unknown-subcommand path still log through a bare `CliLogger()`.
  So those errors bypass `--log-file`.

## Required Rework
None.
Optional follow-ups:
- Replace the `"invalid target "` prefix match with a structured signal.
- Restore an assertion that legacy-only discovery reads the legacy config's values.
