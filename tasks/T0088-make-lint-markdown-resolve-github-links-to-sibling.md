---
id: T0088
owner: ~
needs: []
branch: —
worktree: —
status: ready
started_at: —
ended_at: —
review: agent
preview: none
protocol: standard
---
# T0088: Make lint-markdown resolve GitHub links to sibling checkouts only for configured owners, defaulting to none

## Goals
lint-markdown treats every `github.com/gpellicciotta/...` link as a sibling checkout and checks it on disk.
That owner is hardcoded, so other users' links never get this treatment.
Add a `github-owners` list to the lint configuration, defaulting to empty.
Links of listed owners keep today's sibling-checkout resolution; other GitHub links go through the normal HTTP check.
This repository's own configuration lists `gpellicciotta`, so its lint results do not change.

## Task Execution Steps
- [ ] **[Read]**      Read profiles.py, the link checker in lint.py, and lint-markdown.md's configuration section.
- [ ] **[Implement]** Write failing tests for loading `github-owners` and for owner-dependent link resolution.
- [ ] **[Verify]**    Run the new tests and record their expected failures in validation-proof.md as red-phase proof.
- [ ] **[Implement]** Add `github_owners` to `LintProfile`, use it in the link checker, and add .lint-markdown.json.
- [ ] **[Verify]**    Confirm `lint-markdown rules` and offline check output are unchanged, then run `python scripts/devops.py check`.
- [ ] **[Doc]**       Update lint-markdown.md, migration-v2.md, and CHANGELOG.md.
- [ ] **[Review]**    Obtain review approval of the finished work before completion.

## Execution Log
- [2026-11-10] **[Doc]**
  Companion task file scaffolded at task creation.
