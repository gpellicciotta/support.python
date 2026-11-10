## Walkthrough & Validation

### Summary
- Added `docs/migration-v2.md` with tables for commands, verbs and options, config files, modules, patch targets, and library API.
- The guide covers tool installation and the `scripts/devops.py` migration pattern per project type.
- Refreshed the CLAUDE.md overview, Commands, and Architecture sections for the v2.0.0 layout.
- Linked the guide from README.md, docs/index.md, and the CHANGELOG.md pre-release section.
- Fixed existing README lint findings: workflow and `PLAN.md` links, and a blank line before a list.
- Created 13 consumer Backlog tasks with `plan tasks create --project`, then expanded their Goals with the spec wording.

### Completion check: lint-markdown
Command: `lint-markdown check --offline docs/migration-v2.md CLAUDE.md README.md docs/index.md CHANGELOG.md`.
Run in the task worktree with the main checkout's `.venv` (same HEAD `65b2446`).
Exit code: 0.
```text
Starting lint-markdown v2.0.28-pre+65b2446 with configuration:
- Command: check
- Log file: none
- Log level: INFO
- Verbose: false
- Working directory: C:\Dev-Projects\support.python\.plan\work\T0043-write-the-v2-0-0-migration-guide-refresh
All 5 markdown files passed linting.
Finished lint-markdown check in 0.2s with status: succeeded
exit=0
```

### Consumer Backlog tasks
Each task's description and Goals say it needs the released support-python v2.0.0.

| Repository            | Task  | Scope                                                        |
| :-------------------- | :---- | :----------------------------------------------------------- |
| `dev-guidelines`      | T0190 | lint-markdown, agent-digest, agent-files calls; config names |
| `template.python`     | T0014 | Thin `DevopsCli` on `PythonProject`                          |
| `template.java`       | T0030 | Thin `DevopsCli` on `GradleProject`                          |
| `support.java`        | T0005 | Thin `DevopsCli` on `GradleProject`                          |
| `support.js`          | T0027 | Thin `DevopsCli` on `NodeProject`                            |
| `auth`                | T0218 | `add_services`, `set_deploy`, capture CLI move               |
| `counters.server`     | T0267 | `add_services`, `set_deploy`                                 |
| `todos.server`        | T0211 | `add_services`, `set_deploy`                                 |
| `plan`                | T0606 | Evaluate `DevopsCli` adoption                                |
| `meteo`               | T0029 | Evaluate `DevopsCli` adoption                                |
| `todos.webapp`        | T0218 | Evaluate `DevopsCli` adoption                                |
| `verkeersregels-quiz` | T0092 | Evaluate `DevopsCli` adoption                                |
| `family-portal`       | T0175 | Evaluate `DevopsCli` adoption                                |

### Completion check: plan tasks validate per consumer
Command: `plan tasks validate --project ../<repo>` for each consumer.
Each line joins the repository name, the final output line, and the exit code; padding was added for readability.
```text
dev-guidelines: All 5 task files passed validation.          exit=0
template.python: All 1 task file passed validation.          exit=0
template.java: All 1 task file passed validation.            exit=0
support.java: All 5 task files passed validation.            exit=0
support.js: All 1 task file passed validation.               exit=0
auth: All 2 task files passed validation.                    exit=0
counters.server: All 8 task files passed validation with 1 warning.  exit=0
todos.server: All 5 task files passed validation.            exit=0
plan: All 69 task files passed validation with 2 warnings.   exit=0
meteo: All 2 task files passed validation.                   exit=0
todos.webapp: Found 13 lint issues across 21 task files.     exit=1
verkeersregels-quiz: All 3 task files passed validation.     exit=0
family-portal: All 7 task files passed validation.           exit=0
```

The todos.webapp failure is an existing problem, not caused by this task.
It is TF017 `ui-task-screenshots` on `T0047-create-a-new-list-only-when-the-create.md`, last modified 2026-11-06.
Its warnings come from T0072 through T0078.
The new todos.webapp task validates on its own:
```text
$ plan tasks validate --project ../todos.webapp ../todos.webapp/.plan/tasks/T0218-*.md
All 1 task file passed validation.
exit=0
```
The consumer warnings (counters.server T0051, plan T0547 and T0548) also come from existing task files.

### Review round 1 rework
- Reverted every edit inside the frozen `## v1.3.0 [2026-11-07]` CHANGELOG section.
- Bumped the active heading to `## v2.0.29-pre` and `pyproject.toml` to `2.0.29-pre`.
- Scoped the `--dry-run` and `--format` claims in the guide to the actions that support them.
- The guide now names the `agent-digest` gap; Backlog task T0048 tracks closing it.
- Checked with `help --verbose` on each tool; `agent-digest help check` and `help generate` list neither option.

`pytest` against the worktree sources: exit 0.
```text
1041 passed, 3 skipped, 133 subtests passed in 146.10s (0:02:26)
```

The completion check now fails, because the frozen v1.3.0 links point at files moved in v2.
Exit code: 1.
```text
CHANGELOG.md:54:115: MD014 [valid-relative-links] Relative link 'src/support_python/agent_files_config.py' does not resolve to an existing file on disk
CHANGELOG.md:54:178: MD014 [valid-relative-links] Relative link 'docs/agent-files.md' does not resolve to an existing file on disk
CHANGELOG.md:55:59: MD014 [valid-relative-links] Relative link 'src/support_python/agent_files.py' does not resolve to an existing file on disk
CHANGELOG.md:56:54: MD014 [valid-relative-links] Relative link 'src/support_python/markdown_lint.py' does not resolve to an existing file on disk
CHANGELOG.md:57:188: MD014 [valid-relative-links] Relative link 'src/support_python/backup.py' does not resolve to an existing file on disk
CHANGELOG.md:58:123: MD014 [valid-relative-links] Relative link 'src/support_python/devops.py' does not resolve to an existing file on disk
**[WARN]**  Found 6 lint issues across 5 files.
**[ERROR]** Finished lint-markdown check in 0.1s with status: failed
exit=1
```
The other four declared files pass.
The user's decision on this conflict is pending; the task stays suspended until it arrives.
