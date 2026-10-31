---
name: adhoc
description: Quick task protocol with optional task file and auto isolation in automated runs.
worktree: auto
branch: auto
task_file: optional
integration: squash
commit: auto
push: none
cleanup: auto
review: none
preview: none
---

# Adhoc Task Execution Protocol

You are executing task **{{task-id}}**: {{description}}

## Environment
- Working Directory: {{work-dir}}
- Target Branch: {{branch}}
- Target Worktree: {{worktree}}

## Workflow
1. {{isolation-instructions}}
2. A companion task markdown file is optional; use one only if it already exists.
3. Implement the requested fix or minor change cleanly.
4. Run relevant tests to verify the change introduces no regressions.
5. When verification succeeds, update CHANGELOG.md if user-facing.
6. {{completion-instruction}}
7. End the turn immediately once the terminal state is reached.
