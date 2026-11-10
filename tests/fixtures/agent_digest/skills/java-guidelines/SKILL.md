---
name: java-guidelines
description: >-
  Guidelines and conventions for Java code, Gradle wrapper and toolchains,
  buildSrc plugins, and JUnit platform testing. Use when writing, editing, or
  configuring Java projects.
---

# Java Guidelines
Guidelines on writing Java code and structuring Java projects.

## Starting Projects
- Start Java projects from [java-project-template](https://github.com/gpellicciotta/java-project-template.git).

## Ecosystem Compliance
- Follow active Java ecosystem practices unless a concrete documented reason justifies deviation.

## Build and Toolchain
- Use Gradle with a pinned wrapper to ensure reproducible local and CI builds.
- Declare the target JDK explicitly using a Java toolchain.
- Keep the toolchain, CI environment, container image, and documented prerequisites aligned.
- Begin with a single Gradle module until a distinct second module is necessary.
- Share multi-project build logic with Groovy convention plugins in `buildSrc/` rather than repeating configuration.
- Stamp `Implementation-Title`, `Implementation-Version`, and `Implementation-Vendor` into JAR manifest attributes during packaging.
- Resolve runtime versions dynamically via `Package.getImplementationVersion()` rather than hardcoding strings.

## Project Structure
- Use `src/main/java` for production code and `src/test/java` for tests, with matching package structures.
- Separate application and library modules when responsibilities, dependencies, or release requirements differ.
- Keep public API dependencies separate from implementation dependencies in libraries.
- Document package responsibilities, design rationale, and API versus SPI boundaries in `package-info.java`.

## Code Style and Documentation
- Document all public API surface with Javadoc, including classes, interfaces, records, enums, constants, fields, and methods.

## Dependencies
- Use centrally managed, reproducibly resolved dependency versions.
- Avoid dynamic version specifications such as `1.+` or `1.6.+` in build files.

## Testing and Quality
- Run formatting, static analysis, unit tests, integration tests, and packaging checks in CI.
- Standardize on a single JUnit generation and test platform within a project.
- For Gradle 9+, declare `testRuntimeOnly 'org.junit.platform:junit-platform-launcher'` alongside JUnit Jupiter dependencies.
- Configure `testLogging.showStandardStreams = true` in Gradle test blocks to stream test output directly to console.

## Configuration and Operations
- Test configuration path resolution explicitly across environments.
- Derive application, artifact, container, and deployment versions from one authoritative value.
