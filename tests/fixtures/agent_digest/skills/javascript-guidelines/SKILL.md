---
name: javascript-guidelines
description: >-
  Guidelines and conventions for writing JavaScript/TypeScript code, modern
  project structure (ESM, package.json), ESLint Stroustrup formatting, Vitest, and
  dependencies. Use when editing, creating, or testing JavaScript or TypeScript
  projects.
---

# JavaScript Guidelines
Guidelines on writing JavaScript and TypeScript code and structuring JS/TS projects.

## Ecosystem Compliance
- Follow modern JavaScript and TypeScript ecosystem practices unless a concrete documented reason justifies deviation.
- Use Node.js LTS or specified runtime engines declared explicitly in `package.json` and CI workflows.

## Project Structure and Modules
- Use ECMAScript Modules (`import`/`export`) rather than CommonJS (`require`) for all new codebases.
- Maintain `package.json` as the single authoritative source of metadata, dependency versions, and lifecycle scripts.
- Resolve package version dynamically from `package.json` at runtime rather than hardcoding version strings.
- Place production source files under `src/` and automated tests under `tests/`.

## Code Style and Formatting
- Enforce Stroustrup brace formatting using ESLint Stylistic rule `@stylistic/brace-style` set to `['error', 'stroustrup']`.

## Supported Versions and Dependencies
- Declare semver dependency ranges in `package.json` and commit `package-lock.json` to version control.
- Run `npm ci` in continuous integration workflows to install dependencies reproducibly from `package-lock.json`.

## Testing and Quality
- Run formatting checks, linting, type-checking, tests, and build packaging in continuous integration.
- Standardize on Vitest for automated unit and integration test suites.
