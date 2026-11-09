---
task: T0023
round: 1
verdict: rejected
reviewer: "@claude"
reviewed_at: 2026-11-09T19:08:22Z
reviewed_commit: "c2ceed5"
base_commit: "08b4ecf"
branch: task/T0023-record-adr-0003-on-tool-library-and-script
---
# Review Findings: Task T0023 (Round 1)

## Summary
ADR-0003 covers all nine technical-spec decisions and the three alternatives.
ADR-0001's partial supersession, the `v2.0.0-pre` heading, and the `pyproject.toml` version are correct.
`docs/requirements.md` reads correctly as target requirements.
The work is rejected because `CLAUDE.md` and `docs/index.md` describe ADR-0003's future state as current behavior.
The spec's completion lint command also fails, and the evidence narrowed it without recording the deviation.

Checks run by the reviewer on `c2ceed5`, using the worktree `src/`:
- `python -m pytest -q`: 734 passed, 3 skipped, 64 subtests passed.
- `ruff check .` passed, and `ruff format --check .` reported 98 files already formatted.
- `support-python lint markdown check --offline docs CHANGELOG.md CLAUDE.md` (the spec command): exit 1, with 3 MD019 issues.

## Defects
1. `CLAUDE.md` presents planned tools as shipped, which contradicts the code and `README.md`.
   - Line 12 says the package is a "suite of five standalone CLI tools".
     `[project.scripts]` defines only `support-python` and `processes`.
     No `agent-digest` tool exists in this repository.
   - Line 31 says agent-files is "exposed via `agent-files`", and line 38 says linting is "exposed via `lint-markdown`".
     Both are currently `support-python agent-files` and `support-python lint markdown`, as `README.md` documents.
   - The `support-python greet` demo command was dropped from Commands, but it still exists and `README.md` documents it.
   - The goal only asked to replace the stale pre-1.0 semver note.
     The other rewrites go beyond that goal and add drift, which the project's conventions treat as a bug.
2. `docs/index.md` makes entries contradict the code and the README sections they link to.
   - Line 13 says backup is "exposed via `git-repository-backup`", but the code exposes `support-python backup`.
   - Line 19 says "exposed via `lint-markdown`", but the linked README section documents `support-python lint markdown`.
   - Line 20 names a `.agent-files.json` schema and the `agent-files` command.
     The code reads `agent-files.json` and exposes `support-python agent-files`.
   - The DevOps entry advertises `DevopsCli`, project adapters, and `steps`/`services`/`release`/`projects`/`cli` submodules.
     None of these exist, and its README anchor documents only the current managers.
3. Minor: ADR-0003 links "each consumer repository's" `devops.py` to this repository's `../../scripts/devops.py`.
   This happens on lines 11, 73, and 88, so the link points readers at the wrong file.
   Use a code span such as `scripts/devops.py` for consumer repositories.
   Keep the link on line 41, which really does mean this repository's script.

## Process Gaps
1. The spec's completion check (`... lint markdown check --offline docs CHANGELOG.md CLAUDE.md` exits 0) fails.
   `docs/devops.md` lines 11, 110, and 112 have pre-existing MD019 issues.
   `validation-proof.md` ran a narrower six-file command instead and still reports it as passing.
   The deviation appears in neither the Execution Log nor a `**[Decided]**` note.
2. `validation-proof.md` cites `.venv/Scripts/support-python`, but the worktree has no `.venv`.
   Its banner, `lint-markdown v1.3.6-pre+08b4ecf`, shows the run used the base-commit install, not the branch.
   The result is equivalent here because no code changed, but the evidence misstates what ran.

## Required Rework
1. Revert the non-semver rewrites in `CLAUDE.md`, or rephrase them to match current entry points.
   Planned tools may appear only if clearly labeled as planned in ADR-0003.
   Keep the semver-note replacement.
2. Make `docs/index.md` entries match current commands and config names (`support-python backup`, `support-python lint markdown`, `support-python agent-files`, `agent-files.json`).
   Drop the claims about the unbuilt `DevopsCli` and its submodules.
   The ADR-0003 index entry may keep describing the decision.
3. Replace the consumer-repository `devops.py` links in ADR-0003 (lines 11, 73, and 88) with code spans.
4. Run the spec's exact completion lint command from the branch code.
   Either fix the three MD019 issues in `docs/devops.md` with a recorded scope amendment, or record the deviation and its reason in the Execution Log.
   Regenerate `validation-proof.md` with the commands actually run.
