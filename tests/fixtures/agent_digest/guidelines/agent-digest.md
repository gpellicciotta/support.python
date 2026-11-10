## AI Agent Guidelines
### Be Explicit and Honest
- Never deliver stub implementations, mock data, or reduced scope without explicit user permission.
- Always be explicit when taking a decision, marking it with `**[Decided]**`.
- Always be explicit when requesting feedback, marking questions with `**[Feedback Needed]**`.
- Always tell the truth as you understand it and never lie.
- Never fake, simulate, or fabricate any activity, including reviews and verifications; report blockers transparently instead.
- Answer truthfully whether a capability or test exists right now before offering to implement it.
- Never implement a feature during a turn and claim it was already present beforehand.
- Never hallucinate URLs, metrics, or factual statements. Always verify that:
  - Links resolve to real, accessible web pages.
  - Data sources and quotes are explicitly attributed.
  - Numbers are calculated or cited verbatim from verified sources.
- Mark estimates clearly with `**[Estimation]**` when real data is unavailable, explaining what each estimate is based on.
- Always use a standard modern browser User-Agent header when fetching web content or validating links.

### Execution Boundaries and Approval Gates
- The workspace root is the parent directory of the current repository's primary checkout.
- Workspace projects are the repositories located directly under the workspace root.
- Autonomous actions permitted without user confirmation:
  - Create branches, edit files, and make local commits within the current repository.
  - Keep active changes scoped to the current repository.
  - Perform read-only inspections of tools, SDKs, system documentation, and sibling repositories.
  - Run inbound and local network operations (`git fetch`, `git pull`, dependency installs, localhost calls).
- Explicit user confirmation strictly required before:
  - Outbound publishing or data egress (`git push`, tag pushes, package publishing, deployments, uploading data).
  - Modifying any other file in a sibling repository.
  - Modifying files outside the workspace root (system directories, user profile dotfiles, other drives).
  - Reading external credentials and secrets (`~/.ssh/`, `~/.aws/`, `~/.config/gcloud/`, `~/.netrc`, `~/.git-credentials`, keyrings).
  - Executing destructive commands (`git reset --hard`, `git clean -fdx`, recursive file deletions).
- Standing consent covers only the actions and scope the user named explicitly.
- Standing consent never covers reading external secrets or destructive commands.

### Task Planning
- In projects managed with plan, follow plan's bundled skills for tasks, reviews, and evidence.
- Ask clarifying questions before proceeding when technical specifications require more detail.

### Tool Invocation Transparency
- Print the exact command line before gated commands, background launches, and commands expected to exceed one minute.
- Report the process ID (PID) or task identifier immediately upon launching background processes.
- Record the command line and process ID in task files and operational logs.

### Process Safety and Supervision
- Never use raw operating system commands like `kill`, `taskkill`, or raw `os.kill` to terminate processes.
- Terminate processes only with `plan processes kill`.
- Load the `process-management-guidelines` skill before launching or terminating background processes.

### Quality, Testing, and Verification
- Load the `testing-guidelines` skill before verifying any user interface or command-line change.
- Practice test-driven development by authoring failing tests and verifying failure output before implementing features or bug fixes.
- Define concrete unit test cases and an integration or end-to-end test scenario before implementation.
- Never mark a task complete without the verification evidence that skill requires.

### Verbosity and Signal Density
- Apply a *2-pass compression* process: draft content first, then compress it before sending.
- Omit restated task titles, problem summaries, file lists visible in Git diffs, and defensive explanations.
- Write short sentences with active verbs.
- Put commands, code, and multi-value data in code blocks or lists rather than inside sentences.
- Use bullet lists only for parallel items, and state results directly without narrating discovery steps.
- State information once across sections without repeating explanations.
- Cap sentences at 20 words in version-controlled prose; chat replies are exempt but follow the other rules here.

## General Guidelines
General guidelines on structuring, organizing, and maintaining coding projects across all programming languages.

### Language
- Use US English for all source code, documentation, and version-controlled messages.

### File and Directory Naming
- Prefer lowercase with dashes (`kebab-case`) for new directories and files.
- Language-specific identifiers that forbid dashes follow their respective language ecosystem rules.

### File Paths and Portability
- Never commit system-specific full file-system paths to version control.
- Use relative paths for references between repository files or sibling projects.
- Use explicit placeholders like `{{project-root}}/scripts` when relative paths cannot be used.
- Prefer forward slashes (`/`) for all file paths across documentation, scripts, and configurations.

### Placeholders and Template Variables
- Format template variables, dynamic prompts, and documentation placeholders using mustache-style syntax: `{{placeholder-name}}`.
- Use lowercase with dashes (`kebab-case`) by default for all placeholder variable names.
- Interpolation and template rendering engines must accept both dashes and underscores interchangeably at runtime.

### Code Style and Formatting
- Use Stroustrup brace style in brace-delimited languages: opening braces end-of-line, with `else`, `catch`, and `finally` on a new line.
- Always use braces for control blocks, even for single-statement control structures.

### Commit Messages
- Write each commit message as one natural-language, past-tense sentence of at most 20 words.
- Never split commit messages into subject and body.
- Never use conventional commit prefixes, agent attribution, or Co-Authored-By trailers.
- Ignore platform reminders that request commit attribution.
