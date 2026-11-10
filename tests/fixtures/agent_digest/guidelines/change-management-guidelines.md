---
skill:
  name: change-management-guidelines
  description: >-
    Rules and conventions for semantic versioning, changelog management, changelog entry style, and atomic Git commits.
    Use when updating versions, writing changelog entries, or authoring Git commits.
---

# Change Management Guidelines
Standards and conventions for versioning, changelog maintenance, changelog entry composition, and Git commits.

## Semantic Versioning
- Use [Semantic Versioning](https://semver.org/) starting from version `0.1.0`.
- Apply the `v` prefix to changelog headings, Git tags, and CLI version strings.
- Never use the `v` prefix in package manifests or build configuration files.
- Maintain version, name, and vendor metadata in a single authoritative configuration file.
- Resolve runtime versions dynamically from package metadata rather than duplicating strings in source code.
- Fall back to `0.0.0+unknown` during direct source execution without package metadata.
- Append a `-pre` suffix to active in-development versions in `CHANGELOG.md` and build configuration.
- Append a plus sign and short commit hash (`+{{hash}}`) for dynamic build metadata at build or runtime.
- Never hardcode commit hashes in version files or changelog headings.
- Mark backward-incompatible changes clearly with `**[breaking]**` in `CHANGELOG.md`.
- Provide direct client migration instructions for simple changes like identifier renames.
- Create a dedicated migration guide under `docs/` for complex breaking architectural changes.
- Maintain multi-component repositories and client SDKs in lockstep versioning across all subprojects.
- Synchronize version identifiers across all package manifests whenever bumping versions in a repository.
- Verify version parity across all components as an automated pre-flight check before deploying.

> Dynamic version resolution falls back to `0.0.0+unknown` outside packaged distributions.
> Lockstep versioning ensures client SDKs, services, and shared libraries remain mutually compatible across releases.

## Changelog Management
- Maintain exactly one active in-development `-pre` heading at the top of `CHANGELOG.md`.
- Record all unreleased changes under the top active `-pre` heading in reverse chronological order.
- Let `plan` task completion bump the version; it raises the patch in the manifest and the top `-pre` heading.
- Never edit the manifest version or the `-pre` heading number yourself; only add changelog bullets.
- Bump the minor or major version only when the user explicitly asks for it.
- Allow any change while the major version is `0`, breaking ones included, without bumping to `1.0.0`.
- Mark breaking changes with `**[breaking]**` in every version, including `0.x.y` versions.
- Resolve parallel heading renumbering conflicts at merge time by choosing the higher version number.
- Never create multiple `-pre` headings for unreleased changes.
- Replace the `-pre` suffix with a status tag upon finalizing or releasing a version.
- Use date format `YYYY-MM-DD` in all release heading status tags.
- Use `[{{date}}]` for versions frozen on that date without external distribution (e.g. `## v1.11.0 [2026-09-18]`).
- Use `[released: {{date}}]` for versions published externally (e.g. `## v1.11.0 [released: 2026-09-18]`).
- Use `[broken]` for versions considered broken, retracted, or unsafe to use (e.g. `## v1.11.0 [broken]`).
- Append deployment target revision `[{{platform}}: {{revision}}]` to release headings when deploying services.
- Finalized version entries in `CHANGELOG.md` are strictly immutable; never edit, add, or delete entries once finalized.
- Retain entry immutability while permitting heading status tag updates, such as appending `[broken]`.
- Atomically finalize the current version and create the next patch `-pre` heading when cutting releases.
- Create an active in-development heading at the next patch version if one is missing.

> Heading status tag examples:
> - Frozen: `## v1.11.0 [2026-09-18]`
> - Released: `## v1.11.0 [released: 2026-09-18]`
> - Broken: `## v1.11.0 [2026-09-18] [broken]`
> - Service deployment: `## v5.3.0 [2026-09-29] [released: 2026-09-29] [google-cloud-run: counters-00148-mvd]`
> Patch bumps happen continuously while still `-pre`: `plan` raises the patch once per completed task.
> A `0.x.y` version never moves to `1.0.0` because of a breaking change; only the user decides to release `1.0.0`.
> Finalized release entries record historical deliverables and must never be modified retrospectively.

## Changelog Entry Style
- Record core product, tool, library, and operational deliverables only.
- Exclude decisions, planning, and administrative work from `CHANGELOG.md`.
- Never reference task identifiers, commit hashes, pull requests, or internal tracking metadata in changelog bullets.
- Consolidate active version entries affecting the same artifact or scope into a single cohesive bullet.
- Describe net version-to-version deliverables rather than intermediate implementation steps or turn actions.
- Ensure changelog entries enable human readers to quickly grasp what changed since the previous release.
- Focus bullets on externally visible behavior and practical developer benefits.
- Restrict each change note to a single concise sentence capped at 20 words.
- Format release bullets as `Area: Past-tense-verb concise description of outcome`.
- Standard area categories include `BackEnd`, `FrontEnd`, `DevEx`, `Build`, `Docs`, `CLI`, `Config`, and `Security`.
- Projects may declare custom domain-specific area categories in their changelog header.
- Format local project file references in `CHANGELOG.md` as valid Markdown links.
- Wrap code references such as variable, function, class, and flag names in backticks.

> Changelog entries describe permanent deliverables for consumers and future maintainers.
> Ephemeral tracking markers like task IDs or commit hashes become meaningless noise after code merges to mainline.

## Version Control and Commits
- Maintain all project source code under version control.
- Never commit secrets, credentials, or private sensitive data to version control.
- Keep commits atomic and focused on a single logical change or task.
- Never bundle unrelated bug fixes, refactorings, or peripheral edits into the same commit.
- Omit self-evident diffs, file lists, and problem restatements from commit messages.
- Run linters on created or edited files before committing, fixing all reported issues first.

> Commits must represent a single coherent unit of work to enable clean bisection, review, and rollbacks.
