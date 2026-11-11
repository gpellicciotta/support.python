---
id: T0081
owner: "@claude"
session: claude-20261111-d032f1
needs: []
branch: task/T0081-specify-the-configuration-file-formats-and-json-output
worktree: .plan/work/T0081-specify-the-configuration-file-formats-and-json-output
status: completed
started_at: "2026-11-11T01:45:13Z"
ended_at: "2026-11-11T01:51:17Z"
review: agent
preview: none
protocol: standard
usage:
  worker: {turns: 4, duration_s: 525.6, input: 184, output: 48624, cache_read: 8561418, cache_write: 245066}
  review: {turns: 2, duration_s: 112.4, input: 40, output: 6448, cache_read: 882584, cache_write: 83532}
work_duration: 363.7
review_status: approved
review_round: 1
reviewed_by: "@claude-2"
completion-commit: f9bc47f9138dd038e7def5ca0bcec3ce85eec649
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
- [x] **[Review]**    Obtain review approval of the finished work before completion.

## Execution Log
- [2026-11-10] **[Doc]**
  Companion task file scaffolded at task creation.

- [2026-11-11] **[Doc]**
  Added docs/specs/ with five specs and linked them from the index, tool pages, and AGENTS.md; 1200 tests passed using the main checkout venv.

- [2026-11-11] **[Verify]**
  Completion validation found 1 errors; pending fix turn 1 of 2.
  - TF020.

- [2026-11-11] **[Read]**
  Read the --format json code paths and configuration loaders of all five tools.

- [2026-11-11] **[Doc]**
  Linked the specs from docs/index.md, the five tool pages, and AGENTS.md; added a CHANGELOG.md entry.

- [2026-11-11] **[Review]**
  Round 1 requested (mode: agent).

- [2026-11-11] **[Review]**
  Round 1 approved by @claude-2: Five specs under docs/specs/ cover all config formats and every `--format json` document.
  - Findings: [review-findings-1.md](T0081-specify-the-configuration-file-formats-and-json-output/review-findings-1.md).

- [2026-11-11] **[Complete]**
  Task completed successfully.

