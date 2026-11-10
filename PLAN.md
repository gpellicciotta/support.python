# Project Planning
An overview of all tasks and their planning.

---

## Next Milestone
- [x] T0062 Allow up to two trailing spaces in lint-markdown MD011, so Markdown hard line breaks pass and fix keeps them.
- [ ] T0060 Provide a reusable settings resolver and config command group in support_python, per the configuration guidelines.
- [x] T0057 Use kebab-case configuration keys in all tools, still accepting snake_case keys, per the configuration guidelines.

---

## Backlog
- [ ] T0064 Add tests for tool-level kebab-case keys, documented example configs, and the agent-files --config integration case.
- [ ] T0063 Report unknown configuration keys as written and pass the tool logger to key normalization in all tools.
- [ ] T0046 Migrate pinned sibling consumers (auth, counters.server, todos.server, template.python) off build_action_parser, print_help, and print_version when they upgrade to support-python v2
