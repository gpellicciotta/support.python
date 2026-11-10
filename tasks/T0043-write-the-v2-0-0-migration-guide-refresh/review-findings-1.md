---
task: T0043
round: 1
verdict: rejected
reviewer: "@claude-2"
reviewed_at: 2026-11-10T04:57:00Z
reviewed_commit: "741df41"
base_commit: "65b2446"
branch: task/T0043-write-the-v2-0-0-migration-guide-refresh
---
# Review Findings: Task T0043 (Round 1)

## Summary
Most of the work is solid.
The migration guide covers every `**[breaking]**` entry in the v2.0.28-pre CHANGELOG section.
The CLAUDE.md refresh is accurate, and the README and docs index link the guide.
All 13 consumer Backlog tasks exist, sit under `## Backlog`, and carry the spec wording plus the v2.0.0 dependency.

Checks I ran on `741df41`:
- `lint-markdown check --offline` on the five declared files: exit 0.
- `ruff check .` and `ruff format --check .`: clean.
- `pytest`: 1041 passed, 3 skipped, exit 0.
- The guide's API claims: removed root names, module moves, patch targets, `GradleProject` kwargs, `ToolHarness.format_version()`.
- The guide's devops example: built `DevopsCli` with `add_services` and `set_deploy`, giving the expected 14 actions.
- The v1.x claims, checked against tag `v1.3.5`: `greet`, `format_support_message`, `--fix`, `update`/`diff`/`sync` aliases, config paths.

I rejected the work for three reasons.
It edited a frozen CHANGELOG section.
It skipped the `-pre` patch bump.
Two blanket CLI claims in the guide are false for `agent-digest`.

## Defects
1. **Frozen CHANGELOG section edited (`CHANGELOG.md`, `## v1.3.0 [2026-11-07]`).**
   Five finalized v1.3.0 bullets were rewritten.
   change-management-guidelines say: "Finalized version entries in `CHANGELOG.md` are strictly immutable; never edit, add, or delete entries once finalized."
   The edits also falsify history by changing link text, not just targets.
   For example, v1.3.0 now claims it ported `MarkdownLinter` "in lint.py" instead of `markdown_lint.py`.
   Other edits: `devops.py` became `steps.py`, and `backup.py` became `git_repository_backup.py`.
   The Execution Log records this as a decision made to satisfy the completion check.
   That check conflicts with the immutability rule, so it needed a `**[Feedback Needed]**` escalation, not a silent edit.
2. **Active `-pre` heading not bumped (`CHANGELOG.md`, `pyproject.toml`).**
   The commit adds a `Docs:` bullet under `## v2.0.28-pre` but keeps the heading and `version = "2.0.28-pre"`.
   The guidelines require a patch bump of the active `-pre` heading for each landed documentation update.
   Each prior task did this: T0044 `2.0.27-pre`→`2.0.28-pre`, T0042 `2.0.26-pre`→`2.0.27-pre`, T0041 `2.0.25-pre`→`2.0.26-pre`.
   Expected: `## v2.0.29-pre`, with `pyproject.toml` matching.
3. **False blanket CLI claims in `docs/migration-v2.md` (`## Verbs and Options`).**
   The guide states ADR-0003 intent as v2.0.0 fact:
   - "Every `list` and `check` action accepts `--format text|json`": `agent-digest check ... --format json` exits 2 with `unrecognized arguments: --format`.
   - "Every writing action accepts `--dry-run`": `agent-digest help generate` lists no `--dry-run`, and `agent_digest.py` has no dry-run handling.
   A consumer who follows the guide in CI gets exit 2.
   The guide's job is to map v1.x to v2.0.0 precisely, so these lines are defects.

## Process Gaps
- The worker resolved a conflict between the spec's completion check and a guideline rule alone.
  The user CLAUDE.md requires `**[Feedback Needed]**` when an unattainable gate forces a trade-off.
- The `Verify` step checked lint only.
  Nobody checked the guide's CLI claims against the tools' real `help` output.
  Running each tool's `help <action>` would have caught defect 3.
- Minor, no rework needed: `docs/index.md:49` fails online MD018 (a dev-guidelines link to a missing file).
  The completion check is offline, so this was already present and is not caused by this task.

## Required Rework
1. Revert every edit inside `## v1.3.0 [2026-11-07]` in `CHANGELOG.md`.
   Raise the lint-versus-immutability conflict with the user as `**[Feedback Needed]**`.
   Example options: exclude frozen sections from MD018, or drop `CHANGELOG.md` from the completion check.
   Do not pick an option without the user's answer.
2. Bump the active heading to `## v2.0.29-pre`, and set `pyproject.toml` `version` to `2.0.29-pre`.
3. Fix `docs/migration-v2.md` `## Verbs and Options` so its claims match v2.0.0.
   Either scope the bullets to the tools that support the options, or name the `agent-digest` exceptions.
   Optionally, record a Backlog task in this repository for the `agent-digest` gap against ADR-0003.
4. Re-run `lint-markdown check --offline` on the declared files.
   Record the result, and the user's resolution of item 1, in the validation proof.
