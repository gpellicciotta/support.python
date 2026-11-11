---
id: T0105
owner: "@claude"
session: claude-20261111-0be961
needs: []
branch: task/T0105-rewrite-github-links-ending-in-docs-guidelines-name
worktree: .plan/work/T0105-rewrite-github-links-ending-in-docs-guidelines-name
status: active
started_at: "2026-11-11T07:04:43Z"
ended_at: —
review: agent
preview: none
protocol: standard
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
- [ ] **[Review]**    Obtain review approval of the finished work before completion.

## Execution Log
- [2026-11-10] **[Doc]**
  Companion task file scaffolded at task creation.
