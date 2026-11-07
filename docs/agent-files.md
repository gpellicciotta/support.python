# Agent Files Synchronization

Deterministic synchronization of repository guideline digests and skills into installed AI coding tools.
Implemented in [agent_files.py](../src/support_python/agent_files.py) and configured via [agent_files_config.py](../src/support_python/agent_files_config.py).

---

## Command-Line Interface
Run actions through the unified CLI in [cli.py](../src/support_python/cli.py):
```bash
support-python agent-files list [--config PATH]
support-python agent-files sync [TOOL ...] [--config PATH] [--dry-run] [--no-prune]
support-python agent-files check [TOOL ...] [--config PATH]
support-python agent-files review [TOOL ...] [--config PATH] [--timeout SECONDS]
```

Supported configuration flags override JSON settings and built-in defaults:
- `--config PATH` loads explicit JSON settings from `PATH`.
- `--repo-root PATH` overrides the source repository root directory.
- `--digest PATH` overrides the source Markdown digest file path.
- `--skills-dir PATH` overrides the source skills directory path.
- `--marker NAME` sets the guarded block marker identifier.
- `--marker-begin TEXT` overrides the opening HTML comment marker line.
- `--marker-end TEXT` overrides the closing HTML comment marker line.
- `--manifest-source NAME` sets the ownership `source` recorded in skills manifests.
- `--legacy-skill NAME` replaces `legacy_skill_names` with the specified bootstrap skill name (repeatable).

---

## JSON Configuration Schema
When `--config` is omitted, the loader checks `agent-files.json` in the resolved repository root.
All relative paths in `agent-files.json` resolve against `repo_root`.
```json
{
  "repo_root": ".",
  "digest_path": "guidelines/agent-digest.md",
  "skills_dir": "skills",
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

| Field                | Type            | Default                       | Purpose                                              |
| :------------------- | :-------------- | :---------------------------- | :--------------------------------------------------- |
| `repo_root`          | `string`        | Config directory or Git root  | Base directory for relative paths and review runs    |
| `digest_path`        | `string`        | `guidelines/agent-digest.md`  | Source Markdown digest synced into target files      |
| `skills_dir`         | `string`        | `skills`                      | Source directory containing `<skill>/SKILL.md` trees |
| `marker`             | `string`        | `dev-guidelines`              | Identifier for guarded block comments                |
| `marker_begin`       | `string`        | Derived from `marker`         | Explicit opening guarded block line                  |
| `marker_end`         | `string`        | Derived from `marker`         | Explicit closing guarded block line                  |
| `manifest_source`    | `string`        | `dev-guidelines`              | Ownership tag written into the skills manifest       |
| `manifest_name`      | `string`        | `.dev-guidelines-skills.json` | Manifest filename inside each target skills folder   |
| `legacy_skill_names` | `array<string>` | Built-in legacy list or `[]`  | Bootstrap skill names owned before manifest creation |
| `replace_tools`      | `boolean`       | `false`                       | Replace default tools instead of merging `tools`     |
| `tools`              | `array<object>` | Built-in tool registry        | Additional or overridden tool registry entries       |

---

## Default Tool Registry
The built-in registry in [agent_files_config.py](../src/support_python/agent_files_config.py) defines three default entries:
- `claude-code` (alias `claude`) targets `~/.claude/CLAUDE.md` and `~/.claude/skills`.
- `antigravity` targets `~/.gemini/GEMINI.md` and `~/.gemini/config/skills`.
- `codex-cli` (alias `codex`) targets `~/.codex/AGENTS.md` and `~/.agents/skills`.
