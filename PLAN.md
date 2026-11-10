# Project Planning
An overview of all tasks and their planning.

---

## Next Milestone
- [x] T0058 Resolve user configuration files through XDG_CONFIG_HOME or APPDATA in a shared helper, per the configuration guidelines.
- [ ] T0057 Use kebab-case configuration keys in all tools, still accepting snake_case keys, per the configuration guidelines.
- [ ] T0059 Make git-repository-backup find its user config through user_config_path, reading the old ~/.config location with a deprecation warning.
- [x] T0055 Make --debug imply --verbose in ToolHarness, so actions reading args.verbose also see it.
- [x] T0056 Accept millisecond and offset instants and add date-only helpers in support_python.dates, per the REST API guidelines.
- [x] T0054 [owner: @claude-code] [protocol: adhoc] Give extract-release-notes, migrate-namespace, reset-history, and install-from-github-release working --help and --version options.
- [x] T0047 [owner: @claude-code] [protocol: adhoc] Make test_is_process_alive_current_dead_and_expected_start derive its stale time from the process start, not from now minus 60s.
- [x] T0048 Add --dry-run to agent-digest generate and --format text|json to agent-digest check, as ADR-0003 requires.
- [x] T0045 Keep ToolHarness help option columns separated when an option name exceeds 23 characters.
- [x] T0053 Share JSON output handling in ToolHarness and CliLogger, and use it in agent-files, lint-markdown, processes, and git-repository-backup.

---

## Backlog
- [ ] T0046 Migrate pinned sibling consumers (auth, counters.server, todos.server, template.python) off build_action_parser, print_help, and print_version when they upgrade to support-python v2
