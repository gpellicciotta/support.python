## Technical Specifications

### Decisions
- **[Decided]** `docs/tutorials/` holds one short tutorial per package group; `docs/tools/` stays the CLI reference.
- **[Decided]** The tutorial keeps every README statement and example; only formatting and typos change.
- **[Decided]** Tutorial structure: H1 title, a short intro naming the modules with relative source links, then one H2 per topic.
- **[Decided]** Topics: subprocess steps, local service managers, release helpers, `ReleasePipeline`, `DevopsCli` and project adapters, deploy action, service action groups.
- **[Decided]** The README keeps its "DevOps script helpers and environment managers" heading with a summary and link until T0051 restructures it.
- **[Decided]** Fix the existing README trailing-whitespace findings, since the completion check lints README.md.

### Declared Files
- docs/tutorials/devops-scripts.md
- README.md
- docs/index.md
- docs/migration-v2.md
- CHANGELOG.md
- pyproject.toml

### Tests
- Unit: none (documentation-only change with no code)
- Integration: none (documentation-only change; the Markdown linter run is the completion check)

Size estimate: 6 files, 520 lines
Size note: Moves one README section of about 240 lines; splitting it would document one package in two places.

Completion check: `.venv/Scripts/lint-markdown check --offline README.md docs/index.md docs/migration-v2.md docs/tutorials` exits 0.
