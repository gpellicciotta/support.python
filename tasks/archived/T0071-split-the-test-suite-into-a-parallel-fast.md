---
id: T0071
owner: "@gemini"
session: antigravity-20261111-d45aa9
needs: []
branch: task/T0071-split-the-test-suite-into-a-parallel-fast
worktree: .plan/work/T0071-split-the-test-suite-into-a-parallel-fast
status: completed
started_at: "2026-11-10T23:05:37Z"
ended_at: "2026-11-10T23:38:50Z"
review: agent
preview: none
protocol: standard
usage:
  worker: {turns: 4, duration_s: 3566.4, input: 3551514, output: 158186, cache_read: 68283802}
  review: {turns: 4, duration_s: 310.4, input: 52, output: 7586, cache_read: 900790, cache_write: 97698}
review_status: approved
review_round: 2
work_duration: 1992.2
reviewed_by: "@claude"
completion-commit: 2015bb6ef5c2cbbe582258303a9f13385905f2d2
---
# T0071: Split the test suite into a parallel fast default suite and a marked slow suite, with per-test timeouts

## Goals
Split the tests into a fast default suite and a slow suite, as the testing and Python guidelines require.
Add `pytest-xdist` and `pytest-timeout` to the `dev` extra, register a `slow` marker, and set `addopts` in pyproject.toml.
Mark integration, end-to-end, build, and subprocess tests, and any test over 5 seconds, as slow.
Make every remaining test safe under `-n auto`, fixing shared state that parallel runs expose.
Run both suites in CI, and keep the fast suite under 2 minutes.

## Task Execution Steps
- [x] **[Read]**      Read the testing and Python guidelines, then record `pytest --durations=0` output as the baseline.
- [x] **[Implement]** Add the dev extras, `slow` marker, and `addopts` to pyproject.toml.
- [x] **[Verify]**    Run the default suite and record which tests fail or time out under `-n auto`.
- [x] **[Implement]** Mark slow tests with `@pytest.mark.slow` and fix tests that share state.
- [x] **[Implement]** Add a slow-suite step running `pytest -m slow --timeout=120` to python-package.yml.
- [x] **[Verify]**    Run both suites, recording timings and verbatim output in validation-proof.md.
- [x] **[Doc]**       Document both suites in devops.md and AGENTS.md, and add a CHANGELOG.md entry.
- [x] **[Review]**    Obtain review approval of the finished work before completion.

## Execution Log
- [2026-11-10] **[Doc]**
  Companion task file scaffolded at task creation.

- [2026-11-11] **[Read]**
  Read guidelines and recorded serial baseline durations.
  - 1243 passed in 313.7s.
  - Slowest tests subprocess git release.

- [2026-11-11] **[Implement]**
  Added dev extras, slow marker, and addopts to pyproject.toml.
  - dev extra has pytest-xdist and pytest-timeout.
  - addopts sets parallel auto and slow exclusion.

- [2026-11-11] **[Verify]**
  Ran default suite under -n auto and recorded zero failures or timeouts.
  - 1243 passed on 8 workers in 113.8s.
  - No tests failed or timed out.

- [2026-11-11] **[Implement]**
  Marked slow integration and subprocess tests across 12 modules.
  - 159 slow tests marked with pytest.mark.slow.
  - Fast suite now runs in 17.4s.

- [2026-11-11] **[Implement]**
  Added slow-suite step to python-package.yml CI workflow.
  - CI runs fast suite then slow suite.
  - pytest -m slow --timeout=120 added.

- [2026-11-11] **[Verify]**
  Verified fast suite and slow suite, recording verbatim proofs.
  - Fast suite passed in 16.98s.
  - Slow suite passed in 60.48s.

- [2026-11-11] **[Doc]**
  Documented fast and slow suites in devops.md, AGENTS.md, and CHANGELOG.md.
  - Documented parallel fast suite.
  - Documented slow suite command and CI.

- [2026-11-11] **[Review]**
  Round 1 requested (mode: agent).

- [2026-11-11] **[Review]**
  Round 1 rejected by @claude: Implementation meets the core goals.
  - Findings: [review-findings-1.md](T0071-split-the-test-suite-into-a-parallel-fast/review-findings-1.md).

- [2026-11-11] **[Doc]**
  Restored build bullet in devops.md and test selection in AGENTS.md.
  - devops.md build bullet restored.
  - AGENTS.md test selection restored.

- [2026-11-11] **[Verify]**
  Re-verified fast and slow suites, updating verbatim outputs.
  - Fast suite passed in 17.25s.
  - Slow suite passed in 58.01s.

- [2026-11-11] **[Review]**
  Round 2 requested (mode: agent).

- [2026-11-11] **[Review]**
  Round 2 approved by @claude: Round 1 rework is complete.
  - Findings: [review-findings-2.md](T0071-split-the-test-suite-into-a-parallel-fast/review-findings-2.md).

- [2026-11-11] **[Complete]**
  Task completed successfully.

