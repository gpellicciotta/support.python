---
task: T0017
round: 1
verdict: rejected
reviewer: "@claude"
reviewed_at: 2026-11-07T18:05:35Z
reviewed_commit: "62c868b"
base_commit: "15e4dea"
branch: task/T0017-parameterize-the-ported-agent-files-sync-with-configurable
---
# Review Findings: Task T0017 (Round 1)

## Summary
The code meets the functional goals; the rejection is for documentation drift only.

Verified:
- Full suite passes (`747 passed, 3 skipped`); `ruff check` and `ruff format --check` are clean.
- The JSON loader, CLI flags, and `ToolRegistry` work. Invalid and missing configs exit 2 with an indicator-formatted error.
- The second-marker and added-tool tests cover the completion check.
- `agent-files sync --dry-run` against `dev-guidelines` is byte-identical (apart from the version header) between `main` and this branch. Behavior is unchanged.
- The release flow follows `docs/devops.md`: `v1.3.0 [2026-11-07]` is frozen, `v1.3.1-pre` is added, and `pyproject.toml` matches.

## Defects
1. **README drift (project rule: "treat drift as a bug").**
   - `README.md` lines 507-512 (Agent files sync) still show the pre-T0017 usage.
   - It omits `--config`, `--repo-root`, `--digest`, `--skills-dir`, `--marker*`, `--manifest-source`, `--legacy-skill`.
   - It does not mention `agent-files.json` or `docs/agent-files.md`.
2. **`docs/agent-files.md` misdescribes `--legacy-skill`.**
   - It says the flag "appends" a name.
   - `load_agent_files_config` replaces the JSON `legacy_skill_names` list with the flag values.
   - Fix the doc or the behavior.
3. **New doc not discoverable.** `docs/index.md` links only to the README anchor, not `docs/agent-files.md`. `CLAUDE.md` "Architecture" omits `agent_files_config.py`.
4. **Cosmetic help glitch.** The `--digest, --digest-path PATH` option label is too long for the help column, so it runs into the description: `--digest, --digest-path PATHguidelines digest file path override`.

## Process Gaps
- The Execution Log claims an "empty dev-guidelines dry-run diff".
  - On review the dry-run is not empty: the installed global files differ from the current `dev-guidelines` digest and skills.
  - The output is identical to the `main` baseline, so the claim is not reproducible as worded.
  - Restate it as "identical to baseline".
- Size: 720 lines against a 300-line estimate (2.4x), below the 3x sign-off line. The undeclared `pyproject.toml` edit was logged.

## Required Rework
1. Update `README.md` Agent files sync section: new flags, `agent-files.json`, link to `docs/agent-files.md`.
2. Correct the `--legacy-skill` description in `docs/agent-files.md` (replace vs. append).
3. Link `docs/agent-files.md` from `docs/index.md` and add `agent_files_config.py` to the `CLAUDE.md` architecture list.
4. Fix the help label for `--digest` (for example, a single `--digest` flag with `--digest-path` as a hidden alias, or a shorter label).
5. Correct the Execution Log wording on the dry-run diff.
