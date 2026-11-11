---
id: T0081
owner: "@claude"
session: claude-20261111-d032f1
needs: []
branch: task/T0081-specify-the-configuration-file-formats-and-json-output
worktree: .plan/work/T0081-specify-the-configuration-file-formats-and-json-output
status: active
started_at: "2026-11-11T01:45:13Z"
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
- [x] **[Read]**      Read every tool's `--format json` code path and configuration loader.
- [x] **[Doc]**       Write one spec per configuration format under docs/specs/.
- [x] **[Doc]**       Write the JSON output document spec under docs/specs/.
- [x] **[Doc]**       Link the specs from docs/index.md, the tool pages, and AGENTS.md.
- [ ] **[Review]**    Obtain review approval of the finished work before completion.

## Execution Log
- [2026-11-10] **[Doc]**
  Companion task file scaffolded at task creation.

- [2026-11-11] **[Doc]**
  Added docs/specs/ with five specs and linked them from the index, tool pages, and AGENTS.md; 1200 tests passed using the main checkout venv.

