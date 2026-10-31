---
name: standard
description: Standard full task protocol with companion task file and auto isolation in automated runs.
worktree: auto
branch: auto
task_file: true
integration: squash
commit: auto
push: none
cleanup: auto
review: agent
preview: none
---

# Standard Task Execution Protocol

You are executing task **{{task-id}}**: {{description}}

## Environment
- Working Directory: {{work-dir}}
- Task File: {{task-file}}
- Target Branch: {{branch}}
- Target Worktree: {{worktree}}

## Workflow
1. {{isolation-instructions}}
2. Inspect git status and any checkpoint stashes from previous turns.
3. Review goals, execution steps, and acceptance criteria in {{task-file}}.
4. Implement the planned changes cleanly and keep modifications scoped to declared files.
5. Run automated test suites and verify all checks pass cleanly.
6. {{completion-instruction}}
7. End the turn immediately once the terminal state is reached.
