## Walkthrough & Validation

### Key Changes
- `ServiceActions` registers the `docker`, `db`, `server`, `mail`, and `client` groups on a `ToolHarness`.
- `DevopsCli.add_services(...)` registers a group only when its manager is supplied.
- The first positional argument selects the sub-action; unknown sub-actions exit 2.
- `LocalVerifier.run_all_checks()` backs `client verify` and `server start --verify`.

### Red Phase
Command: `../../../.venv/Scripts/python -m pytest -q tests/test_devops_service_actions.py` (exit 1)

```text
[... 34 lines omitted ...]
FAILED tests/test_devops_service_actions.py::MailGroupTests::test_test_emails_takes_a_positional_recipient
FAILED tests/test_devops_service_actions.py::ClientGroupTests::test_verify_deployment_defaults
FAILED tests/test_devops_service_actions.py::ClientGroupTests::test_verify_deployment_options
FAILED tests/test_devops_service_actions.py::ClientGroupTests::test_verify_deployment_without_a_url_exits_2
FAILED tests/test_devops_service_actions.py::ClientGroupTests::test_verify_runs_all_checks
FAILED tests/test_devops_service_actions.py::RegistrationTests::test_group_help_lists_the_options
FAILED tests/test_devops_service_actions.py::RegistrationTests::test_groups_are_absent_without_their_manager
FAILED tests/test_devops_service_actions.py::RegistrationTests::test_help_lists_the_groups_and_sub_actions
FAILED tests/test_devops_service_actions.py::RegistrationTests::test_no_managers_adds_no_actions
FAILED tests/test_devops_service_actions.py::RegistrationTests::test_unknown_sub_action_exits_2
FAILED tests/test_devops_service_actions.py::LocalVerifierRunAllChecksTests::test_fails_fast_when_nothing_listens
FAILED tests/test_devops_service_actions.py::LocalVerifierRunAllChecksTests::test_passes_when_every_check_passes
FAILED tests/test_devops_service_actions.py::LocalVerifierRunAllChecksTests::test_runs_every_check
FAILED tests/test_devops_service_actions.py::DockerStatusIntegrationTests::test_real_docker_status_reports_without_starting_anything
48 failed in 3.40s
```

Command: `... pytest -q tests/test_devops_service_actions.py 2>&1 | grep -E "^E  +(AttributeError|AssertionError)" | sort | uniq -c` (exit 0)

```text
     44 E               AttributeError: Mock object has no attribute 'run_all_checks'
      1 E           AttributeError: 'DevopsCli' object has no attribute 'add_services'
      3 E       AttributeError: 'LocalVerifier' object has no attribute 'run_all_checks'
```

### Green Phase
Command: `../../../.venv/Scripts/python -m pytest -q tests/test_devops_service_actions.py` (exit 0)

```text
................................................                [100%]
48 passed, 9 subtests passed in 2.06s
```

### Full Suite
Command: `../../../.venv/Scripts/python -m pytest -q 2>&1 | tail -4` (exit 0)

```text
........................................................................................................................................................................................... [ 85%]
................................................................................................ [ 94%]
........................................................             [100%]
1023 passed, 3 skipped, 114 subtests passed in 146.80s (0:02:26)
```

### Lint
Command: `../../../.venv/Scripts/python -m ruff check . && ../../../.venv/Scripts/python -m ruff format --check .` (exit 0)

```text
All checks passed!
143 files already formatted
```

### Integration: Real Docker Status
Command: `PYTHONPATH=src ../../../.venv/Scripts/python -c "...DevopsCli(...).add_services(docker=LocalDockerManager()); cli.run(['docker', 'status'])"` (exit 0)

```text
Starting devops v2.0.26-pre+026879e with configuration:
- Command: docker
- Log file: none
- Log level: INFO
- Verbose: false
Docker Engine: NOT-INSTALLED
Finished devops docker in 0.0s with status: succeeded
```

### End to End: Unknown Sub-Action
Command: `PYTHONPATH=src ../../../.venv/Scripts/python -c "...cli.run(['docker', 'bogus'])"` (exit 2)

```text
**[ERROR]** argument subaction: invalid choice: 'bogus' (choose from status, start)
            Usage: devops docker {status|start} [options]
```

### End to End: Group Help
Command: `PYTHONPATH=src ../../../.venv/Scripts/python -c "...cli.run(['help', 'db'])" | sed -n 3,12p` (exit 0)

```text
Detailed Action Description: db
  Manage the local MySQL container, snapshots, and the Cloud SQL proxy. Sub-actions:
    status         check the MySQL container status
    start          start the isolated MySQL container
    stop           stop the MySQL container
    snapshot       extract and anonymize a database snapshot
    load-snapshot  load a SQL snapshot into a local or test database
    proxy          launch the Cloud SQL Auth Proxy for remote database access
  Without a sub-action, `db` runs `db status`.
  Put a positional snapshot path directly after load-snapshot, or use --snapshot-path.
```
