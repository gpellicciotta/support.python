---
id: T0105
owner: "@claude"
session: claude-20261111-0be961
needs: []
branch: task/T0105-rewrite-github-links-ending-in-docs-guidelines-name
worktree: .plan/work/T0105-rewrite-github-links-ending-in-docs-guidelines-name
status: completed
started_at: "2026-11-11T07:04:43Z"
ended_at: "2026-11-11T07:07:37Z"
review: agent
preview: none
protocol: standard
usage:
  worker: {turns: 4, duration_s: 215.0, input: 88, output: 14366, cache_read: 1973004, cache_write: 79656}
  review: {turns: 2, duration_s: 48.8, input: 20, output: 2562, cache_read: 328506, cache_write: 45516}
work_duration: 174.4
review_status: approved
review_round: 1
reviewed_by: "@claude-2"
completion-commit: efd2ccfc3bbbd3dfd9545c9a8f341a879090cf0e
---
# T0105: Rewrite GitHub links ending in docs/guidelines/{{name}}.md to the skill reference, as links ending in skills/{{name}}/SKILL.md are today

## Goals
plan moves its bundled skill sources to `docs/guidelines/{{name}}.md`, so `agent-digest` stops recognizing links to them.
Rewrite `https://github.com/...` links ending in `/docs/guidelines/{{name}}.md` to ``the `{{name}}` skill``, like `/skills/{{name}}/SKILL.md` links today.
Keep the existing rule working for both forms.
Document the convention in `docs/tools/agent-digest.md`.
Specifications: [technical-spec.md](T0105-rewrite-github-links-ending-in-docs-guidelines-name/technical-spec.md).

## Task Execution Steps
- [x] **[Decide]**    Choose between the path convention and an explicit external-skill option.
- [x] **[Implement]** Author a failing test for the docs/guidelines URL form.
- [x] **[Verify]**    Run the new test and record its failure output.
- [x] **[Implement]** Extend the link rewriting to the new URL form.
- [x] **[Verify]**    Run the affected tests and the integration scenario.
- [x] **[Doc]**       Update docs/tools/agent-digest.md and CHANGELOG.md.
- [x] **[Review]**    Obtain review approval of the finished work before completion.

## Execution Log
- [2026-11-10] **[Doc]**
  Companion task file scaffolded at task creation.

- [2026-11-11] **[Verify]**
  Completion validation found 3 errors; pending fix turn 1 of 2.
  - TF018.
  - TF019.
  - TF020.

- [2026-11-11] **[Decided]**
  Chose the path convention, limited to github.com URLs, over an explicit external-skill option.

- [2026-11-11] **[Implement]**
  Added a failing test for docs/guidelines GitHub URLs and confirmed it failed.

- [2026-11-11] **[Verify]**
  Recorded the failure: the link stayed unrewritten in the digest.

- [2026-11-11] **[Implement]**
  Extended link rewriting in agent_digest.py to the docs/guidelines URL form.

- [2026-11-11] **[Verify]**
  Ran 54 digest tests, ruff, and a generate then check scenario; all passed.

- [2026-11-11] **[Doc]**
  Updated agent-digest.md and CHANGELOG.md.

- [2026-11-11] **[Review]**
  Round 1 requested (mode: agent).

- [2026-11-11] **[Review]**
  Round 1 approved by @claude-2: The change meets the goals.
  - Findings: [review-findings-1.md](T0105-rewrite-github-links-ending-in-docs-guidelines-name/review-findings-1.md).

- [2026-11-11] **[Complete]**
  Task completed successfully.

