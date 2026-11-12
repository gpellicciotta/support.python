# Changelog version fallback

## Scope
Update release helpers, version tests, release pipeline tests, CLI action tests, integration coverage, the DevOps tutorial, and the changelog.
Use the first version heading only when no supported manifest exists.
Preserve manifest precedence and errors for manifests without versions.
Release freezing and reopening must edit the changelog once and stage it once.

### Tests
- Unit: Read and update changelog versions, preserve history and CRLF, and reject missing headings or versionless manifests.
- Integration: Execute version and versions entry points without manifests; exercise release freezing and reopening against temporary Git repositories.
