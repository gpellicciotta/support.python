# Project Planning
An overview of all tasks and their planning.

---

## Next Milestone
- [x] T0001 Add atomic text write helpers with Windows-safe retries.
- [x] T0007 Add ANSI-aware Markdown table helpers.
- [x] T0012 Make CloudSqlProxyManager find cloud-sql-proxy outside PATH and fail cleanly when Docker is also missing.
- [ ] T0004 Add duration and time formatting helpers.
- [ ] T0008 [needs: T0004] Add a task rate limiter.
- [ ] T0005 Unify the CLI logger and action harness with dev-guidelines and plan.
- [ ] T0013 [needs: T0005] Consolidate the harness and logging into support_python and move backup-git-repos into the package.
- [ ] T0014 [needs: T0013] Port the Markdown linter into support_python unchanged with a lint markdown CLI and ported tests.
- [ ] T0015 [needs: T0013] Port the agent-files sync into support_python unchanged with an agent-files CLI and ported tests.
- [ ] T0017 [needs: T0015] Parameterize the ported agent-files sync with configurable digest, skills, marker, and tool registry.
- [ ] T0016 [needs: T0014] Refactor the ported Markdown linter into registered rule classes with loadable profiles.
- [ ] T0009 [needs: T0005] Add subprocess output streaming with logging.
- [ ] T0018 [needs: T0005] Implement the processes CLI and standalone script with safe kill and filtered list commands.


---

## Backlog
*(Currently no tasks)*
