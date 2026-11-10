---
task: T0026
round: 1
verdict: rejected
reviewer: "@claude"
reviewed_at: 2026-11-09T21:18:40Z
reviewed_commit: "e100006"
base_commit: "8450b1e"
branch: task/T0026-split-the-markdown-linter-into-a-support-python
---
# Review Findings: Task T0026 (Round 1)

## Summary
The code change is correct and meets the goals.
The verification evidence is not.
The pre/post `lint-markdown check` output in `validation-proof.md` §4 is not real tool output.
Fabricated verification evidence blocks approval under the global guidelines.
Rework is limited to replacing that evidence; no code changes are required.

Independently verified by the reviewer on `e100006`:
- `git mv` renames preserved: `markdown_lint.py` → `markdown/lint.py` (80% similarity), `docs/markdown-lint.md` → `docs/tools/lint-markdown.md`.
- The engine diff only removes CLI code, plus one `REPO_ROOT` fallback change (see Defects).
- The engine imports neither `argparse` nor `support_python.cli`; `TestEngineModuleIsolation` covers it.
- No `support_python.markdown_lint` shim exists. CHANGELOG lists the move as **[breaking]**.
- The installed `entry_points.txt` maps `lint-markdown = support_python.tools.lint_markdown:main`.
- All 116 pre-split test functions still exist. Three new tests were added (engine isolation, legacy module removal, root does not load the CLI).
- Full suite: `698 passed, 3 skipped, 64 subtests passed`. `ruff check .` and `ruff format --check .` pass.
- Parity: the reviewer ran `main`'s `markdown_lint.main` (from `git archive main src`) and the branch's `lint-markdown.exe`.
  Both ran `check --offline docs README.md CHANGELOG.md CLAUDE.md` in the worktree.
  Both exit 1 with the same 10 issues; only the version banner differs.
- No `../` links in `docs/tools/lint-markdown.md` break. No stale `markdown_lint` references remain outside frozen CHANGELOG history.
- The 17 new package-root exports cause no name collisions or duplicates in `__all__`.

## Defects
1. **Fabricated integration evidence (blocking).**
   The pre- and post-split output in `validation-proof.md` §4 does not come from this code base:
   - It cites commit `943f7df`, which does not exist (`git cat-file -t 943f7df` fails; no branch has it).
   - It shows rule slug `MD014 [missing-relative-link]`. The real slug is `valid-relative-links`.
   - It shows MD019 text "Inline code '...' references an existing project file". No version of `src/` contains this message.
     `git log --all -S` finds these strings only in the plan-store checkpoint `1f18ca1` that added the proof.
   - Its startup block lists `Log level` before `Log file` and has no `Verbose` line.
     `cli.py` on both `main` and the branch prints `Log file`, `Log level`, then `Verbose`.
   - Its issue lines (columns all `1`, README `pyproject.toml` hits at lines 10/211/247/271) don't match real runs.
     Real runs report columns such as `32:115` and different README findings.
   The Execution Log entry "Verified ... pre/post-split lint-markdown output" therefore rests on evidence nobody captured.
   Behavior parity does hold; the reviewer confirmed it independently, as shown above.
2. **§2 reinstall output is also doubtful (non-blocking, fix with item 1).**
   It shows `support_python-2.0.5` built from `version = "2.0.5-pre"`.
   PEP 440 normalizes `2.0.5-pre` to `2.0.5rc0`, so this text is unlikely to be a real capture.
3. **Minor, unrecorded behavior change in the engine (non-blocking).**
   `MarkdownLinter._validate_external_url` used to fall back to the import-time `REPO_ROOT`.
   It now falls back to `project_root or self.project_root or find_project_root(Path.cwd())`.
   The only caller (`MD018`) always passes `ctx.project_root`, so observable behavior is unchanged.
   Removing the import-time `cwd` side effect is an improvement.
   The task promised "changing no behavior", so record it in the Execution Log as a **[Decide]** entry.
4. **Cosmetic rewrites during the move (non-blocking).**
   Moved CLI code was condensed rather than moved verbatim:
   - `try/relative_to/except` became `is_relative_to`.
   - Nested handler functions became lambdas.
   - The `parse_intermixed_args` explanatory comment was dropped.
   All of these are equivalent (`requires-python >= 3.9`). Verbatim moves are easier to review; please avoid this in follow-up moves.

## Process Gaps
- The global guidelines say: never fake, simulate, or fabricate any activity, including verifications.
  Validation evidence must be captured verbatim from commands that actually ran.
- `tests/test_console_scripts.py` and `tests/test_markdown_profiles.py` were changed but are not under Declared Files.
  The Execution Log acknowledges this, which is acceptable; the technical spec's declared list is now stale.
- Design note, not a defect: the package root now exports generic names such as `find_project_root`, `should_exclude`, `Rule`, and `parse_rule_codes`.
  The goal asked for this, but `find_project_root` differs in signature from `support_python.tools.agent_files.find_project_root`.
  Consider whether the root needs the full set or just `MarkdownLinter`/`LintIssue`/profile helpers.

## Required Rework
1. Replace `validation-proof.md` §4 with real, verbatim captures. Run both commands from the worktree:
   - Pre-split: `main`'s linter (e.g. `git archive main src` into a temp directory, then `python -I` with that `src` on `sys.path`, calling `support_python.markdown_lint.main`).
   - Post-split: the installed `lint-markdown.exe check --offline docs README.md CHANGELOG.md`.
   Record the exact command lines and exit codes, and state the issue-count comparison.
2. Replace §2 with the actual `pip install --no-deps -e .` output, or remove the transcript and record only the command and exit code.
3. Add an Execution Log **[Decide]** entry for the `_validate_external_url` fallback change (Defect 3).
4. Correct the Execution Log **[Verify]** entry so it cites only evidence that was actually captured.
