# Agent Digest Generator

Deterministic Markdown guideline digest and skill generator with built-in budget and link validation.
Implemented in [agent_digest.py](../../src/support_python/tools/agent_digest.py) and exposed via the `agent-digest` console script.

---

## Command-Line Interface
Run actions through the `agent-digest` console script in [agent_digest.py](../../src/support_python/tools/agent_digest.py):
```bash
agent-digest generate <PATH>... [--digest PATH] [--skills-dir PATH] [--link-base URL] [--max-words N] [--max-bytes N] [--dry-run]
agent-digest check <PATH>... [--digest PATH] [--skills-dir PATH] [--link-base URL] [--max-words N] [--max-bytes N] [--skill-index FILE] [--format text|json]
agent-digest help [--verbose]
agent-digest version
```

| Option               | Default             | Purpose                                                            |
| :------------------- | :------------------ | :----------------------------------------------------------------- |
| `<PATH>...`          | Required            | One or more Markdown files or directories to process               |
| `--digest PATH`      | `./agent-digest.md` | Output Markdown digest path (e.g. `guidelines/agent-digest.md`)    |
| `--skills-dir PATH`  | `./agent-skills`    | Output directory containing `<name>/SKILL.md` skill trees          |
| `--link-base URL`    | Derived from Git    | Base URL for repo links outside the digest and skills folders      |
| `--max-words N`      | `20`                | Maximum word count per directive sentence                          |
| `--max-bytes N`      | `20480`             | Maximum UTF-8 byte size for the generated digest                   |
| `--skill-index FILE` | None                | Index Markdown file that must link to every skill source (`check`) |
| `--dry-run`          | Off                 | Report planned writes without writing anything (`generate`)        |
| `--format FORMAT`    | `text`              | Print the `check` result as `text` or one `json` document          |

Standard logging options (`--log-file PATH`, `--log-level LEVEL`, `--debug`, `--verbose`) apply to `generate` and `check`.

---

## Input Collection and Ordering
`agent-digest` resolves `<PATH>...` arguments into an ordered source file list using seven deterministic rules:
1. Process `<PATH>` arguments in the exact order given on the command line.
2. Add file arguments directly; reject missing paths or non-`.md` file arguments with exit code `2`.
3. Recursively collect `*.md` files inside directory arguments, sorted by relative POSIX path.
4. Skip any directory whose name starts with `.` during recursive traversal.
5. Exclude the resolved `--digest` file and any file located inside `--skills-dir`.
6. Drop duplicate resolved paths while keeping the first occurrence.
7. Order files with top-level integer `index` front-matter first in ascending order, followed by unindexed files.

Ties between identical `index` values preserve the discovery order from steps 1 through 6.
A non-integer `index` value fails with exit code `1` and names the offending file.

---

## Front-Matter Schema
Source Markdown files support two optional top-level YAML front-matter keys:
```yaml
---
index: 1
skill:
  name: python-guidelines
  description: Guidelines and conventions for Python code, packaging, pytest, and Ruff.
---
```

- Files without a `skill` block are core guidelines and merge into the `--digest` output file.
- Files with a `skill` block generate `<skills-dir>/<name>/SKILL.md` with blockquote (`>`) lines removed.
- Top-level keys are restricted to `index` and `skill`.
- `skill` keys are restricted to `name` and `description`.

---

## Link Rewriting
`agent-digest` rewrites Markdown links outside code fences for core digest content and derived skill files:
- Links targeting a skill-bearing input file rewrite to ``the `<name>` skill``.
- Relative or `https://github.com/...` links whose target ends in `/skills/<name>/SKILL.md` rewrite to ``the `<name>` skill``.
- Links targeting another digest-bound core guideline collapse to plain link text (`[text](other.md)` becomes `text`).
- Links inside a derived skill targeting `<skills-dir>/<name>/...` rewrite to the skill-relative path.
- Remaining relative repository links rewrite against `--link-base` when a base URL is provided or derived from Git.
- When no `--link-base` is given and Git origin or branch metadata is unavailable, repository links remain relative.

---

## Validation Rules in `check`
`agent-digest check` verifies generated files and source rules in a single pass:
- Derived `<skills-dir>/<name>/SKILL.md` files and the `--digest` file match regenerated output on disk.
- The `--digest` file stays within `--max-bytes` UTF-8 bytes.
- Every directive sentence in the generated digest and derived skills contains at most `--max-words` words.
- YAML front-matter keys are restricted to `index` and `skill`, with only `name` and `description` under `skill`.
- When `--skill-index FILE` is provided, that file links to every skill-bearing input file.
- Every non-`SKILL.md` file under `<skills-dir>/<name>/` is linked from its companion `SKILL.md` (no orphan files).
- The generated digest contains no relative Markdown links.
- Derived `SKILL.md` files contain no links escaping the skill directory (`../`, `/`, or `\`).

---

## Dry Run in `generate`
`agent-digest generate --dry-run` builds every output in memory and writes nothing:
- Each output file logs `Would create {{path}}`, `Would update {{path}}`, or `{{path}} is up to date.`
- The digest byte budget still applies, so an oversized digest exits `1`.

---

## JSON Output in `check`
`agent-digest check --format json` prints one JSON document on `stdout` for exit codes `0` and `1`:
```json
{
  "ok": false,
  "digest": {"path": "guidelines/agent-digest.md", "status": "stale", "bytes": 1234, "max_bytes": 20480},
  "skills": [{"name": "python-guidelines", "path": "skills/python-guidelines/SKILL.md", "status": "up-to-date"}],
  "issues": [{"check": "stale-digest", "path": "guidelines/agent-digest.md", "message": "guidelines/agent-digest.md is out of date"}]
}
```

- `ok` is `true` exactly when the exit code is `0`.
- `digest.status` and `skills[].status` take `up-to-date`, `stale`, or `missing`; `digest.bytes` is the regenerated size.
- `digest` is `null` when input collection fails on invalid front-matter.
- `issues[].check` names the failed validation: `frontmatter`, `skill-index`, `missing-skill`, `stale-skill`, `orphan-file`, `escaping-link`, `digest-size`, `missing-digest`, `stale-digest`, `word-budget`, or `relative-link`.
- `issues[].path` is the offending file, or `null` when no single file applies; `issues[].message` is the error's first line.
- Log messages, including stale-file diffs, go to `stderr`; exit code `2` errors print nothing on `stdout`.

---

## Exit Codes

| Exit Code | Meaning                                                               |
| :-------- | :-------------------------------------------------------------------- |
| `0`       | Digest and skills generated or verified within all configured budgets |
| `1`       | Stale output, budget violation, invalid link, or invalid front-matter |
| `2`       | Invalid command-line arguments, missing path, or non-`.md` file path  |
