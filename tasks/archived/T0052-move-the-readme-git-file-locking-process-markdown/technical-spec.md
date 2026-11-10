## Technical Specifications

### Decisions
- **[Decided]** Follow the T0049 decisions: one short tutorial per package group, keeping every README statement and example.
- **[Decided]** Tutorial grouping:
  - `git-helpers.md`: `support_python.git`.
  - `files-and-locking.md`: `files` and `locking`.
  - `process-management.md`: `processes`; CLI examples move to `docs/tools/processes.md` when it lacks them.
  - `markdown.md`: `markdown.tables` and the `markdown` linter API, linking `docs/tools/lint-markdown.md` for the CLI.
  - `durations-and-rate-limiting.md`: `durations` and `ratelimit`.
- **[Decided]** The README "Markdown linter" CLI synopsis stays for T0051, which owns the tool sections.
- **[Decided]** Moved README sections keep their headings with a one-line linked summary until T0051 restructures the README.

### Declared Files
- docs/tutorials/git-helpers.md
- docs/tutorials/files-and-locking.md
- docs/tutorials/process-management.md
- docs/tutorials/markdown.md
- docs/tutorials/durations-and-rate-limiting.md
- README.md
- docs/index.md
- CHANGELOG.md
- pyproject.toml

### Tests
- Unit: none (documentation-only change with no code)
- Integration: none (documentation-only change; the Markdown linter run is the completion check)

Size estimate: 9 files, 480 lines
Size note: Above the typical line by one file and about 80 moved lines; each tutorial is small, and splitting further adds lifecycle overhead only.

Completion check: `.venv/Scripts/lint-markdown check --offline README.md docs/index.md docs/tutorials docs/tools/processes.md` exits 0.
