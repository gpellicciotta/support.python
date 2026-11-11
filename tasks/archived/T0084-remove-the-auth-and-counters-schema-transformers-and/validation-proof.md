# T0084 validation proof

## Red phase
```text
python -m pytest tests/test_sql.py tests/test_devops.py tests/test_devops_service_actions.py -q -n0
FAILED tests/test_sql.py::TestSqlAnonymizer::test_transformers_argument_is_required
FAILED tests/test_sql.py::TestSqlAnonymizer::test_realistic_auth_fixture_e2e
FAILED tests/test_sql.py::TestSqlAnonymizer::test_realistic_counters_fixture_e2e
SUBFAILED[app] tests/test_sql.py::TestSqlAnonymizer::test_removed_parameters_are_rejected
SUBFAILED[custom_password] tests/test_sql.py::TestSqlAnonymizer::test_removed_parameters_are_rejected
SUBFAILED[transform_auth_users] tests/test_sql.py::TestSqlAnonymizer::test_schema_transformers_are_removed
SUBFAILED[transform_counters_webhooks] tests/test_sql.py::TestSqlAnonymizer::test_schema_transformers_are_removed
FAILED tests/test_devops.py::LocalMySqlManagerTests::test_snapshot_refuses_without_transformers
FAILED tests/test_devops.py::LocalMySqlManagerTests::test_snapshot_applies_constructor_transformers
FAILED tests/test_devops_service_actions.py::DbGroupTests::test_snapshot_defaults
25 failed, 116 passed, 13 subtests passed in 3.26s
```
The list above is an excerpt of the 25 failures.

## Green phase
```text
python scripts/devops.py check   (exit 0)
All checks passed!
165 files already formatted
1106 passed, 3 skipped, 181 subtests passed in 10.97s
============================ 159 passed in 37.96s =============================
Successfully built support_python-2.0.21rc0.tar.gz and support_python-2.0.21rc0-py3-none-any.whl
```
The fast suite, slow suite, lint, format check, and build all succeeded.
