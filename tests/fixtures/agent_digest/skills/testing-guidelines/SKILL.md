---
name: testing-guidelines
description: >-
  Standards for automated unit, integration, CLI, and multi-modal UI verification.
  Use when writing tests, verifying bug fixes, running CLI tools, or inspecting
  user interfaces.
---

# Testing Guidelines
Standards and procedures for testing software reliably across unit, integration, CLI, and user interface layers.

## Core Testing Principles
- Write automated tests for all business logic, data transformations, and critical execution paths.
- Keep unit tests completely independent of external networks, services, and live credentials.
- Use isolated test databases and staging environments for integration tests.
- Separate side-effecting adapters for external interactions from core domain logic.

## Test-Driven Development
- Practice test-driven development (TDD) as a mandatory prerequisite for all new features and bug fixes.
- Specify explicit dedicated unit test cases and an integration or end-to-end test scenario in the task companion file.
- Author automated tests defining expected behavior or reproducing defects before writing production code.
- Execute tests and confirm they fail as expected, capturing failure output as red-phase proof.
- Implement only the minimal production code necessary to turn failing tests green.
- Verify all tests pass before refactoring and capturing final green-phase execution evidence.

## Root Cause Analysis and Regression Testing
- Analyze the root cause of every reported bug or failure before applying fixes.
- Implement an automated regression test reproducing the failure before writing the fix.
- Document untestable issues under `docs/issues/` following the `project-setup-guidelines` skill naming rules, recording follow-up tasks in `PLAN.md`.

## CLI End-to-End Testing
- Test CLI tools end-to-end by executing their actual entry points with realistic arguments.
- Never rely solely on mocked unit tests when verifying command-line tools and scripts.
- Present execution evidence for all tested CLI invocations as described under Execution Evidence.

## Execution Evidence
- Run the relevant automated test suite after the final code change unless loop-owned verification applies.
- Accept failing-first and affected-test runs as task evidence when a project's work loop owns full-suite verification.
- Inspect recorded affected-test evidence during review rather than rerunning entire test suites.
- Paste the verbatim terminal output of that run into the companion `validation-proof.md` file's `## Walkthrough & Validation` section.
- Precede each output block with the exact command line and its exit code.
- Use fenced `text` code blocks; never paraphrase, reformat, or reconstruct output from memory.
- Truncate long output to its final summary and all failure details, limited to 40 lines per block.
- Exclude omission markers from the 40-line evidence block limit.
- Mark every truncation with a line reading `[... {{n}} lines omitted ...]`.
- Apply these rules to every task that changes code, tests, scripts, or build configuration.
- For documentation-only tasks, paste the output of the applicable linter instead.
- For tasks without a task file, present the same evidence in the completion message.
- State explicitly when no automated test applies, and give the reason.

## Visual UI Verification
- Visually verify all user interface prototypes and components before requesting integration of changes affecting rendered output.
- Capture two screenshots for every visual change: one before the change and one after it.
- Store UI screenshots in `.plan/tasks/T{{nnnn}}-{{slug}}/`.
- For tasks without a task companion directory, present screenshots in the session and commit none.
- Link or embed screenshots in the task file Execution Log or visual verification section.
- Confirm the local server returns HTTP 200 before capturing screenshots.
- Inspect captures to ensure they show actual UI rather than blank pages or error screens.
- Inspect browser console logs, exceptions, and network responses during visual verification.
- Enforce a zero-tolerance gate failing on console.error output, unhandled exceptions, or rejected promises.
- Fail verification on any request failing at the network level or returning HTTP 400 or higher.
- Exempt expected errors or status codes by documenting them with rationale in the task verification section.
- Verify UI components in light and dark modes across responsive viewports specified in [playwright-recipes.md](references/playwright-recipes.md).
- In interactive sessions, leave the development server running and report its URL and PID in the completion message.
- In autonomous loops and unattended runs, stop the development server using `plan processes kill` before ending the turn.
- Use the harness in [playwright-recipes.md](references/playwright-recipes.md) for automated UI checks.
