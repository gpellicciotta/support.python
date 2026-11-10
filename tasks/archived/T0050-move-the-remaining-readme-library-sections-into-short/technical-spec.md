## Technical Specifications

### Decisions
- **[Decided]** Follow the T0049 decisions: one short tutorial per package group, keeping every README statement and example.
- **[Decided]** Tutorial grouping:
  - `cli-harness-and-logging.md`: `support_python.cli`, `logging`, `tables`, and `tokens`.
  - `script-utilities.md`: `terminal`, `version`, `net.is_port_in_use`, `env`, and `crypto`.
  - `rest-clients.md`: `net` transport, `errors`, `dates`, and `models`.
  - `view-capture.md`: `capture` and `httpd`.
  - `sql-anonymizer.md`: `sql`.
- **[Decided]** Moved README sections keep their headings with a one-line linked summary until T0051 restructures the README.

### Declared Files
- docs/tutorials/cli-harness-and-logging.md
- docs/tutorials/script-utilities.md
- docs/tutorials/rest-clients.md
- docs/tutorials/view-capture.md
- docs/tutorials/sql-anonymizer.md
- README.md
- docs/index.md
- CHANGELOG.md
- pyproject.toml

### Tests
- Unit: none (documentation-only change with no code)
- Integration: none (documentation-only change; the Markdown linter run is the completion check)

Size estimate: 9 files, 500 lines
Size note: Above the typical line by one file and about 100 moved lines; each tutorial is small, and splitting further adds lifecycle overhead only.

Completion check: `.venv/Scripts/lint-markdown check --offline README.md docs/index.md docs/tutorials` exits 0.
