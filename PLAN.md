# Project Planning
An overview of all tasks and their planning.

---

## Next Milestone
- [x] T0002 Add git runner and read-only repository helpers.
- [x] T0003 Add process hierarchy and safe termination helpers.
- [x] T0006 Add the locking base class, file lock, null lock, and backend factory.
- [ ] T0001 Add atomic text write helpers with Windows-safe retries.
- [ ] T0007 Add ANSI-aware Markdown table helpers.
- [x] T0010 Add a Redis-backed distributed lock as an optional extra.
- [x] T0011 Add a MySQL advisory lock as an optional extra.
- [ ] T0013 [needs: T0005] Consolidate the harness and logging into support_python and move backup-git-repos into the package.
- [ ] T0012 Make CloudSqlProxyManager find cloud-sql-proxy outside PATH and fail cleanly when Docker is also missing.
- [ ] T0015 [needs: T0013] Port the agent-files sync into support_python unchanged with an agent-files CLI and ported tests.
- [ ] T0017 [needs: T0015] Parameterize the ported agent-files sync with configurable digest, skills, marker, and tool registry.
- [ ] T0004 Add duration and time formatting helpers.
- [ ] T0008 [needs: T0004] Add a task rate limiter.
- [ ] T0014 [needs: T0013] Port the Markdown linter into support_python unchanged with a lint markdown CLI and ported tests.
- [ ] T0016 [needs: T0014] Refactor the ported Markdown linter into registered rule classes with loadable profiles.
- [ ] T0005 Unify the CLI logger and action harness with dev-guidelines and plan.
- [ ] T0009 [needs: T0005] Add subprocess output streaming with logging.

---

## Backlog
*(Currently no tasks)*
