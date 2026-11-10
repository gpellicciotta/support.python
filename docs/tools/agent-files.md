# Agent Files Synchronization

Deterministic installation of an existing agent digest and skills directory into installed AI coding tools.
`agent-files` never generates or refreshes the digest; run [agent-digest](agent-digest.md) first.
Implemented in [agent_files.py](../../src/support_python/tools/agent_files.py) and configured via [agent_files_config.py](../../src/support_python/tools/agent_files_config.py).

---

## Command-Line Interface
Run actions through the `agent-files` console script in [agent_files.py](../../src/support_python/tools/agent_files.py):
```bash
agent-files list [--format text|json] [--config PATH]
agent-files sync [TOOL ...] [--config PATH] [--dry-run] [--no-prune]
agent-files check [TOOL ...] [--format text|json] [--config PATH]
agent-files review [TOOL ...] [--config PATH] [--timeout SECONDS]
```

Supported configuration flags override JSON settings and built-in defaults:
- `--config PATH` loads explicit JSON settings from `PATH`.
- `--format text|json` selects text or JSON output on `list` and `check` (default: `text`; `check` JSON reports `up-to-date`, `changes-pending`, or `unavailable` when a target file cannot be read or has invalid guarded-block markers).
- In `json` mode, log messages go to `stderr` so `stdout` holds only the JSON document.
- `--repo-root PATH` overrides the source repository root directory.
- `--digest PATH` overrides the digest file to install (default: `{{repo-root}}/agent-digest.md`).
- `--skills-dir PATH` overrides the skills directory to install (default: `{{repo-root}}/agent-skills`).
- `--marker NAME` sets the guarded block marker identifier.
- `--marker-begin TEXT` overrides the opening HTML comment marker line.
- `--marker-end TEXT` overrides the closing HTML comment marker line.
- `--manifest-source NAME` sets the ownership `source` recorded in skills manifests.
- `--legacy-skill NAME` replaces `legacy-skill-names` with the specified bootstrap skill name (repeatable).

Default digest and skills paths match `agent-digest` and resolve under `repo-root`.
A missing skills directory means no skills.
When the digest is missing, `sync` and `check` exit 1 with a hint:
```bash
agent-digest generate {{path}}... --digest agent-digest.md --skills-dir agent-skills
agent-files sync
```

---

## JSON Configuration Schema
Configuration keys accept dashes or underscores interchangeably; this document shows the preferred kebab-case spelling.
When `--config` is omitted, the loader checks `.agent-files.json` in the resolved repository root, falling back to `agent-files.json` with a deprecation warning (removed in `v3.0.0`).
All relative paths in `.agent-files.json` resolve against `repo-root`.
```json
{
  "repo-root": ".",
  "digest-path": "agent-digest.md",
  "skills-dir": "agent-skills",
  "marker": "dev-guidelines",
  "manifest-source": "dev-guidelines",
  "legacy-skill-names": [
    "plan-task-usage",
    "ui-verification"
  ],
  "replace-tools": false,
  "tools": [
    {
      "name": "cursor-agent",
      "command": "cursor",
      "target-file": "~/.cursor/rules.md",
      "skills-dir": "~/.cursor/skills",
      "native-skill-discovery": true,
      "aliases": ["cursor"]
    }
  ]
}
```

| Field                | Type            | Default                         | Purpose                                                |
| :------------------- | :-------------- | :------------------------------ | :----------------------------------------------------- |
| `repo-root`          | `string`        | Config directory or Git root    | Base directory for relative paths and review runs      |
| `digest-path`        | `string`        | `{{repo-root}}/agent-digest.md` | Existing Markdown digest synced into target files      |
| `skills-dir`         | `string`        | `{{repo-root}}/agent-skills`    | Source directory containing `{{skill}}/SKILL.md` trees |
| `marker`             | `string`        | `dev-guidelines`                | Identifier for guarded block comments                  |
| `marker-begin`       | `string`        | Derived from `marker`           | Explicit opening guarded block line                    |
| `marker-end`         | `string`        | Derived from `marker`           | Explicit closing guarded block line                    |
| `manifest-source`    | `string`        | `dev-guidelines`                | Ownership tag written into the skills manifest         |
| `manifest-name`      | `string`        | `.dev-guidelines-skills.json`   | Manifest filename inside each target skills folder     |
| `legacy-skill-names` | `array<string>` | Built-in legacy list or `[]`    | Bootstrap skill names owned before manifest creation   |
| `replace-tools`      | `boolean`       | `false`                         | Replace default tools instead of merging `tools`       |
| `tools`              | `array<object>` | Built-in tool registry          | Additional or overridden tool registry entries         |

### Guarded Block Markers
The default `dev-guidelines` marker wraps the synced block in these lines:
```markdown
<!-- BEGIN dev-guidelines (generated by agent-files sync -- do not edit by hand; edit the source digest instead) -->
<!-- END dev-guidelines -->
```

Any other `marker` gets `<!-- BEGIN {{marker}} -->` and `<!-- END {{marker}} -->`.
Without an explicit `marker-begin`, `sync` also recognizes any whole line `<!-- BEGIN {{marker}} ({{note}}) -->`.
It then rewrites that line to the current text, so blocks written with an earlier wording keep syncing.
An explicit `marker-begin` is matched exactly.

---

## Default Tool Registry
The built-in registry in [agent_files_config.py](../../src/support_python/tools/agent_files_config.py) defines three default entries:
- `claude-code` (alias `claude`) targets `~/.claude/CLAUDE.md` and `~/.claude/skills`.
- `antigravity` targets `~/.gemini/GEMINI.md` and `~/.gemini/config/skills`.
- `codex-cli` (alias `codex`) targets `~/.codex/AGENTS.md` and `~/.agents/skills`.
