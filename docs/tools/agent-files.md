# Agent Files Synchronization

Deterministic installation of an existing agent digest and skills directory into installed AI coding tools.
`agent-files` never generates or refreshes the digest; run [agent-digest](agent-digest.md) first.
Implemented in [agent_files.py](../../src/support_python/tools/agent_files.py) and configured via [agent_files_config.py](../../src/support_python/tools/agent_files_config.py).
Specifications: [config file](../specs/config-agent-files.md) and [JSON output](../specs/json-output.md).

---

## Command-Line Interface
Run actions through the `agent-files` console script in [agent_files.py](../../src/support_python/tools/agent_files.py):
```bash
agent-files list [--format text|json] [--config PATH]
agent-files sync [TOOL ...] [--format text|json] [--config PATH] [--dry-run] [--no-prune]
agent-files check [TOOL ...] [--format text|json] [--config PATH]
agent-files review [TOOL ...] [--config PATH] [--timeout SECONDS]
agent-files config [list|names|path|get|set|delete|edit] [NAME] [VALUE] [--user|--system] [--format text|json]
```

Supported configuration flags override environment variables, files, and built-in defaults:
- `--config PATH` loads settings from `PATH` only, instead of the discovered files.
- `--format text|json` selects text or JSON output on `list`, `sync`, and `check` (default: `text`); see [JSON Output](#json-output-in-sync-and-check).
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

## Configuration
Settings resolve in this order, and the first valid value wins:
1. Command-line option.
2. Environment variable `AGENT_FILES_{{SETTING}}`, such as `AGENT_FILES_MARKER`.
3. Project file `.agent-files.json` in the repository root, falling back to `agent-files.json` with a deprecation warning (removed in `v3.0.0`).
4. User file `agent-files/config.json` in the user configuration folder (`%APPDATA%` on Windows, `$XDG_CONFIG_HOME` or `~/.config` elsewhere).
5. System file `%PROGRAMDATA%/agent-files/config.json` on Windows, `/etc/agent-files/config.json` elsewhere.
6. Built-in default.

`tools` is the exception: its entries merge across all sources by tool name, and the highest source wins for each name.
Unknown keys are ignored and listed in `--debug` output.
A malformed file or a wrongly typed value logs one warning and falls through to the next source.
`--config PATH` replaces the three files; a missing `PATH` exits `2`.
Keys accept dashes or underscores interchangeably; this document shows the preferred kebab-case spelling.
A relative `repo-root` resolves against the folder of the file that sets it; other relative paths resolve against `repo-root`.
List values in the environment are comma-separated or a JSON array; `tools` is a JSON object.
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
  "tools": {
    "cursor-agent": {
      "command": "cursor",
      "target-file": "~/.cursor/rules.md",
      "skills-dir": "~/.cursor/skills",
      "native-skill-discovery": true,
      "aliases": ["cursor"]
    }
  }
}
```

| Setting              | Type            | Default                         | Environment variable                | Purpose                                                |
| :------------------- | :-------------- | :------------------------------ | :---------------------------------- | :----------------------------------------------------- |
| `repo-root`          | `string`        | Project file folder or Git root | `AGENT_FILES_REPO_ROOT`             | Base directory for relative paths and review runs      |
| `digest-path`        | `string`        | `{{repo-root}}/agent-digest.md` | `AGENT_FILES_DIGEST_PATH`           | Existing Markdown digest synced into target files      |
| `skills-dir`         | `string`        | `{{repo-root}}/agent-skills`    | `AGENT_FILES_SKILLS_DIR`            | Source directory containing `{{skill}}/SKILL.md` trees |
| `marker`             | `string`        | `dev-guidelines`                | `AGENT_FILES_MARKER`                | Identifier for guarded block comments                  |
| `marker-begin`       | `string`        | Derived from `marker`           | `AGENT_FILES_MARKER_BEGIN`          | Explicit opening guarded block line                    |
| `marker-end`         | `string`        | Derived from `marker`           | `AGENT_FILES_MARKER_END`            | Explicit closing guarded block line                    |
| `manifest-source`    | `string`        | `dev-guidelines`                | `AGENT_FILES_MANIFEST_SOURCE`       | Ownership tag written into the skills manifest         |
| `manifest-name`      | `string`        | `.dev-guidelines-skills.json`   | `AGENT_FILES_MANIFEST_NAME`         | Manifest filename inside each target skills folder     |
| `legacy-skill-names` | `array<string>` | Built-in legacy list or `[]`    | `AGENT_FILES_LEGACY_SKILL_NAMES`    | Bootstrap skill names owned before manifest creation   |
| `replace-tools`      | `boolean`       | `false`                         | `AGENT_FILES_REPLACE_TOOLS`         | Replace default tools instead of merging `tools`       |
| `tools`              | `object`        | Built-in tool registry          | `AGENT_FILES_TOOLS`                 | Tool definitions by name, merged across sources        |

The file keys `digest` and `skills` are accepted for `digest-path` and `skills-dir`.
A file may also give `tools` as an array of objects that each carry a `name`.
An invalid tool definition, an empty string setting, or an unknown tool key exits `2`.

### Config Command
`agent-files config` inspects and changes the settings; see the [configuration tutorial](../tutorials/configuration.md) for the shared actions.
It targets the project file `.agent-files.json` in the Git root of the current directory; pass `--user` or `--system` for the other files.
```bash
agent-files config list --format json
agent-files config set marker my-rules
agent-files config set replace-tools true --user
agent-files config path --all
```

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

## JSON Output in `sync` and `check`
`sync --format json` and `check --format json` print one JSON array on `stdout`, one entry per selected tool, for exit codes `0` and `1`:
```json
[
  {
    "tool": "claude-code",
    "status": "synced",
    "changes": [
      "instructions file updated: ~/.claude/CLAUDE.md",
      "skill 'python-guidelines' updated: missing file in target: SKILL.md"
    ]
  }
]
```

- `status` is `up-to-date`, `synced`, `changes-pending`, `failed`, or `unavailable`.
- `synced` (`sync`) lists the applied changes; `changes-pending` (`check` and `sync --dry-run`) lists the planned ones.
- `failed` means a write or deletion failed; the failure is the last entry of `changes`.
- `unavailable` means a target file cannot be read or has invalid guarded-block markers.
- `sync --dry-run` writes nothing and reports exactly as `check` does.
- Log messages go to `stderr`; a missing digest or invalid arguments print nothing on `stdout`.

---

## Default Tool Registry
The built-in registry in [agent_files_config.py](../../src/support_python/tools/agent_files_config.py) defines three default entries:
- `claude-code` (alias `claude`) targets `~/.claude/CLAUDE.md` and `~/.claude/skills`.
- `antigravity` targets `~/.gemini/GEMINI.md` and `~/.gemini/config/skills`.
- `codex-cli` (alias `codex`) targets `~/.codex/AGENTS.md` and `~/.agents/skills`.
