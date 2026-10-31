# Versioned Changes

A summarized overview of all changes, per version of this project.

> Entries are in reverse chronological order, most recent at the top.
>
> A version actively being developed carries a `-pre` SemVer pre-release suffix on its heading (e.g.
> `## v0.1.1-pre`) instead of a status tag. Status codes used once a version leaves that state are:
> - `[{{date}}]` - frozen/finalized on {{date}}
> - `[released: {{date}}]` - released to package manager or production on {{date}}
> - `[broken]` - considered broken and not be used

---

## v1.0.1-pre

---

## v1.0.0 [released: 2026-10-31]

- CLI: Added `CliLogger` and `LogLevel` for guideline-compliant CLI logging with severity indicators and log files.
- CLI: Added `build_action_parser`, `print_version`, and `print_help` for action-oriented command-line tools.
- CLI: Added table rendering, file-backed session token storage, env-file parsing, and UTF-8 console setup.
- BackEnd: Added a stdlib-only REST transport with a typed error hierarchy and status-code mapping.
- BackEnd: Added wire date helpers, `WireEnum`, and standard server metadata models.
- BackEnd: Added a streaming SQL snapshot anonymizer with deterministic masking and custom table transformers.
- BackEnd: Added `ViewCaptureEngine` for headless-Chrome screenshots, an embedded static server, and UI tour reports.
- Security: Added standard password hashing and property decryption in `crypto`.
- DevEx: Added Docker, MySQL, server, mail, and Cloud SQL proxy managers plus `run_step` in `devops`.
- DevEx: Required explicit MySQL passwords and a Cloud SQL instance, with no built-in defaults.
- DevEx: Added bootstrap, devops, kill-processes, backup-git-repos, and release-notes scripts.
- Build: Added src-layout setuptools packaging for Python 3.9+, ruff linting, pytest, and GitHub Actions build and release.
- Docs: Documented the public API with Google-style docstrings, a README, requirements, and a DevOps guide.
