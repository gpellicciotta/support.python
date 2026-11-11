# T0084 validation proof

## Red phase

```text
python -m pytest tests/test_sql.py tests/test_devops.py tests/test_devops_service_actions.py -q -n0
FAILED tests/test_sql.py::TestSqlAnonymizer::test_custom_column_lists_and_syntax_variations
FAILED tests/test_sql.py::TestSqlAnonymizer::test_custom_password_flows_through_local_credentials_rule
FAILED tests/test_sql.py::TestSqlAnonymizer::test_custom_transformers_callback
FAILED tests/test_sql.py::TestSqlAnonymizer::test_full_sql_dump_anonymization_auth
SUBFAILED[auth-sample] tests/test_sql.py::TestSqlAnonymizer::test_golden_outputs_match_removed_schema_profiles
SUBFAILED[auth-inline] tests/test_sql.py::TestSqlAnonymizer::test_golden_outputs_match_removed_schema_profiles
SUBFAILED[counters-sample] tests/test_sql.py::TestSqlAnonymizer::test_golden_outputs_match_removed_schema_profiles
SUBFAILED[counters-inline] tests/test_sql.py::TestSqlAnonymizer::test_golden_outputs_match_removed_schema_profiles
FAILED tests/test_sql.py::TestSqlAnonymizer::test_realistic_auth_fixture_e2e
FAILED tests/test_sql.py::TestSqlAnonymizer::test_realistic_counters_fixture_e2e
SUBFAILED[app] tests/test_sql.py::TestSqlAnonymizer::test_removed_parameters_are_rejected
SUBFAILED[custom_password] tests/test_sql.py::TestSqlAnonymizer::test_removed_parameters_are_rejected
SUBFAILED[custom_transformers] tests/test_sql.py::TestSqlAnonymizer::test_removed_parameters_are_rejected
SUBFAILED[transform_auth_users] tests/test_sql.py::TestSqlAnonymizer::test_schema_transformers_are_removed
SUBFAILED[transform_auth_credentials] tests/test_sql.py::TestSqlAnonymizer::test_schema_transformers_are_removed
SUBFAILED[transform_auth_applications] tests/test_sql.py::TestSqlAnonymizer::test_schema_transformers_are_removed
SUBFAILED[transform_auth_tokens] tests/test_sql.py::TestSqlAnonymizer::test_schema_transformers_are_removed
SUBFAILED[transform_counters_users] tests/test_sql.py::TestSqlAnonymizer::test_schema_transformers_are_removed
SUBFAILED[transform_counters_webhooks] tests/test_sql.py::TestSqlAnonymizer::test_schema_transformers_are_removed
FAILED tests/test_sql.py::TestSqlAnonymizer::test_transformers_argument_is_required
FAILED tests/test_devops.py::LocalMySqlManagerTests::test_snapshot_and_anonymize_has_no_custom_password
FAILED tests/test_devops.py::LocalMySqlManagerTests::test_snapshot_applies_constructor_transformers
FAILED tests/test_devops.py::LocalMySqlManagerTests::test_snapshot_refuses_without_transformers
FAILED tests/test_devops_service_actions.py::DbGroupTests::test_snapshot_defaults
FAILED tests/test_devops_service_actions.py::DbGroupTests::test_snapshot_passes_every_option
25 failed, 116 passed, 13 subtests passed in 3.26s
```

## Green phase

```text
python scripts/devops.py check   (exit 0)
Command: C:\Dev-Projects\support.python\.plan\work\T0084-remove-the-auth-and-counters-schema-transformers-and\.venv\Scripts\python.exe -m ruff check .
Process ID: 72676
All checks passed!
Command: C:\Dev-Projects\support.python\.plan\work\T0084-remove-the-auth-and-counters-schema-transformers-and\.venv\Scripts\python.exe -m ruff format --check .
Process ID: 71556
165 files already formatted
Command: C:\Dev-Projects\support.python\.plan\work\T0084-remove-the-auth-and-counters-schema-transformers-and\.venv\Scripts\python.exe -m pytest -q
Process ID: 28484
bringing up nodes...
bringing up nodes...
....................u.u.............uu.uu....................uu.u..u..u. [  5%]
..u.u...u..u........uu.................................................. [ 11%]
...........................................s....u.u...uu.........u..u.uu [ 17%]
.u.....uuuu............uu...uu............................uuuuu......... [ 22%]
......................................uuu......u.uuuuuuu......uu....uu.u [ 27%]
..uuu.u.uuuu......uuu....uuuu.uu............................u.u.u....... [ 32%]
..............................uu.......u..u.u........u.u.u.............. [ 37%]
.....s.................................................................. [ 44%]
..............u...u.............uu..................................u.u. [ 50%]
......uu....uu.u...u..u..uu....................................u.u...u.. [ 55%]
u...........................s..................uu.u..................... [ 61%]
.......uu.u..uuuuuu.........................................uuuuu....... [ 67%]
....u..u.uu.uu...........................u..uu.u..................u.u... [ 72%]
...........................................................uu.u.u......u [ 78%]
.u..uuu.....................uu...u..................uu.................. [ 84%]
..............................................uuuu.....uuu.u............ [ 90%]
...................u....uuuuuuu.u.u.............u.uu.u.u.uuuuuu......... [ 94%]
uu...........................u.u..u...................u.u.........       [100%]
1106 passed, 3 skipped, 181 subtests passed in 10.97s
Command: C:\Dev-Projects\support.python\.plan\work\T0084-remove-the-auth-and-counters-schema-transformers-and\.venv\Scripts\python.exe -m pytest -m slow --timeout=120
Process ID: 64308
============================= test session starts =============================
platform win32 -- Python 3.12.8, pytest-9.2.0, pluggy-1.7.0
rootdir: C:\Dev-Projects\support.python\.plan\work\T0084-remove-the-auth-and-counters-schema-transformers-and
configfile: pyproject.toml
testpaths: tests
plugins: timeout-2.4.0, xdist-3.8.0
timeout: 120.0s
timeout method: thread
timeout func_only: False
created: 8/8 workers
8 workers [159 items]
........................................................................ [ 45%]
........................................................................ [ 90%]
...............                                                          [100%]
============================ 159 passed in 37.96s =============================
Removing dist
Command: C:\Dev-Projects\support.python\.plan\work\T0084-remove-the-auth-and-counters-schema-transformers-and\.venv\Scripts\python.exe -m build -o dist
Process ID: 74264
  - setuptools>=77
writing src\support_python.egg-info\PKG-INFO
writing dependency_links to src\support_python.egg-info\dependency_links.txt
writing entry points to src\support_python.egg-info\entry_points.txt
writing requirements to src\support_python.egg-info\requires.txt
writing top-level names to src\support_python.egg-info\top_level.txt
reading manifest file 'src\support_python.egg-info\SOURCES.txt'
writing manifest file 'src\support_python.egg-info\SOURCES.txt'
  - setuptools==84.2.1
writing src\support_python.egg-info\PKG-INFO
writing dependency_links to src\support_python.egg-info\dependency_links.txt
writing entry points to src\support_python.egg-info\entry_points.txt
writing requirements to src\support_python.egg-info\requires.txt
writing top-level names to src\support_python.egg-info\top_level.txt
reading manifest file 'src\support_python.egg-info\SOURCES.txt'
writing manifest file 'src\support_python.egg-info\SOURCES.txt'
Writing support_python-2.0.21rc0\setup.cfg
Creating tar archive
removing 'support_python-2.0.21rc0' (and everything under it)
  - setuptools>=77
writing src\support_python.egg-info\PKG-INFO
writing dependency_links to src\support_python.egg-info\dependency_links.txt
writing entry points to src\support_python.egg-info\entry_points.txt
writing requirements to src\support_python.egg-info\requires.txt
writing top-level names to src\support_python.egg-info\top_level.txt
reading manifest file 'src\support_python.egg-info\SOURCES.txt'
writing manifest file 'src\support_python.egg-info\SOURCES.txt'
  - setuptools==84.2.1
writing src\support_python.egg-info\PKG-INFO
writing dependency_links to src\support_python.egg-info\dependency_links.txt
writing entry points to src\support_python.egg-info\entry_points.txt
writing requirements to src\support_python.egg-info\requires.txt
writing top-level names to src\support_python.egg-info\top_level.txt
reading manifest file 'src\support_python.egg-info\SOURCES.txt'
writing manifest file 'src\support_python.egg-info\SOURCES.txt'
installing to build\bdist.win-amd64\wheel
Copying src\support_python.egg-info to build\bdist.win-amd64\wheel\.\support_python-2.0.21rc0-py3.12.egg-info
removing build\bdist.win-amd64\wheel
Successfully built support_python-2.0.21rc0.tar.gz and support_python-2.0.21rc0-py3-none-any.whl
```
