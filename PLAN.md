# Project Planning
An overview of all tasks and their planning.

---

## Next Milestone
- [x] T0054 [owner: @claude-code] [protocol: adhoc] Give extract-release-notes, migrate-namespace, reset-history, and install-from-github-release working --help and --version options.
- [x] T0047 [owner: @claude-code] [protocol: adhoc] Make test_is_process_alive_current_dead_and_expected_start derive its stale time from the process start, not from now minus 60s.
- [x] T0048 Add --dry-run to agent-digest generate and --format text|json to agent-digest check, as ADR-0003 requires.
- [x] T0045 Keep ToolHarness help option columns separated when an option name exceeds 23 characters.
- [x] T0053 Share JSON output handling in ToolHarness and CliLogger, and use it in agent-files, lint-markdown, processes, and git-repository-backup.

---

## Backlog
- [ ] T0046 Migrate pinned sibling consumers (auth, counters.server, todos.server, template.python) off build_action_parser, print_help, and print_version when they upgrade to support-python v2
