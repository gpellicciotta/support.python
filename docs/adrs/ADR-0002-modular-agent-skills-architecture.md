# ADR-0002: Modular Guidelines and Mechanical Skill Derivation

> Originally recorded as ADR-0001 in dev-guidelines, and moved here with the `agent-digest` tool that implements it.
> Paths such as `guidelines/` and `skills/` refer to the dev-guidelines repository layout.

## Status
Accepted

## Context
As the repository's guidelines expanded to cover languages, testing, operations, database migrations, and planning workflows, `agent-digest.md` grew to 42,077 bytes.
When injected into agent instruction files (`~/.gemini/GEMINI.md`, `~/.claude/CLAUDE.md`, `~/.codex/AGENTS.md`), this exceeded prompt injection size limits across multiple AI coding tools:
- Gemini CLI and Antigravity enforce an injection cap of approximately 24 KiB, causing silent truncation of 19,056 bytes from `<RULE[user_global]>`.
- Claude Code produces warning diagnostics when project instruction files exceed 40 KiB.
- Codex CLI defaults `project_doc_max_bytes` to 32 KiB.

Human collaborators require detailed explanations, architectural rationale, code templates, and background notes in guideline documents.
Conversely, AI agents require token-dense, imperative directives and progressive disclosure so that domain-specific conventions are loaded only when relevant to the active task.

## Decision
1. **Size Budget for Core Digest**:
   Enforce a hard size budget of 20 KiB (`20,480` bytes) on `agent-digest.md`, validated in CI and checked by `agent-digest validate` (originally dev-guidelines' `generate-agent-digest.py validate`).
2. **Mechanical Skill Derivation (1:1)**:
   Derive agent skills mechanically from human guideline documents using YAML frontmatter in `guidelines/{{name}}.md`:
   ```yaml
   ---
   skill:
     name: {{name}}
     description: >-
       Actionable description of the skill and clear triggering conditions.
   ---
   ```
   Each guideline with `skill:` frontmatter produces `skills/{{name}}/SKILL.md` with identical naming (1:1 correspondence).
3. **Automatic Rationale Stripping**:
   Strip all markdown blockquotes (`>`) when generating skills and digest content, preserving human rationales in guideline docs while maximizing signal density for agents.
4. **Link Normalization and Installed Context**:
   Rewrite markdown links during generation so installed skills and the core digest never contain broken relative references:
   - Sibling guidelines defining a skill become `the `{{name}}` skill` with backticks and no link.
   - Sibling guidelines without a skill become link text only.
   - References within the same skill directory become skill-relative links (`{{path}}`).
   - Repository file references become canonical GitHub links: `[filename](https://github.com/gpellicciotta/dev-guidelines/blob/main/{{repo-relative-path}})`.
   - Absolute `http` and `https` links remain unchanged.

5. **Separation of Invariants vs. On-Demand Skills**:
   The core agent digest (`agent-digest.md`) retains only universal behavioral invariants: truthfulness, approval gates, command transparency, verbosity limits, and universal path/language standards.
   All domain-specific topics are extracted into dedicated guideline files and corresponding on-demand skills:
   - Language skills: `javascript-guidelines`, `python-guidelines`, `java-guidelines`, `markdown-guidelines`
   - Operational skills: `process-management-guidelines`, `testing-guidelines`, `cli-guidelines`, `logging-guidelines`, `database-guidelines`, `project-setup-guidelines`, `plan-task-usage-guidelines`, `change-management-guidelines`
6. **Co-location of Process Management**:
   Relocate `kill-processes.py` from `plan/scripts/` to `dev-guidelines/scripts/` so that process management tools and their governing guidelines reside together in the primary guidelines repository.

## Consequences
- **Prompt Size Reduction**: The core digest shrinks from 42 KiB to approximately 7 KiB, leaving more than 65% headroom below the 20 KiB cap.
- **Elimination of Context Truncation**: All AI coding tools receive the complete set of core safety invariants without truncation.
- **Single Source of Truth**: Human documentation and agent skills are authored and edited in one file per domain, preventing drift between human and AI rules.
- **Progressive Disclosure**: Agents inspect specialized skills only when executing tasks relevant to that domain, saving context window capacity for actual code and reasoning.
