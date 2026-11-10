### Declared Files
- src/support_python/devops/services.py
- tests/test_devops_services.py
- docs/tutorials/devops-scripts.md
- CHANGELOG.md

### Parameters
All parameters are keyword arguments whose defaults reproduce today's behavior.

`LocalServerManager`:
- `environment_file_option: Optional[str] = "-Denvironment-properties-file"`, rendered as `{option}={env_file}`.
- `config_file_option: Optional[str] = "--config-file"`, rendered as `{option}={config_file}`.
- `log_file_option: Optional[str] = "--logging.file-path"`, rendered as `{option}={log_file}`.
- `mail_backend_args: Sequence[str] = ("--mail.back-end-type=com.pellicciotta.support.mail.DummyBackEnd",)`.
- `memory_db_args: Sequence[str] = ("--db.jdbc-url=memory",)`.
- `start_args: Sequence[str] = ("start",)`.
- `static_dir_env_var: Optional[str] = None`; `None` keeps today's `{APP_NAME}_STATIC_DIR` name.
- An option set to `None` omits its argument.

`LocalMailManager`:
- `test_mail_args: Sequence[str] = ("test-mail-formats",)`; the command appends the recipient and app name after them.
- It reuses the server manager's `environment_file_option` and `config_file_option`.

`LocalVerifier`:
- `health_endpoint: str = "/api/status"`: the default of `verify_health_status` and the path `verify_deployment` polls.
- `running_status: str = "running"`: the status `verify_deployment` accepts.
- `default_assets: Sequence[str] = ("/css/main.css", "/js/main.mjs")`.
- `verify_health_status(endpoint: Optional[str] = None)` uses `health_endpoint` when `endpoint` is `None`.

`LocalMySqlManager`:
- `prod_env_file_name: str = "{{app}}-proddb-cloudrun.env"`.
- `test_env_file_name: str = "{{db-name}}-testdb-devserver.env"`.
- Render these mustache placeholders, accepting `{{db_name}}` as well as `{{db-name}}`.

### Tests
- Unit: with defaults, the `LocalServerManager.start` command captured by patching `subprocess.Popen` equals today's exactly.
- Unit: each override replaces its argument, `None` options drop theirs, and `mail_backend_args=()` drops the mail flag.
- Unit: `LocalMailManager` builds `[..., *test_mail_args, recipient, app]`; env-file names render both placeholder spellings.
- Integration: Serve `{"status": "ok", "version": "1.2.3"}` on a custom health path with `EmbeddedStaticServer`.
  - `LocalVerifier(health_endpoint=..., running_status="ok").verify_deployment(url, "1.2.3")` must pass.
  - A default `LocalVerifier` must fail against the same server.

Completion check: `.venv/Scripts/python -m pytest tests/test_devops_services.py` plus `python scripts/devops.py check`.
Size estimate: 4 files, 320 lines

### Notes
- The user asked to keep the existing values as defaults; the change is backward compatible and needs no migration entry.
- Needs T0084, because both tasks edit `snapshot_and_anonymize`.
