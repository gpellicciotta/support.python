---
task: T0020
round: 1
verdict: rejected
reviewer: "@claude"
reviewed_at: 2026-11-10T00:33:06Z
reviewed_commit: "5be8119"
base_commit: "2e7ca39"
branch: task/T0020-generalize-agent-digest-to-take-markdown-paths-order
---
# Review Findings: Task T0020 (Round 1)

## Summary
The code change meets the technical spec, but the new tool documentation describes behavior that does not exist.
Verified by the reviewer against the worktree source (`PYTHONPATH=src`):
- `python -m pytest tests -q`: 738 passed, 3 skipped, 81 subtests passed.
- `ruff check .` and `ruff format --check .`: clean.
- Integration on a temporary copy of dev-guidelines (369a963):
  - `generate guidelines --digest guidelines/agent-digest.md --skills-dir skills` exited 0 and left `git status --short` empty.
  - `check guidelines ... --skill-index guidelines/general-guidelines.md` exited 0.
- Path collection, index ordering, non-integer `index` (exit 1), missing `PATH` (exit 2), and removed `validate` (exit 2) behave as specified.

The verdict is rejected because `docs/tools/agent-digest.md` is a new, mandatory user-facing document.
Several of its claims are false, and the CLI help does not contradict them.

## Defects
1. **docs/tools/agent-digest.md documents features the code does not implement.**
   Each claim below was probed with a scratch input tree or confirmed by reading `agent_digest.py`:
   - Options table: "`--max-words` ... (`0` disables check)" and "`--max-bytes` ... (`0` disables)".
     `check --max-words 0` reports every sentence as a violation and exits 1.
     `check --max-bytes 0` reports "exceeds the hard budget limit (0 bytes)" and exits 1.
   - Front-Matter Schema: the `skill.references` list of `path`/`source` mappings, and "`skill` keys are restricted to `name`, `description`, and `references`".
     The doc's own YAML example fails: `Unsupported frontmatter syntax at line 7: '      source: ../docs/x.md'`, exit 1.
     `allowed_skill_keys` is `{"name", "description"}`, so `check` would reject `references` anyway.
   - "Files with a `skill` block generate ... configured reference copies": reference copying does not exist.
   - Link Rewriting: "Links targeting another core guideline collapse to a `#<slug>` heading anchor".
     The code emits plain link text (`[B rules](b.md)` becomes `B rules`).
   - Link Rewriting: "Links inside derived skills that match a declared `references` source rewrite to the local `references/...` path": not implemented.
   - Validation Rules: "with no stale directories": `check` never detects skill directories that no longer have a source.
   - Validation Rules: "with unique `skill.name` values": not checked. A duplicate name silently overwrites the earlier skill in `build_skills`.
   - Validation Rules: "Local Markdown links resolve to existing files": not checked.
     `check` only flags relative links in the digest and escaping (`../`, `/`) links in skills.
   - Validation Rules: "Every directive sentence across all input files": the word budget is applied to the generated digest and skills, not to the input files.
   - Validation Rules: "every file under `<skills-dir>/<name>/references/` is declared". The real check is that every non-`SKILL.md` file is linked from `SKILL.md`.
   - Input Collection: "reports the offending file path". The error names only `filepath.name`, so it is ambiguous when several inputs share a basename.

   Non-blocking observations:
   - The startup banner prints `str(Path)`, which gives `- Digest: guidelines\agent-digest.md` on Windows. Prefer `as_posix()` to match the forward-slash convention and the other log lines.
   - `--skill-index` is a global option, so `generate` accepts it and silently ignores it. The spec lists it only for `check`.
   - `DigestHarness.run` repeats the path validation that `action_generate`/`action_check` already do. It swaps `parser.error` for a generator-`throw` lambda, which is fragile.
   - When no link base can be derived, `build_digest`/`build_skills` pass `link_base=None`. `rewrite_markdown_links` then re-runs `derive_link_base` (git subprocesses) for every file.
     Separately, each action calls `collect_input_files`, and so re-reads every file, three times.
   - `agent-files` `ensure_digest` now derives the link base from the current branch, where it used to hardcode `blob/main/`.
     On a non-main or detached checkout of dev-guidelines (e.g. CI PR builds), the derived digest therefore differs from the committed one.
     This follows the spec, but callers in CI will need an explicit `--link-base`.

## Process Gaps
1. The TDD red-phase evidence in `validation-proof.md` does not match the delivered tests.
   None of the failing test identifiers it lists exist in the final `tests/tools/test_agent_digest.py`. Examples:
   - `TestSkillLinkAndOriginDerivation`
   - `TestMergedCheckValidation`
   - `test_collect_paths_orders_by_index_then_cli_discovery_order`
   - `test_missing_path_exits_2`
   - `test_non_md_file_argument_exits_2`

   So the recorded red phase does not prove that the shipped tests failed before implementation.
2. `validation-proof.md` omits the spec-required `generate` integration evidence, the empty `git status --short` after `generate`. The reviewer reproduced it, and it passes.
3. The Execution Log is out of sequence. `[Read]` and `[Doc]` entries were logged after implementation, verification, and the completion-validation failure.
   The TF020 fix turn has no entry describing what was changed.

## Required Rework
1. Rewrite `docs/tools/agent-digest.md` so every statement matches the implemented behavior. Specifically:
   - Remove the `0` disables claims for `--max-words` and `--max-bytes`, or implement them with tests.
   - Remove `references` from the front-matter schema, its example, and the reference-copy and reference-link rewriting bullets.
   - Say that links to other digest-bound guidelines become plain text, not `#<slug>` anchors.
   - Restate the `check` rules to list only what `action_check` verifies:
     - skill and digest freshness;
     - digest byte budget;
     - word budget on the generated digest and skills;
     - allowed front-matter keys (`index`, `skill`; `name`, `description` under `skill`);
     - `--skill-index` coverage;
     - orphan files not linked from `SKILL.md`;
     - relative links in the digest;
     - escaping links in skills.
   - Say that non-integer `index` errors name the file, not its path, or change the code to report the display path.
2. Add proof that the red phase actually ran, against the delivered test identifiers:
   - Re-run the delivered tests against the pre-change module (`2e7ca39`), or
   - record why the earlier red-phase identifiers differ.
3. Add the `generate` integration result (an empty `git status --short`) to `validation-proof.md`.
