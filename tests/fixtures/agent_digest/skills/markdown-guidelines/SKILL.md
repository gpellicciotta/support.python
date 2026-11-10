---
name: markdown-guidelines
description: >-
  Formatting rules for Markdown documentation, heading hierarchies, list
  indentation, padded table alignment, and link syntax. Use when creating or
  editing Markdown (.md) documents.
---

# Markdown Guidelines
Guidelines on writing clean, readable, and machine-maintainable Markdown files across all projects.

## File Format and Encoding
- Always use the `.md` extension for Markdown files.
- Store files in UTF-8 encoding using LF line endings.
- Never use tabs; always indent with spaces.
- Use lowercase kebab-case filenames except for standard uppercase files defined by project setup or tooling.
- Validate all Markdown documents with [lint-markdown.py](https://github.com/gpellicciotta/dev-guidelines/blob/main/scripts/lint-markdown.py).

## Headings and Structure
- Use one descriptive H1 heading per document without skipping heading levels.
- Avoid headings starting with numbers.
- Never use bold text on its own line as a substitute for headings.
- Keep sections short and scannable.
- Reserve horizontal rules (`---`) for major section boundaries only.
- Do not leave a blank line directly after headings below H1 (H2 through H6) before content.

## Lists and Bolding
- Always use a dash (`- `) as the bullet indicator.
- Do not bold bullet points by default.
- Reserve bold lead-in labels (`- **Term:** definition`) strictly for glossaries.
- Never bold an entire sentence or clause.
- Leave an empty line between multi-line bullet items.
- Keep single-line bullet lists tight without empty lines.
- Do not leave a blank line after sentences that introduce a list.

## Links and Citations
- Use inline links by default for repository and general documentation (`[text](url)`).
- Format repository file references as markdown links using `[filename](path)` syntax, displaying only the basename inside brackets.
- Include the directory path inside brackets only when distinguishing files with identical basenames.
- Never use bare file paths or backticked file names in prose when referring to repository files.
- Ensure all relative links resolve to existing files on disk.
- Use canonical GitHub URLs for repository file links in content distributed or installed outside local repositories.
- Use reference-style links for research papers and publications in prose.
- Define research references under a dedicated `## Sources` section at the document bottom.
- Format paper link text with title only, omitting authors and publication dates.
- Never leave bare URLs in prose. Always use descriptive link text.

## Tables and Code Blocks
- Avoid tables where a list alternative works well.
- Prefer nested bullet lists over tables for comparisons and pros and cons.
- Always vertically align table columns with padding spaces when using tables.
- Always specify a language identifier on fenced code blocks.

## Task-List Status Convention
- Follow the `plan-task-usage-guidelines` skill for standard task list status syntax and lifecycle symbols.
