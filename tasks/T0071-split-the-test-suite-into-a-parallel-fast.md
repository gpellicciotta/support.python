---
id: T0071
owner: ~
needs: []
branch: —
worktree: —
status: ready
started_at: —
ended_at: —
review: agent
preview: none
protocol: standard
---
# T0071: Split the test suite into a parallel fast default suite and a marked slow suite, with per-test timeouts

## Goals
Split the tests into a fast default suite and a slow suite, as the testing and Python guidelines require.
Add `pytest-xdist` and `pytest-timeout` to the `dev` extra, register a `slow` marker, and set `addopts` in pyproject.toml.
Mark integration, end-to-end, build, and subprocess tests, and any test over 5 seconds, as slow.
Make every remaining test safe under `-n auto`, fixing shared state that parallel runs expose.
Run both suites in CI, and keep the fast suite under 2 minutes.

## Task Execution Steps
- [ ] **[Read]**      Read the testing and Python guidelines, then record `pytest --durations=0` output as the baseline.
- [ ] **[Implement]** Add the dev extras, `slow` marker, and `addopts` to pyproject.toml.
- [ ] **[Verify]**    Run the default suite and record which tests fail or time out under `-n auto`.
- [ ] **[Implement]** Mark slow tests with `@pytest.mark.slow` and fix tests that share state.
- [ ] **[Implement]** Add a slow-suite step running `pytest -m slow --timeout=120` to python-package.yml.
- [ ] **[Verify]**    Run both suites, recording timings and verbatim output in validation-proof.md.
- [ ] **[Doc]**       Document both suites in devops.md and AGENTS.md, and add a CHANGELOG.md entry.
- [ ] **[Review]**    Obtain review approval of the finished work before completion.

## Execution Log
- [2026-11-10] **[Doc]**
  Companion task file scaffolded at task creation.
