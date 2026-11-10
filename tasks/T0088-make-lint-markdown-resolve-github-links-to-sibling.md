---
id: T0088
owner: "@gemini"
session: antigravity-20261110-cad2c6
needs: []
branch: task/T0088-make-lint-markdown-resolve-github-links-to-sibling
worktree: .plan/work/T0088-make-lint-markdown-resolve-github-links-to-sibling
status: active
started_at: "2026-11-10T22:30:48Z"
ended_at: —
review: agent
preview: none
protocol: standard
usage:
  worker: {turns: 4, duration_s: 3276.0, input: 2196936, output: 163952, cache_read: 57342886}
work_duration: 1526.6
review_status: pending
review_round: 1
---
# T0088: Make lint-markdown resolve GitHub links to sibling checkouts only for configured owners, defaulting to none

## Goals
lint-markdown treats every `github.com/gpellicciotta/...` link as a sibling checkout and checks it on disk.
That owner is hardcoded, so other users' links never get this treatment.
Add a `github-owners` list to the lint configuration, defaulting to empty.
Links of listed owners keep today's sibling-checkout resolution; other GitHub links go through the normal HTTP check.
This repository's own configuration lists `gpellicciotta`, so its lint results do not change.

## Task Execution Steps
- [x] **[Read]**      Read profiles.py, the link checker in lint.py, and lint-markdown.md's configuration section.
- [x] **[Implement]** Write failing tests for loading `github-owners` and for owner-dependent link resolution.
- [x] **[Verify]**    Run the new tests and record their expected failures in validation-proof.md as red-phase proof.
- [x] **[Implement]** Add `github_owners` to `LintProfile`, use it in the link checker, and add .lint-markdown.json.
- [x] **[Verify]**    Confirm `lint-markdown rules` and offline check output are unchanged, then run `python scripts/devops.py check`.
- [x] **[Doc]**       Update lint-markdown.md, migration-v2.md, and CHANGELOG.md.
- [ ] **[Review]**    Obtain review approval of the finished work before completion.

## Execution Log
- [2026-11-10] **[Doc]**
  Companion task file scaffolded at task creation.

- [2026-11-10] **[Read]**
  Read profiles.py, the link checker in lint.py, and lint-markdown documentation.

- [2026-11-10] **[Implement]**
  Wrote failing tests for loading github-owners and owner-dependent link resolution.

- [2026-11-10] **[Verify]**
  Ran new tests and recorded expected failures in validation-proof.md as red-phase proof.

- [2026-11-10] **[Implement]**
  Added github_owners to LintProfile, updated link checker, and added .lint-markdown.json.

- [2026-11-10] **[Verify]**
  Verified lint-markdown rules, offline check output, and full devops check passing cleanly.

- [2026-11-10] **[Doc]**
  Updated lint-markdown.md, migration-v2.md, and CHANGELOG.md for github-owners.

- [2026-11-10] **[Review]**
  Round 1 requested (mode: agent).

