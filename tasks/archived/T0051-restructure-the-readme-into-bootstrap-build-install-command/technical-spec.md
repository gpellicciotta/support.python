## Technical Specifications

### Decisions
- **[Decided]** README sections, as the user requested on 2026-11-10:
  - Bootstrap and Build: how to bootstrap and build this project.
  - Install: pipx, uv, pip, the release installer script, downstream `pyproject.toml` pins, and GitHub release assets.
  - Command-line tools: a table of the five console scripts, each linking its `docs/tools/` page.
  - Library: a table of package groups and main uses, each linking its `docs/tutorials/` page.
- **[Decided]** Install examples use `v<version>` placeholders instead of the stale `v1.0.0` pins.
- **[Decided]** Repository maintenance scripts move to the `docs/devops.md` Scripts section, which also drops removed v1 wrapper scripts.
- **[Decided]** README-only tool details, such as config fallbacks and synopses, move into `docs/tools/` pages when missing there.

### Declared Files
- README.md
- docs/index.md
- docs/devops.md
- CHANGELOG.md
- pyproject.toml
- Up to two `docs/tools/` pages, only where README-only details are missing; unknown until the read step.

### Tests
- Unit: none (documentation-only change with no code)
- Integration: none (documentation-only change; the Markdown linter run is the completion check)

Size estimate: 7 files, 300 lines

Completion check: `.venv/Scripts/lint-markdown check --offline README.md docs/index.md docs/devops.md docs/tools docs/tutorials` exits 0.
