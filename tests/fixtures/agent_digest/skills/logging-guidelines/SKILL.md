---
name: logging-guidelines
description: >-
  Standards for operational logging, dual stream emission, severity padding, and
  startup/exit banners. Use when adding, refactoring, or configuring logging in
  applications and scripts.
---

# Logging Guidelines
Standards for structuring, formatting, and emitting operational logs across application processes and automation scripts.

## Stream Emission and Destinations
- Direct operational logging output to standard console streams and optionally append to a log file.
- Provide a `--log-file` CLI option overriding any tool-specific default log file destination.
- Always pair `--log-file` with a `--log-level` CLI option setting the logging threshold.
- Standardize on four log levels: `DEBUG`, `INFO`, `WARN`, and `ERROR`, defaulting to `INFO`.
- The configured logging threshold filters standard console streams and log file destinations identically.
- Discard log messages with severity below the configured log level threshold.
- Direct `INFO` and `DEBUG` severity entries to stdout, directing `WARN` and `ERROR` entries to stderr.
- Emit machine-parseable command output directly to stdout without timestamp, severity, or origin prefixes.
- Emit startup details in a single multi-line message containing name, version, command, and configuration.
- Emit a completion summary upon process exit including runtime duration and final status.

## Formatting and Severity Indicators
- Prefix log file entries with UTC timestamp `[YYYY-MM-DD HH:MM:SS]`, severity indicator, and optional `<origin>`.
- All timestamps written to log files must strictly use UTC.
- Pad severity indicators with trailing spaces to a total width of 11 characters.
- Standard severity indicators are `**[ERROR]**`, `**[WARN]** `, `**[INFO]** `, and `**[DEBUG]**`.
- Format optional origin labels as `<origin>` separated by spaces following the severity indicator.
- Indent multi-line log entries with spaces matching the start column of the first line message.
- Omit timestamps from console streams, dropping the `INFO` severity indicator on stdout.
- Retain `**[DEBUG]**` indicators on stdout and `**[WARN]**` / `**[ERROR]**` indicators on stderr.

## Formatting Reference Examples
- Sample operational log file entry:
  ```text
  [2026-10-09 10:48:13] **[INFO]**  Starting devops runner v1.12.8-pre with configuration:
                                    - Task: T0107
                                    - Verbose: true
  ```
- Sample stdout entry for the same invocation:
  ```text
  Starting devops runner v1.12.8-pre with configuration:
  - Task: T0107
  - Verbose: true
  ```
- Sample warning entry on stderr with origin and continuation:
  ```text
  **[WARN]**  <worker> Configuration file missing optional cache directory
                       defaulting to temporary storage
  ```
- Sample debug entry on stdout:
  ```text
  **[DEBUG]** <worker> Cache lookup missed for key 'schema:v2'
  ```
