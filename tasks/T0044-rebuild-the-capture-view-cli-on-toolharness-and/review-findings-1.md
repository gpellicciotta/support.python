---
task: T0044
round: 1
verdict: rejected
reviewer: "@claude-2"
reviewed_at: 2026-11-10T04:30:20Z
reviewed_commit: "6eb9e9b"
base_commit: "62c26fd"
branch: task/T0044-rebuild-the-capture-view-cli-on-toolharness-and
---
# Review Findings: Task T0044 (Round 1)

## Summary
The helper removal is complete and clean.
`build_action_parser`, `print_help`, `print_version`, and `format_version` are gone from `cli.py`, `__all__`, and the package root.
`scripts/` still uses only `_cli_common.py`.
The CHANGELOG lists both changes as **[breaking]** under the unreleased `v2.0.27-pre` major.
README, `docs/index.md`, and `docs/requirements.md` no longer mention the removed helpers.

The capture CLI rebuild has one behavior regression, so the verdict is rejected.

Independent verification on `6eb9e9b`, using the primary checkout's `.venv` with `PYTHONPATH=src`:
- `ruff check .` and `ruff format --check .`: passed (143 files formatted).
- `python -m pytest -q`: 1036 passed, 3 skipped, 129 subtests passed (exit 0).
- Grep of `src`, `tests`, `scripts`, `README.md`, and `docs`: no remaining uses outside `scripts/_cli_common.py` and the removal test.
- Probe script with `run_capture`, `run_tour`, and `print_presets_list` mocked, run outside the repo (results below).

## Defects
1. **Leading global options send explicit actions to `capture`** (`src/support_python/capture.py`, `run_capture_cli`).
   `run_capture_cli` inserts `capture` before any first token that starts with `-`, except `-h`, `--help`, and `--version`.
   Any global option placed before an action therefore turns that action into the capture target.
   Probe results:
   - `--verbose list` ran `run_capture(target="list")`, not the list action.
   - `--debug tour` ran `run_capture(target="tour")`, not `run_tour`.
   - `--log-file x.log list` ran `run_capture(target="list")`.

   The old argparse parser placed `action` anywhere among the options, so `--verbose list` ran `list`.
   `run_capture` treats an unknown target as a relative URL path (`raw_path = url or target`).
   So `capture-view --verbose tour` silently screenshots `/tour` instead of running the tour.
   That breaks the goal of keeping the existing actions and capture behavior.
   No test covers a leading global option followed by an action.

2. **Minor, non-blocking: `list` stdout now includes harness startup and completion log lines.**
   `handle_list` runs through the harness's logged dispatch.
   So the preset listing now sits between `Starting ... with configuration:` and `Finished ... list` lines.
   This matches the harness convention, but it also changes plain `list` output.
   The CHANGELOG entry does not mention it.

3. **Minor, non-blocking: the capture logger lost `origin=config.cli_name`.**
   The old code built `CliLogger(..., origin=config.cli_name)`.
   `ToolHarness.create_logger` passes no origin.
   Mention this if log consumers depend on it; otherwise ignore it.

## Process Gaps
1. The spec's integration check (`../auth/scripts/capture-view.py help` exits 0) failed.
   The spec allowed a waiver only when auth needs unavailable dependencies.
   The real cause is that auth imports the removed helpers and `build_capture_parser` directly.
   The worker recorded the failure honestly, added a read-only shim check, and filed auth backlog task T0217.
   This is acceptable, but the failure is a spec deviation, not a dependency waiver.
   The deviation should be logged as a `**[Decided]**` entry.
2. Several other sibling consumers import the removed helpers from `support_python`.
   Examples: `counters.server`, `todos.server`, and `template.python`, which pin `@v1.0.0`.
   Pinned consumers are unaffected until they upgrade.
   Only auth's unpinned fallback was surveyed and backlogged.
   Consider one backlog note covering the v2 migration of these pinned consumers.
3. The diff touched 9 files and 572 lines against an estimate of 7 files and 350 lines.
   The overrun is recorded in the Execution Log and stays below the 3x sign-off threshold.

## Required Rework
1. Fix `run_capture_cli` so leading global options do not hide an explicit action.
   Example: when a later non-option token is a registered action (`capture`, `tour`, `list`, `version`, `help`), dispatch to that action.
   Keep the leading options when doing so.
   Insert `capture` only when no action token follows.
   Handle options that take values (`--log-file PATH`, `--log-level LEVEL`) so their values are not mistaken for actions or targets.
2. Add unit tests, written to fail before the fix, covering:
   - `--verbose list`, which calls `print_presets_list`, not `run_capture`.
   - `--debug tour`, which calls `run_tour`.
   - `--log-file PATH list`, which calls `print_presets_list` and sets the log file.
   - `--mobile sign-in`, which still captures `sign-in` with the mobile viewport.
3. Optionally, note the extra startup and completion lines around `list` output in the existing CHANGELOG entry.
