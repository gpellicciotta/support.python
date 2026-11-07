---
task: T0016
round: 1
verdict: rejected
reviewer: "@claude"
reviewed_at: 2026-11-07T18:50:51Z
reviewed_commit: "9b93ace"
base_commit: "98420d2"
branch: task/T0016-refactor-the-ported-markdown-linter-into-registered-rule
---
# Review Findings: Task T0016 (Round 1)

## Summary
The rule split, registry, and JSON profile loading work.
I ran the full suite in the worktree (pytest resolves `src` relative to the worktree): 752 passed, 3 skipped.
`ruff check` and `ruff format --check` are clean.
The ported tests are unchanged; only `tests/test_markdown_profiles.py` was added.
The package layout, however, is hacky and the documented default-profile behavior is wrong.
I did not re-run the T0014 output parity check against dev-guidelines. I rely on the Execution Log for it.

## Defects
1. **Module/package name collision handled by an import hack.**
   `src/support_python/markdown.py` (table formatting) still exists next to the new `src/support_python/markdown/` package.
   The package shadows the module, so `markdown.py` is unreachable through normal imports.
   `markdown/__init__.py` loads it with `importlib.util.spec_from_file_location`, injects `support_python._markdown_tables` into `sys.modules`, and re-exports names by hand.
   It also carries a mid-file `import sys` and an `assert` for type narrowing.
   This breaks the "simplicity over ingenuity" guideline and leaves a dead module on the import path.
   It also makes the table helpers dependent on a sibling file path.
   README.md:477 and CLAUDE.md:49 still link `markdown.py` as the table helper module.
2. **The no-config behavior contradicts the "default" profile and the docs.**
   `docs/markdown-lint.md` says that without a config the CLI falls back to `default`, which leaves `MD015` and historical-task exemptions off.
   Verified in a temp repo with `a.md` containing `## Sub`, a blank line, then body text:
   - `lint markdown a.md` (no config, no profile) reports `MD015`, which is dev-guidelines behavior.
   - `--profile default` reports nothing.
   - Adding `.markdown-lint.json` with only `{"disable": ["MD018"]}` silently turns `MD015` off, because the base becomes `DEFAULT_PROFILE`.
   Adding an unrelated config key therefore changes results.
   `MarkdownLinter(profile=None)` also enables all rules and historical exemptions.
   Keeping the legacy behavior may be intended for backward compatibility with the ported tests.
   If so, it must be a named, documented behavior, and the config and no-config paths must agree.

## Process Gaps
- The docs describe the fallback incorrectly (see defect 2), so documentation does not match behavior.
- No test covers "no config, no profile" against the `default` profile, or a config file without a `profile` key. This is why defect 2 went unnoticed.
- README.md and CLAUDE.md architecture entries were not updated for the new package.
- `docs/index.md` was not updated to link `docs/markdown-lint.md`. I did not verify whether an existing link covers it.

## Required Rework
1. Move `markdown.py` into the package (for example `markdown/tables.py` via `git mv`).
   Re-export its names with a normal `from support_python.markdown.tables import ...`.
   Remove the `importlib` and `sys.modules` hack, and keep `tests/test_markdown.py` passing.
   Update README.md, CLAUDE.md, and any other links.
2. Make profile selection consistent and documented:
   - Choose one behavior for "no config and no `--profile`".
   - Choose the base profile for a config file that has no `profile` key.
   - Make both paths agree, make the docs state it, and add tests for both paths.
   - Preferably make `default` mean the generic profile everywhere, and require `--profile dev-guidelines` (or a config) for `MD015`.
   - If legacy all-rules behavior is kept for the programmatic API, document it.
3. Re-run ruff and the full suite after the changes, and record the evidence.
