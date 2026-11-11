# Specification: `agent-digest` Front-Matter

Front-matter format of the guideline files that `agent-digest` reads.
Implemented in [agent_digest.py](../../src/support_python/tools/agent_digest.py).
Usage is in [agent-digest.md](../tools/agent-digest.md).

---

## Placement
- Front-matter is optional.
- It starts on the first line of the file with `---` and ends at the next `---`.
- A file without it is plain digest content.
- `agent-digest check` reports an error for unknown keys.

## Keys
| Key                 | Type    | Required     | Meaning                                                    |
| :------------------ | :------ | :----------- | :--------------------------------------------------------- |
| `index`             | integer | no           | Sort position of the file in the digest; lower comes first |
| `skill`             | mapping | no           | Marks the file as a source of one derived skill            |
| `skill.name`        | string  | with `skill` | Skill name; the folder `{{skills-dir}}/{{name}}` holds it  |
| `skill.description` | string  | no           | Skill description, normally a folded block scalar          |
| `skill.references`  | list    | no           | Files next to the guideline copied into the skill folder   |

- A file with `skill` but no `skill.name` yields no skill.
- A non-integer `index` is an error.
- Top-level keys other than `index` and `skill` are errors.
- Keys under `skill` other than `name`, `description`, and `references` are errors.

## References
- Each entry is a relative POSIX path, such as `assets/template.md`.
- An entry must exist next to the guideline file.
- An entry may not be empty, absolute, drive-qualified, or use backslashes.
- An entry may not escape the guideline directory, repeat another entry, or name `SKILL.md`.
- A listed file that does not exist is reported as a `missing-reference` issue.

## Supported Syntax
The parser is strict and dependency-free; it accepts a small YAML subset:
- Top-level scalars: `index: 2`.
- Top-level mappings: `skill:` followed by two-space indented keys.
- Second-level scalars: `name: python-guidelines`.
- Second-level folded block scalars: `description: >-`, with the text indented four spaces.
- Second-level string lists: a bare key followed by four-space indented `- item` lines.
- Single or double quotes around scalars are stripped.
- Blank lines and `#` comment lines are skipped.

Everything else is an error, including inline collections such as `[a, b]` or `{a: 1}`.

## Example
```yaml
---
index: 2
skill:
  name: python-guidelines
  description: >-
    Guidelines and conventions for Python code, src/ layout, and pytest.
    Use when writing, editing, or testing Python code.
  references:
    - assets/pyproject-template.toml
---
```
