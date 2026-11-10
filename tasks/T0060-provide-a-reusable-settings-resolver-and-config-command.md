---
id: T0060
owner: ~
needs: ['T0057', 'T0058']
branch: —
worktree: —
status: ready
started_at: —
ended_at: —
review: agent
preview: none
protocol: standard
---
# T0060: Provide a reusable settings resolver and config command group in support_python, per the configuration guidelines

## Goals
The dev-guidelines [Configuration Guidelines](https://github.com/gpellicciotta/dev-guidelines/blob/main/guidelines/configuration-guidelines.md) define setting precedence, file locations, and a standard `config` command group.
Give tools built on `ToolHarness` both in a few lines: declare the settings once, then resolve them and add `config`.
plan's `plan config` group is the reference behavior for the command shape.

Specifications: [technical-spec.md](T0060-provide-a-reusable-settings-resolver-and-config-command/technical-spec.md).
Completion check: `python -m pytest tests/test_config.py tests/test_config_actions.py` and `ruff check src tests`
Size estimate: 7 files, 700 lines

## Task Execution Steps
- [ ] **[Verify]**    Author the failing unit tests from the technical spec and record their failure output.
- [ ] **[Implement]** Add `Setting` and `SettingsSchema` declarations and a resolver applying the guideline precedence.
- [ ] **[Implement]** Add `add_config_actions` registering `path`, `list`, `names`, `get`, `set`, `delete`, and `edit`.
- [ ] **[Verify]**    Run the completion check and the integration scenario; record verbatim output.
- [ ] **[Doc]**       Add a configuration tutorial under `docs/tutorials/`, update `docs/requirements.md`, and CHANGELOG.md.
- [ ] **[Review]**    Obtain review approval of the finished work before completion.

## Execution Log
- [2026-11-10] **[Doc]**
  Companion task file scaffolded at task creation.
