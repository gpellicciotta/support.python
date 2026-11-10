---
task: T0052
round: 1
verdict: approved
reviewer: "@claude-reviewer"
reviewed_at: 2026-11-10T07:55:28Z
reviewed_commit: "a3bf8f2"
base_commit: "a3bf8f2"
---
# T0052 Review Findings, Round 1

Verdict: approve.
No defects.
Three optional nits follow.

## Checks
- Content: all eight moved README sections from `git show HEAD:README.md` are in the five tutorials.
  Every statement, bullet, and example keeps its meaning.
  Some long bullets were split into sub-lines without changing their meaning.
- Re-exports: every symbol in `git`, `files`, `locking`, `durations`, `ratelimit`, and `markdown.tables` is exported from `support_python`.
  The same holds for `MarkdownLinter`, `LintIssue`, `RuleRegistry`, `LintProfile`, and `load_profile`.
- `process-management.md` imports from `support_python.processes` and makes no root re-export claim.
  That is correct, because several process helpers are not exported from `support_python`.
- Linter example: I ran the `markdown.md` snippet from a scratch directory.
  It reports `3:17 MD011 Line contains trailing whitespace`, and `fix_content` returns `b"# Notes\n\nTrailing space\n"` as the comment says.
- `load_profile` accepts the built-in names `default` and `dev-guidelines` and rejects any other name with `ValueError`.
  Given a path, it also loads a `.lint-markdown.json` file.
- Links: all relative links in the five tutorials resolve.
  The README and `docs/index.md` anchors `#locks`, `#atomic-text-files`, `#table-helpers`, `#linter`, and `#task-rate-limiter` match tutorial headings.
  `lint-markdown.md#rule-plugins` also resolves.
- Stale anchors: no `.md` or `.py` file outside `.venv` and `.plan` links to a removed README anchor.
- Completion check: `.venv/Scripts/lint-markdown check --offline README.md docs/index.md docs/tutorials docs/tools/processes.md` passed with exit code 0 on 14 files.
- Version: `pyproject.toml` `2.0.34-pre` matches the top `CHANGELOG.md` heading.
- Task file: `plan tasks validate` passed.

## Findings

### N1 (nit): legacy config note dropped from README
- Location: `README.md:152`.
- The old Markdown linter paragraph mentioned the legacy `.markdown-lint.json` file and linked `tools/lint_markdown.py`.
- The new summary line drops both.
- The legacy fallback is still documented in `docs/tools/lint-markdown.md:41`, which the README links.
- Fix (optional): write "reads `.lint-markdown.json` (or legacy `.markdown-lint.json` with a warning)".

### N2 (nit): processes examples not copied word for word
- Location: `docs/tools/processes.md:36-42`.
- Two README examples are not there literally: `processes list --cwd . --format json` and `processes kill 1234 5678 --force`.
- Equivalent forms already exist on lines 37-39.
- Fix (optional): add both lines to match the README.

### N3 (nit): CLI source link dropped
- Location: `docs/tutorials/process-management.md:5`.
- The original README linked the CLI source `tools/processes.py`, and the tutorial does not.
- Fix (optional): add "([tools/processes.py](../../src/support_python/tools/processes.py))" after "The `processes` command-line tool".
