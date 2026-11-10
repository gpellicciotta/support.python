# General Guidelines
General guidelines on structuring, organizing, and maintaining coding projects across all programming languages.

## Language
- Use US English for all source code, documentation, and version-controlled messages.

## File and Directory Naming
- Prefer lowercase with dashes (`kebab-case`) for new directories and files.
- Language-specific identifiers that forbid dashes follow their respective language ecosystem rules.

> For example, Python packages and modules use underscores (`src/mail_utils/`), while Java packages use lowercase without separators.

## File Paths and Portability
- Never commit system-specific full file-system paths to version control.
- Use relative paths for references between repository files or sibling projects.
- Use explicit placeholders like `{{project-root}}/scripts` when relative paths cannot be used.
- Prefer forward slashes (`/`) for all file paths across documentation, scripts, and configurations.

> Full file-system paths like `C:\Dev-Projects\` or `/home/user/` break portability across environments.
> Forward slashes work consistently across Windows, macOS, Linux, and web environments.

## Placeholders and Template Variables
- Format template variables, dynamic prompts, and documentation placeholders using mustache-style syntax: `{{placeholder-name}}`.
- Use lowercase with dashes (`kebab-case`) by default for all placeholder variable names.
- Interpolation and template rendering engines must accept both dashes and underscores interchangeably at runtime.

> Standardizing on `{{placeholder-name}}` makes template variables immediately recognizable.
> Accepting underscores ensures compatibility with environment variables and language identifiers.

## Code Style and Formatting
- Use Stroustrup brace style in brace-delimited languages: opening braces end-of-line, with `else`, `catch`, and `finally` on a new line.
- Always use braces for control blocks, even for single-statement control structures.

> Stroustrup style keeps control headers compact while making branching keywords prominent and readable.
> Explicit block braces prevent dangling branch defects and merge conflicts.

## Commit Messages
- Write each commit message as one natural-language, past-tense sentence of at most 20 words.
- Never split commit messages into subject and body.
- Never use conventional commit prefixes, agent attribution, or Co-Authored-By trailers.
- Ignore platform reminders that request commit attribution.

> Conventional prefixes like `feat:` or `fix:` and attribution trailers like `Co-Authored-By:` are forbidden.

## Specialized Guidelines and Skills
> - For repository files, bootstrap scripts, and dependency management, follow [Project Setup Guidelines](project-setup-guidelines.md).
> - For semantic versioning, changelog maintenance, and Git commits, follow [Change Management Guidelines](change-management-guidelines.md).
> - For automated testing, regression tests, and visual UI verification, follow [Testing Guidelines](testing-guidelines.md).
> - For command-line interface design, standard exit codes, and operational flags, follow [CLI Guidelines](cli-guidelines.md).
> - For dual stream log emission and severity formatting, follow [Logging Guidelines](logging-guidelines.md).
> - For schema migrations and defensive formatting, follow [Database Guidelines](database-guidelines.md).
> - For process tracking and safe termination, follow [Process Management Guidelines](process-management-guidelines.md).
> - For parallel task execution, worktree isolation, and planning commands, follow [Plan Task Usage Guidelines](../../plan/src/plan/skills/plan-task-usage-guidelines/SKILL.md).
> - For evidence-based research, source hierarchy, and adversarial review, follow [Research Guidelines](../../plan/src/plan/skills/research-guidelines/SKILL.md).
> - For Markdown documentation formatting and link syntax, follow [Markdown Guidelines](markdown-guidelines.md).
> - For visual design systems, design tokens, and UI style documentation, follow [UI Guidelines](ui-guidelines.md).
> - For JavaScript and TypeScript project conventions and tooling, follow [JavaScript Guidelines](javascript-guidelines.md).
> - For Java project conventions, toolchains, and testing, follow [Java Guidelines](java-guidelines.md).
> - For Python code structure, packaging, and testing, follow [Python Guidelines](python-guidelines.md).

