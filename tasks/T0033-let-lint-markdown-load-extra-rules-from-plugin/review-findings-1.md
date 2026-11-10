---
task: T0033
round: 1
verdict: rejected
reviewer: "@claude-2"
reviewed_at: 2026-11-10T01:52:37Z
reviewed_commit: "8b35e40"
base_commit: "3db050a"
branch: task/T0033-let-lint-markdown-load-extra-rules-from-plugin
---
# Review Findings: Task T0033 (Round 1)

## Summary
Rejected for three small correctness defects in the new plugin path; the overall design is sound.
The loader, `plugins` key, `--plugin` option, `rules` action, and docs meet the stated goals.
Verification I ran on commit `8b35e40` with `PYTHONPATH=src`:
- `python -m pytest -q`: 773 passed, 3 skipped, 81 subtests passed, exit 0.
- `ruff check .` and `ruff format --check .`: clean.
- `lint-markdown check --offline` on changed docs: findings only in lines this diff did not touch.
- Manual runs in a temp project confirmed path plugins, `--rules X001`, JSON `rules` output, and exit-2 errors.

## Defects
1. Listing one plugin in config and in `--plugin` exits 2 with a spurious collision.
   - Repro: config `{"plugins": ["rules/no_todo.py"]}` plus `check --offline --plugin rules/no_todo.py notes.md`.
   - Output: `Plugin 'rules/no_todo.py': rule ID 'X001' is already registered`, exit 2.
   - Cause: `build_linter` calls `load_plugins` twice, so the resolved-path dedup does not span both sources.
   - The docs say entries may come from the config key, `--plugin`, "or both".
   - The same entry listed twice in one source loads once, so this behavior is inconsistent.
2. `rules` reports `source: builtin` for a plugin rule whose `rule_id` is not uppercase.
   - Repro: a plugin rule with `rule_id = "x002"`; `lint-markdown rules --plugin rules/lower.py` shows `x002 ... builtin`.
   - Cause: `load_plugins` keys `sources` by the registry's uppercased IDs.
   - `run_rules` then looks up the raw `rule.rule_id`.
3. `--config DIR` silently ignores the directory's `plugins` key.
   - Repro: `--config ..` pointing at a directory with `.lint-markdown.json`; X001 is not reported, exit 0.
   - Cause: `load_profile` resolves a directory to its config file, but `read_plugin_entries` returns `[]` for non-files.
   - `build_linter` also uses `resolved_cfg.parent` as the plugin base directory.
   - The docs describe `--config` as a file, so this is minor, but other settings apply while plugins vanish silently.

## Process Gaps
- `CLAUDE.md` was edited but not listed under Declared Files; the Execution Log notes it, which is acceptable.
- Otherwise none: red-phase proof, green-phase evidence, the size-overrun note, and the commit message all follow the guidelines.

## Required Rework
1. Deduplicate plugin entries across the config and `--plugin` sources by resolved path or module name.
   - Add a test proving the same plugin from both sources loads once and exits 1 reporting X001.
2. Key the `rules` source lookup consistently, for example by `rule.rule_id.strip().upper()`.
   - Add a test with a lowercase plugin rule ID expecting the plugin entry as its source.
3. Resolve a directory `--config` to its config file before reading plugin entries and choosing the base directory.
   - Alternatively, reject a directory `--config` with exit 2. Add a test either way.
