### Requirement
[ADR-0003](../../../docs/adrs/ADR-0003-standalone-tools-and-reusable-devops.md) requires `--dry-run` on every writing action.
It also requires `--format text|json` on every `list` and `check` action, with one JSON document on stdout in `json` mode.
`agent-digest generate` lacks `--dry-run`, and `agent-digest check` lacks `--format`.

### `generate --dry-run`
- **[Decided]** Register `--dry-run` on `generate` only, through its own parser configurator.
- Build the skills and digest in memory exactly as a real run does; write no file and create no directory.
- Log one INFO line per output file: `Would create {path} ...`, `Would update {path} ...`, or `{path} is up to date.`
- Keep the exit codes: the digest byte budget still fails with exit 1, and path errors exit 2.
- Add `Dry run: true|false` to the `generate` startup banner.
- `action_generate` gains a keyword `dry_run: bool = False` parameter.

### `check --format text|json`
- **[Decided]** Register `--format` through `ToolHarness.add_format_option` (T0053), so `json` enables the shared JSON output mode.
  Log messages keep their wording and move to stderr; no tool-specific logger.
- `action_check` gains a keyword `output_format: str = "text"` parameter.
- **[Decided]** Print the JSON document with `indent=2`, as `agent-files` and `git-repository-backup` do.
- Emit the document for exit codes 0 and 1; exit 2 argument errors print nothing on stdout.
- Every reported error also becomes one entry in `issues`; the text error messages are unchanged.

```json
{
  "ok": false,
  "digest": {"path": "guidelines/agent-digest.md", "status": "stale", "bytes": 1234, "max_bytes": 20480},
  "skills": [{"name": "python-guidelines", "path": "skills/python-guidelines/SKILL.md", "status": "up-to-date"}],
  "issues": [{"check": "stale-digest", "path": "guidelines/agent-digest.md", "message": "guidelines/agent-digest.md is out of date"}]
}
```
- `ok` is `true` exactly when the exit code is `0`.
- `digest.status` and `skills[].status` take `up-to-date`, `stale`, or `missing`; `digest` is `null` when input collection fails.
- `digest.bytes` is the regenerated digest's UTF-8 size.
- `issues[].check` takes `frontmatter`, `skill-index`, `missing-skill`, `stale-skill`, `orphan-file`, `escaping-link`,
  `digest-size`, `missing-digest`, `stale-digest`, `word-budget`, or `relative-link`.
- `issues[].path` is the display path of the offending file, or `null` when no single file applies.
- `issues[].message` is the first line of the logged error, so stale entries omit the diff.

### Declared Files
- src/support_python/tools/agent_digest.py
- tests/tools/test_agent_digest.py
- docs/tools/agent-digest.md
- CHANGELOG.md

### Tests
- Unit: `generate --dry-run` on fresh sources writes no digest, skill, or directory, and reports `Would create` lines.
- Unit: `generate --dry-run` after a real run reports `is up to date`, and after a source edit reports `Would update`.
- Unit: `generate --dry-run --max-bytes 10` exits 1 with the budget error and writes nothing.
- Unit: `check --format json` on fresh output prints one parseable document with `ok: true`, up-to-date statuses, and no issues.
- Unit: `check --format json` with a stale digest, a missing skill, and an unlinked skill exits 1 and lists matching issues.
- Unit: `check --format json` keeps stdout pure; log messages reach stderr.
- Unit: `check --format json` with a missing path exits 2 with empty stdout.
- Integration: installed `agent-digest check guidelines ... --format json --verbose` on the fixture checkout prints JSON that `json.loads` parses, with banners on stderr.
- Integration: installed `agent-digest generate guidelines --digest out.md --skills-dir out --dry-run` leaves both paths absent.

Completion check: `.venv/Scripts/python -m pytest -q`, `.venv/Scripts/ruff check .`, plus the integration checks above.
Size estimate: 4 files, 300 lines.
