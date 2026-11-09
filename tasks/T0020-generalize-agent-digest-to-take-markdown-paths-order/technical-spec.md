### Command-Line Interface
```text
agent-digest generate <PATH>... [--digest PATH] [--skills-dir PATH] [--link-base URL] [--max-words N] [--max-bytes N]
agent-digest check <PATH>... [--digest PATH] [--skills-dir PATH] [--link-base URL] [--max-words N] [--max-bytes N] [--skill-index FILE]
agent-digest help [--verbose]
agent-digest version
```
- `--digest` defaults to `./agent-digest.md`, and `--skills-dir` defaults to `./agent-skills`, both relative to the current directory.
- `--max-words` defaults to 20 and `--max-bytes` to 20480, the current budgets.
- Remove the `validate` action; `check` keeps its freshness checks and takes over every validation check.
- `generate` and `check` without any `PATH` report a usage error and exit 2.
- A `PATH` that does not exist, or a listed file not ending in `.md`, reports an error and exits 2, like `markdown_lint`.
- Follow the `cli-guidelines` skill for help, version, flags, and exit codes, using `support_python.cli.ToolHarness` and the ADR-0003 conventions.
- Follow the `logging-guidelines` skill for streams, severity indicators, and start and finish banners, using `support_python.logging`.

### Input Collection and Ordering
1. Process the `PATH` arguments in command-line order.
2. A file argument contributes itself.
3. A directory argument contributes every `*.md` file below it, recursively, sorted by relative POSIX path.
4. Skip directories whose name starts with `.`.
5. Exclude the `--digest` file and every file below `--skills-dir`, so generated output never feeds back as input.
6. Drop duplicates by resolved path, keeping the first occurrence.
7. Files whose front-matter has a top-level `index` key come first, in ascending `index` order.
8. Files sharing an `index` value keep their relative order from steps 1–6 (stable sort).
9. All files without `index` follow, in their order from steps 1–6.
10. A non-integer `index` value is an error: `generate` and `check` exit 1 and name the file.

Example: `agent-digest generate guidelines extra.md` with `guidelines/b.md` (`index: 1`), `guidelines/a.md` (no index), and `extra.md` (`index: 0`) orders `extra.md`, `guidelines/b.md`, `guidelines/a.md`.

### Front-Matter
- Front-matter is a YAML block between `---` lines at the start of a file, parsed without third-party dependencies.
- Extend the parser with top-level scalar keys such as `index: 2`, keeping the existing `skill:` mapping support.
- Files with a `skill:` mapping become skills, as now; all other files feed the digest in the order above.
- `check` reports top-level keys other than `index` and `skill`, and unknown keys under `skill:`, as errors.

### Removal of dev-guidelines Specifics
- Remove `SOURCE_FILES`, `GUIDELINES_DIR`, `DIGEST_PATH`, `SKILLS_DIR`, and the missing-source `FileNotFoundError`.
- Remove `PLAN_OWNED_SKILLS`; rewrite any link whose target ends in `/skills/<name>/SKILL.md` as "the `<name>` skill".
- That rewrite covers relative targets and `https://github.com/...` targets alike; dev-guidelines links plan's skills by GitHub URL.
- Replace the hardcoded `https://github.com/gpellicciotta/dev-guidelines/blob/main/` link base with `--link-base`.
- Without `--link-base`, derive it from the input repository's `origin` remote and current branch, as `https://github.com/<owner>/<repo>/blob/<branch>/`.
- When no link base can be derived, leave repository links relative; `check` then reports them as `validate` does today.
- Resolve the repository root from the first `PATH` with `find_project_root`.
- Replace the hardcoded `general-guidelines.md` skill-coverage check with `--skill-index FILE`: every skill source must be linked from `FILE`.
- Skip that check when `--skill-index` is absent.

### Check
- `check` regenerates the digest and skills in memory and reports any difference from the files on disk, as it does today.
- It also runs `validate`'s budget, front-matter, orphan reference file, and link checks.
- It exits 0 only when every check passes, and 1 otherwise.

### Callers
- Update `agent_files.get_digest_generator` and its callers for the new function signatures, keeping `agent-files` behavior unchanged.

### Declared Files
- src/support_python/tools/agent_digest.py
- src/support_python/tools/agent_files.py
- tests/tools/test_agent_digest.py
- tests/tools/test_agent_files.py
- docs/tools/agent-digest.md
- docs/index.md
- README.md
- CHANGELOG.md

### Tests
- Unit: path collection covers files, recursive directories, hidden directories, duplicates, and missing or non-Markdown paths.
- Unit: index ordering covers indexed and unindexed files, equal index values, and a non-integer index.
- Unit: the `--digest` file and `--skills-dir` contents are excluded when they sit inside an input directory.
- Unit: `--digest`, `--skills-dir`, and their defaults control where `generate` writes.
- Unit: `check` fails on a stale digest, a stale skill, a budget violation, and an unlinked skill with `--skill-index`.
- Unit: `--link-base` overrides the derived link base, and a repository without `origin` keeps relative links.
- Unit: a GitHub URL ending in `/skills/<name>/SKILL.md` becomes "the `<name>` skill" in the digest and skills.
- Integration: in a current dev-guidelines checkout, `agent-digest generate guidelines --digest guidelines/agent-digest.md --skills-dir skills` leaves `git status --short` empty.
- Integration: in that checkout, `agent-digest check guidelines --digest guidelines/agent-digest.md --skills-dir skills --skill-index guidelines/general-guidelines.md` exits 0.

Completion check: `python -m pytest tests -q`, plus the dev-guidelines integration commands above.
Size estimate: 8 files, 700 lines.
Size note: Above the typical line because inputs, ordering, outputs, and check form one CLI contract; a partial change leaves an unusable tool.
