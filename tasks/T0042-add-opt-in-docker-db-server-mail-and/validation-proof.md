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

## Review Round 1 Rework

### Red Phase
Command: `../../../.venv/Scripts/python -m pytest -q tests/test_devops_service_actions.py 2>&1 | grep -E "^FAILED|passed|failed"` (exit 1)

```text
[... 6 lines omitted ...]
E       AssertionError: 'Target safety validation failed' not found in "Starting devops v1.2.0-pre+<Mock name='run().stdout.strip()' id='2410638535968'> with configuration:\n- Command: db\n- Log file: none\n- Log level: INFO\n- Verbose: false\n**[ERROR]** Invalid target 'todos_test'. Allowed targets are 'local' and 'testdb'.\n**[ERROR]** Finished devops db in 0.0s with status: failed\n"
E       **[ERROR]** Finished devops db in 0.0s with status: failed
FAILED tests/test_devops_service_actions.py::DbGroupTests::test_a_snapshot_path_on_another_sub_action_exits_2
FAILED tests/test_devops_service_actions.py::DbGroupTests::test_test_database_aliases_are_valid_targets
FAILED tests/test_devops_service_actions.py::ServerGroupTests::test_start_testdb_exits_1_when_the_env_file_is_missing
FAILED tests/test_devops_service_actions.py::ServerGroupTests::test_start_testdb_uses_the_test_database_env_file_without_mysql
FAILED tests/test_devops_service_actions.py::ClientGroupTests::test_verify_deployment_defaults
FAILED tests/test_devops_service_actions.py::ClientGroupTests::test_verify_deployment_options
FAILED tests/test_devops_service_actions.py::LocalVerifierDeploymentTimeoutTests::test_verify_deployment_passes_the_timeout_to_each_request
FAILED tests/test_devops_service_actions.py::RealMySqlLoadSnapshotTests::test_alias_target_names_the_test_database
FAILED tests/test_devops_service_actions.py::RealMySqlLoadSnapshotTests::test_safety_check_still_rejects_a_mismatched_database
FAILED tests/test_devops_service_actions.py::RealMySqlLoadSnapshotTests::test_todos_test_target_loads_into_todos_test
14 failed, 48 passed, 9 subtests passed in 2.43s
```

### Green Phase
Command: `../../../.venv/Scripts/python -m pytest -q tests/test_devops_service_actions.py tests/test_devops.py 2>&1 | grep -E "^FAILED|passed|failed"` (exit 0)

```text
106 passed, 13 subtests passed in 2.49s
```

### Full Suite and Lint
Command: `../../../.venv/Scripts/python -m ruff check . && ../../../.venv/Scripts/python -m ruff format --check . && ../../../.venv/Scripts/python -m pytest -q 2>&1 | tail -3` (exit 0)

```text
All checks passed!
143 files already formatted
................................................................ [ 99%]
..                                                                       [100%]
1033 passed, 3 skipped, 118 subtests passed in 146.53s (0:02:26)
```

### End to End: Reviewer Reproductions With a Real LocalMySqlManager
Command: `PYTHONPATH=src ... cli.run(['db', 'load-snapshot', 's.sql', '--target', 'todos_test'])` with `db_name='todos'` and no proxy running (exit 1)

```text
Starting devops v2.0.26-pre+bae339a with configuration:
**[ERROR]** Cloud SQL Auth Proxy is not running on port 3606. Please launch Cloud SQL Auth Proxy first.
**[ERROR]** Finished devops db in 1.0s with status: failed
```

Command: `PYTHONPATH=src ... add_services(mysql=LocalMySqlManager(), db_targets=('local', 'staging'))` (exit 1)

```text
ValueError: Unsupported db_targets ['staging']: use 'local', 'testdb', or '<name>_test'.
```

Command: `PYTHONPATH=src ... cli.run(['db', 'snapshot', 'stray.sql'])` (exit 2)

```text
**[ERROR]** Unexpected argument 'stray.sql' for `db snapshot`.
**[ERROR]** Finished devops db in 0.0s with status: failed
```
