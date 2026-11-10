---
task: T0051
round: 1
verdict: rejected
reviewer: "@claude-reviewer"
reviewed_at: 2026-11-10T07:58:42Z
reviewed_commit: "ef9c729"
base_commit: "ef9c729"
---
# T0051 Review Findings, Round 1

Verdict: reject.
The README's install section adds one wrong claim.
It is a one-line fix; everything else checks out.

## Checks
- Request fit: the README now holds only bootstrap, build, install, a command-line tools table linking `docs/tools/`, and a library table linking `docs/tutorials/`.
  It also keeps the title, license, and "See also" links.
  This matches the user request and the spec decisions.
- No content lost from the repository:
  - The tool synopses, options, config fallbacks, and source links live in the `docs/tools/` pages:
    - `agent-files.md:5-41`: digest-never-generated note, exit 1 hint, and `agent-files.json` fallback.
    - `agent-digest.md:4-25`.
    - `git-repository-backup.md:3-45`: AES-256 and legacy `backup-git-repos` config.
    - `lint-markdown.md:3-80`: legacy `.markdown-lint.json` and plugins.
  - The maintenance scripts and their usage moved to `docs/devops.md` under Scripts.
  - The install commands, downstream pin, release assets, and version and dependency locations remain in the README.
- Extras: `pyproject.toml` defines `redis` and `mysql` extras.
- Scripts table: `docs/devops.md` matches `scripts/` exactly.
  The directory holds six scripts plus `_cli_common.py`.
  Dropping the old "each supports `--help` and `--version`" line is correct, because `extract-release-notes.py` and `install-from-github-release.py` have no version option.
- Tool flags: I ran all five tools with `help`, `version`, `-h`, `--help`, `--version`, and `version --verbose`.
  Every run exited 0.
- Re-exports: "Most library symbols are re-exported" holds, at about two thirds of public names, excluding `support_python.tools`.
- Links: every relative link in README.md, `docs/index.md`, and `docs/devops.md` resolves.
  No file outside `.venv` and `.plan` links to a `README.md#` anchor.
- Completion check: `.venv/Scripts/lint-markdown check --offline README.md docs/index.md docs/devops.md docs/tools docs/tutorials` passed with exit code 0 on 19 files.
- Task file: `plan tasks validate` passed.

## Findings

### F1 (defect): "isolated environment" claim is wrong for two of the four install commands
- Location: `README.md:35`.
- The README introduces all four commands with "Install the command-line tools globally, each in an isolated environment".
- `pip install --user` installs into the user site-packages, which is not isolated.
- `install-from-github-release.py --global` uses pipx only when pipx is available.
  Otherwise it falls back to `pip install --user` (`scripts/install-from-github-release.py:64-69`).
- Fix: "Install the command-line tools globally; `pipx` and `uv tool` give them an isolated environment:".

### N1 (nit): `net` missing from the Script utilities row
- Location: `README.md:90`.
- The Script utilities row lists "port checks" but leaves `net` out of its Modules column.
- `is_port_in_use` lives in `net`, and the script utilities tutorial covers it.
- Fix (optional): list `net (is_port_in_use)` in that row, or drop "port checks".

### N2 (nit): migration guide filed under Command-Line Tools
- Location: `docs/index.md`.
- "Migrating to v2.0.0" sits under Command-Line Tools, but it also maps the library API.
- Fix (optional): move it to the Overview list or to its own line after both sections.
