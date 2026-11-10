---
skill:
  name: process-management-guidelines
  description: >-
    Rules and procedures for tracking, supervising, and safely terminating operating system processes.
    Use when launching background tasks, managing process lifecycles, or terminating running processes.
---

# Process Management Guidelines
Standards and procedures for supervising, tracking, and safely terminating operating system processes.

## Process Supervision and Lifecycle
- Keep background processes monitored until they exit cleanly or are explicitly stopped.
- In autonomous loops and unattended runs, terminate all spawned background processes before ending the turn.
- In interactive sessions, retain running services requested for inspection, reporting their PID and connection details.

> Monitoring background processes ensures tasks complete reliably without orphaned processes or leaked resources across execution turns.
> Unattended runs must clean up all background jobs, while interactive sessions may retain servers for manual evaluation.

## Safe Process Termination
- Supply one or more target process IDs as positional arguments to `plan processes kill`.
- Pass the `--force` flag for hard process termination when standard termination signals fail.
- Inspect `plan processes kill` output to confirm termination; exit code 0 also allows safely skipped protected processes.

> Inspecting command output confirms target processes actually terminated rather than being safely skipped by ancestor protection.
> The `plan processes kill` command inspects process ancestry and explicitly protects parent processes from accidental termination.

## CLI Usage Reference
- Terminate one or more processes gracefully:
  ```bash
  plan processes kill 1234 5678
  ```
- Forcefully terminate stubborn or unresponsive processes:
  ```bash
  plan processes kill 1234 --force
  ```
- Append operational termination logs to a file:
  ```bash
  plan processes kill 1234 --log-file .plan/logs/process.log
  ```

