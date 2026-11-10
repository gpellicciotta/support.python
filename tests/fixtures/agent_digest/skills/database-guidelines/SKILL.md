---
name: database-guidelines
description: >-
  Rules for database schema migrations, canonical column casing inspection,
  staging validation, and defensive consumer fallbacks. Use when writing
  migrations, altering schemas, querying databases, or handling serialized models.
---

# Database Guidelines
Standards and procedures for managing database schema migrations, inspecting canonical casing, and building defensive consumers.

## Schema Migrations and Staging Validation
- Treat all database schema changes as versioned migrations rather than manual table creation statements.
- Inspect canonical production data to verify exact column names and JSON key casing before writing migrations.
- Test migration scripts against isolated staging datasets before executing them against production databases.
- Validate migrations end-to-end through consuming applications to ensure full runtime and serialization compatibility.
- Verify rollback procedures before executing forward migrations against production systems.

## Defensive Formatting and Fallbacks
- Ensure serializers, deserializers, and parser utilities handle missing, null, or undefined fields safely.
- Provide safe fallback values for low-level UI utilities, date formatters, and numeric parsers.
- Never allow unexpected null database values or omitted payload fields to crash consumer interfaces.
