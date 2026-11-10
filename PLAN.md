# Project Planning
An overview of all tasks and their planning.

---

## Next Milestone
- [ ] T0060 [needs: T0057] Provide a reusable settings resolver and config command group in support_python, per the configuration guidelines.
- [~] T0061 [owner: @claude-code] Support skill references in agent-digest front-matter, copying listed files into skills with link rewriting and checks.
- [ ] T0057 Use kebab-case configuration keys in all tools, still accepting snake_case keys, per the configuration guidelines.
- [x] T0059 Make git-repository-backup find its user config through user_config_path, reading the old ~/.config location with a deprecation warning.

---

## Backlog
- [ ] T0062 Allow up to two trailing spaces in lint-markdown MD011, so Markdown hard line breaks pass and fix keeps them.
- [ ] T0046 Migrate pinned sibling consumers (auth, counters.server, todos.server, template.python) off build_action_parser, print_help, and print_version when they upgrade to support-python v2
