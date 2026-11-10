## Technical Specifications

### Front-Matter
```yaml
---
skill:
  name: testing-guidelines
  description: >-
    ...
  references:
    - references/playwright-recipes.md
---
```

- `skill.references` is an optional list of strings; the parser already supports second-level string lists.
- Allowed `skill` keys become `name`, `description`, and `references`; update the `check` key restriction and error messages.
- Each path is relative to the directory of the guideline file, in POSIX form.
- Reject absolute paths, backslashes, and paths that normalize outside the guideline directory (`..`) with exit code `1` naming the file.
- Reject duplicates and a reference to `SKILL.md`.
- Reject a missing referenced file with exit code `1`.
- Allowed file types: **[Feedback Needed]** Markdown only, or any file type for assets. Default to any type, copied byte for byte, with link rewriting only for `.md`.

### Generate
- Copy `<guideline-dir>/<ref>` to `<skills-dir>/<name>/<ref>`, creating directories as needed.
- For `.md` references, rewrite links with the same rules as `SKILL.md`, treating the reference as inside its skill.
- Links from a reference back to its own skill's files rewrite to skill-relative paths.
- `--dry-run` reports `Would create`, `Would update`, or `is up to date` per copied file.
- Remove files in `<skills-dir>/<name>/` that are no longer listed? **[Feedback Needed]** Default: report them in `check` only; `generate` never deletes.

### Collection
- Files that a guideline lists under `references` are excluded from digest and skill source collection, so they are not treated as core guidelines.
- Recursive directory collection also excludes the conventional `references/` directory name only when a listed reference lives in it; unlisted Markdown in it is still collected.

### Check
- Add issue checks `missing-reference` (listed file absent in source), `missing-skill-file` (copy absent), `stale-skill-file` (copy differs from regenerated output), and `unlisted-file` (replaces `orphan-file` for files under a skill directory that are neither `SKILL.md` nor listed).
- Keep `orphan-file` for files unlinked from `SKILL.md`: **[Decided]** each listed reference must still be linked from `SKILL.md`, as today.
- JSON output lists reference files under `skills[].files` with the same `up-to-date`, `stale`, or `missing` statuses.

### Declared Files
- src/support_python/tools/agent_digest.py
- tests/test_agent_digest.py
- docs/tools/agent-digest.md
- CHANGELOG.md

Size estimate: 4 files, 350 lines

### Tests
- Unit: front-matter parsing accepts `references`; rejects absolute, backslash, `..`, duplicate, and `SKILL.md` entries.
- Unit: referenced files are excluded from digest and skill collection.
- Unit: link rewriting inside a copied `.md` reference follows SKILL.md rules.
- Unit: `check` reports missing, stale, and unlisted reference files with the matching issue names.
- Integration: build a temporary tree with a guideline and `references/x.md`; `generate` creates the copy, `check` exits 0, editing the source makes `check` exit 1, and a rerun of `generate` restores exit 0.
- Integration: `generate --dry-run` writes nothing and reports `Would create` for the copy.

Completion check: `pytest tests/test_agent_digest.py && ruff check .`
