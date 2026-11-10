---
id: T0061
owner: "@claude-code"
needs: []
branch: —
worktree: —
status: completed
started_at: "2026-11-10T11:02:50Z"
ended_at: "2026-11-10T11:21:05Z"
review: agent
preview: none
protocol: standard
review_status: approved
review_round: 1
reviewed_by: "@giova"
completion-commit: 934bc9fcdc17ef8769a8663245156abf93f7d6f9
---
# T0061: Support skill references in agent-digest front-matter, copying listed files into skills with link rewriting and checks

## Goals
Let a guideline with a `skill:` block list extra files under `skill.references`.
`agent-digest generate` copies each listed file into `<skills-dir>/<name>/`, so skills need no hand-authored files.
`agent-digest check` verifies the copies and rejects unlisted files in skill directories.
Reference files under source directories never become digest or skill sources.
Specification: [technical-spec.md](T0061-support-skill-references-in-agent-digest-front-matter/technical-spec.md).
Unblocks dev-guidelines task T0195.

## Task Execution Steps
- [x] **[Read]**      Read agent_digest.py link rewriting, collection, build_skills, and orphan check code.
- [x] **[Implement]** Author failing unit and integration tests for references in test_agent_digest.py.
- [x] **[Verify]**    Run the new tests and record their failure output before implementing.
- [x] **[Implement]** Accept the references key and collect referenced files in front-matter parsing.
- [x] **[Implement]** Copy references in generate, with link rewriting, dry-run output, and collection exclusions.
- [x] **[Implement]** Add check rules for missing, stale, escaping, and unlisted reference files.
- [x] **[Verify]**    Confirm the new tests and the full suite pass, and run ruff.
- [x] **[Doc]**       Update docs/tools/agent-digest.md and CHANGELOG.md.
- [x] **[Review]**    Obtain review approval of the finished work before completion.

## Execution Log
- [2026-11-10] **[Doc]**
  Companion task file scaffolded at task creation.

- [2026-11-10] **[Decided]**
  Specification agreed with the user in conversation; see technical-spec.md.

- [2026-11-10] **[Implement]**
  Added skill.references: parsing, collection exclusion, generate copies, check rules, docs, and fixture conversion.
  - Fixture reference moved to guidelines/references.

- [2026-11-10] **[Decided]**
  Compare Markdown reference copies ignoring CRLF versus LF, since Windows checkouts convert line endings.

- [2026-11-10] **[Decided]**
  check JSON always includes skills[].files; files not listed now fail as unlisted-file.

- [2026-11-10] **[Decided]**
  Size note: 563 lines exceeds the typical line; tests and the fixture reference account for about 320 lines.

- [2026-11-10] **[Review]**
  Round 1 requested (mode: agent).

- [2026-11-10] **[Review]**
  Round 1 approved by @giova.

- [2026-11-10] **[Verify]**
  Recorded task outcomes.
  - Files touched: 6.
  - Lines touched: 592.
  - Reopenings: 0.

- [2026-11-10] **[Complete]**
  Task completed successfully.

