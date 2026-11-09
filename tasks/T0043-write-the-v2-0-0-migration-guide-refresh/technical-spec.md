### Migration Guide
- One table per area (commands, modules, options and verbs, config files, library API), each row mapping old to new.
- Include install instructions for the tools and the `scripts/devops.py` migration pattern per project type.

### Consumer Backlog Tasks
Create each with `plan tasks create --project ../<repo> --section Backlog "<description>"`.
Every description notes that it needs the released support-python v2.0.0.
- `../dev-guidelines`: call `lint-markdown check`, `agent-digest generate|check` with explicit `--digest` and `--skills-dir`,
  and `agent-files sync|check` with `.agent-files.json` paths; rename any lint config to `.lint-markdown.json`.
- `../template.python`, `../template.java`, `../support.java`, and `../support.js`: replace `scripts/devops.py`
  with a thin `DevopsCli` script using the matching adapter, pinning support-python v2.0.0.
- `../auth`, `../counters.server`, and `../todos.server`: replace the duplicated docker, db, server, mail, client,
  and production code with `add_services` and `set_deploy`; auth also moves `capture-view.py` onto the T0044 capture CLI.
- `../plan`, `../meteo`, `../todos.webapp`, `../verkeersregels-quiz`, and `../family-portal`: evaluate adopting `DevopsCli`,
  keeping project-specific actions through `add_action`.

### Declared Files
- docs/migration-v2.md
- CLAUDE.md
- README.md
- docs/index.md
- CHANGELOG.md

### Tests
- Unit test: none (documentation and planning only).
- Integration test: none (no code changes; the completion check verifies the documents and consumer task files)

Completion check: `lint-markdown check --offline docs/migration-v2.md CLAUDE.md README.md docs/index.md CHANGELOG.md`
exits 0, and `plan tasks validate --project ../<repo>` passes for each consumer.
Size estimate: 5 files, 300 lines, excluding consumer planning files.
