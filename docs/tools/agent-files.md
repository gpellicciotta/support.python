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
- `--repo-root PATH` overrides the source repository root directory.
- `--digest PATH` overrides the digest file to install (default: `{{repo-root}}/agent-digest.md`).
- `--skills-dir PATH` overrides the skills directory to install (default: `{{repo-root}}/agent-skills`).
- `--marker NAME` sets the guarded block marker identifier.
- `--marker-begin TEXT` overrides the opening HTML comment marker line.
- `--marker-end TEXT` overrides the closing HTML comment marker line.
- `--manifest-source NAME` sets the ownership `source` recorded in skills manifests.
- `--legacy-skill NAME` replaces `legacy_skill_names` with the specified bootstrap skill name (repeatable).

Default digest and skills paths match `agent-digest` and resolve under `repo_root`.
A missing skills directory means no skills.
When the digest is missing, `sync` and `check` exit 1 with a hint:
```bash
agent-digest generate <PATH>... --digest agent-digest.md --skills-dir agent-skills
agent-files sync
```

---

## JSON Configuration Schema
When `--config` is omitted, the loader checks `.agent-files.json` in the resolved repository root, falling back to `agent-files.json` with a deprecation warning (removed in `v3.0.0`).
All relative paths in `.agent-files.json` resolve against `repo_root`.
```json
{
  "repo_root": ".",
  "digest_path": "agent-digest.md",
  "skills_dir": "agent-skills",
  "marker": "dev-guidelines",
  "manifest_source": "dev-guidelines",
  "legacy_skill_names": [
    "plan-task-usage",
    "ui-verification"
  ],
  "replace_tools": false,
  "tools": [
    {
      "name": "cursor-agent",
      "command": "cursor",
      "target_file": "~/.cursor/rules.md",
      "skills_dir": "~/.cursor/skills",
      "native_skill_discovery": true,
      "aliases": ["cursor"]
    }
  ]
}
```

| Field                | Type            | Default                         | Purpose                                              |
| :------------------- | :-------------- | :------------------------------ | :--------------------------------------------------- |
| `repo_root`          | `string`        | Config directory or Git root    | Base directory for relative paths and review runs    |
| `digest_path`        | `string`        | `{{repo-root}}/agent-digest.md` | Existing Markdown digest synced into target files    |
| `skills_dir`         | `string`        | `{{repo-root}}/agent-skills`    | Source directory containing `<skill>/SKILL.md` trees |
| `marker`             | `string`        | `dev-guidelines`                | Identifier for guarded block comments                |
| `marker_begin`       | `string`        | Derived from `marker`           | Explicit opening guarded block line                  |
| `marker_end`         | `string`        | Derived from `marker`           | Explicit closing guarded block line                  |
| `manifest_source`    | `string`        | `dev-guidelines`                | Ownership tag written into the skills manifest       |
| `manifest_name`      | `string`        | `.dev-guidelines-skills.json`   | Manifest filename inside each target skills folder   |
| `legacy_skill_names` | `array<string>` | Built-in legacy list or `[]`    | Bootstrap skill names owned before manifest creation |
| `replace_tools`      | `boolean`       | `false`                         | Replace default tools instead of merging `tools`     |
| `tools`              | `array<object>` | Built-in tool registry          | Additional or overridden tool registry entries       |

---

## Default Tool Registry
The built-in registry in [agent_files_config.py](../../src/support_python/tools/agent_files_config.py) defines three default entries:
- `claude-code` (alias `claude`) targets `~/.claude/CLAUDE.md` and `~/.claude/skills`.
- `antigravity` targets `~/.gemini/GEMINI.md` and `~/.gemini/config/skills`.
- `codex-cli` (alias `codex`) targets `~/.codex/AGENTS.md` and `~/.agents/skills`.
