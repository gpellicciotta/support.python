---
id: T0081
owner: ~
needs: [T0068, T0069, T0070, T0074, T0075, T0076, T0077, T0078]
branch: —
worktree: —
status: ready
started_at: —
ended_at: —
review: agent
preview: none
protocol: standard
---
# T0081: Specify the configuration file formats and JSON output documents of all five tools under docs/specs/

## Goals
Create `docs/specs/` with one specification per configuration file format and for the tools' JSON output documents.
Cover `.agent-files.json`, `.lint-markdown.json`, the git-repository-backup config, and agent-digest front-matter.
Cover every `--format json` document of the five tools, field by field, with types and examples.
Link the specs from docs/index.md, the tool pages, and the AGENTS.md architecture lines.

## Task Execution Steps
- [ ] **[Read]**      Read every tool's `--format json` code path and configuration loader.
- [ ] **[Doc]**       Write one spec per configuration format under docs/specs/.
- [ ] **[Doc]**       Write the JSON output document spec under docs/specs/.
- [ ] **[Doc]**       Link the specs from docs/index.md, the tool pages, and AGENTS.md.
- [ ] **[Review]**    Obtain review approval of the finished work before completion.

## Execution Log
- [2026-11-10] **[Doc]**
  Companion task file scaffolded at task creation.
