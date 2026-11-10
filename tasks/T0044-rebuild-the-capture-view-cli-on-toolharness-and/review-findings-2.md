---
task: T0044
round: 2
verdict: approved
reviewer: "@claude-2"
reviewed_at: 2026-11-10T04:39:57Z
reviewed_commit: "bbbe746"
base_commit: "62c26fd"
branch: task/T0044-rebuild-the-capture-view-cli-on-toolharness-and
---
# Review Findings: Task T0044 (Round 2)

## Summary
Round 1's blocking defect is fixed, so the verdict is approved.
`run_capture_cli` now skips leading options and their values, then dispatches a following action token.
It inserts `capture` only when no action token follows.
The capture parser's own option table decides which options take values.

Round 1's optional items are also handled:
- The CHANGELOG entry now covers the `list` startup and completion lines and the dropped `cli_name` origin.
- The Execution Log records the auth integration check failure as a `**[Decided]**` spec deviation.

Independent verification on `bbbe746`, using the primary checkout's `.venv` with `PYTHONPATH=src`:
- `support_python.__file__` resolved to the worktree's `src`.
- `ruff check .` and `ruff format --check .`: passed (143 files formatted).
- `python -m pytest -q`: 1041 passed, 3 skipped, 133 subtests passed (exit 0).
- Probe with `run_capture`, `run_tour`, and `print_presets_list` mocked:

```text
--verbose list               -> 0 list
--debug tour                 -> 0 tour
--log-level DEBUG list       -> 0 list
--log-level=DEBUG list       -> 0 list
-vv list                     -> 0 list
--port 8000 tour             -> 0 tour (port 8000)
--mobile sign-in             -> 0 capture(target='sign-in')
--mode tour sign-in          -> 0 capture(target='sign-in')
-- tour                      -> 0 capture(target='tour')
--tour                       -> 0 tour
--verbose help capture       -> 0 help
--mobile list                -> 2 (list rejects --mobile)
--log x.log list             -> 2 (ambiguous abbreviation)
```

No case silently captures an action name as a URL path anymore.
The new tests cover each round 1 rework case and have recorded red-phase proof.
The commit message follows the one-sentence, past-tense convention.

## Defects
None blocking. Non-blocking notes:
1. `run_capture_cli` reads private members: `harness._build_parser`, `harness._actions`, and argparse's `_option_string_actions`.
   Subclasses in the same package already use `_build_parser`, so the coupling stays in-package.
   A small public `ToolHarness` helper (such as `action_names()`) would make it sturdier later.
2. Options placed before an action that the action does not accept now exit 2 (`--mobile list`, `--port 8000 list`).
   The old single parser ignored them.
   This fails loudly rather than misbehaving, a test asserts it, and the CHANGELOG notes the invalid-arguments exit 2.

## Process Gaps
None blocking.
The size overrun (9 files, 641 lines against 7 files, 350 lines) is logged and stays below the 3x sign-off line.
Round 1's suggestion of one backlog note for pinned v1 consumers (`counters.server`, `todos.server`, `template.python`) was optional.
It remains a useful follow-up for the v2.0.0 release.

## Required Rework
None.
