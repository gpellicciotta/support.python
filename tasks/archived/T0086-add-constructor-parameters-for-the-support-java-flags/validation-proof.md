# Validation Proof

## Red phase
`python -m pytest tests/test_devops_services.py -q` exited 1 before the implementation.

```
TypeError: LocalVerifier.__init__() got an unexpected keyword argument 'health_endpoint'
TypeError: LocalVerifier.__init__() got an unexpected keyword argument 'default_assets'
TypeError: LocalServerManager.__init__() got an unexpected keyword argument 'environment_file_option'
TypeError: LocalMySqlManager.__init__() got an unexpected keyword argument 'test_env_file_name'
AttributeError: 'LocalMySqlManager' object has no attribute 'render_env_file_name'
FAILED tests/test_devops_services.py::VerifierOptionTests::test_default_health_endpoint_and_assets
FAILED tests/test_devops_services.py::VerifierOptionTests::test_verify_health_status_defaults_to_the_configured_endpoint
FAILED tests/test_devops_services.py::VerifierOptionTests::test_default_assets_are_the_asset_check_default
FAILED tests/test_devops_services.py::ServerManagerOptionTests::test_none_options_and_empty_args_drop_their_arguments
FAILED tests/test_devops_services.py::MailManagerOptionTests::test_overrides_and_server_manager_options_apply
FAILED tests/test_devops_services.py::ServerManagerOptionTests::test_every_override_replaces_its_argument
FAILED tests/test_devops_services.py::MySqlEnvFileNameTests::test_custom_names_accept_both_placeholder_spellings
FAILED tests/test_devops_services.py::MySqlEnvFileNameTests::test_default_names
FAILED tests/test_devops_services.py::CustomHealthEndpointIntegrationTests::test_verify_deployment_against_a_custom_health_path
9 failed, 2 passed in 2.97s
```

The 2 passing tests assert the default commands, which already matched.

## Green phase
`python scripts/devops.py check` exited 0.

```
All checks passed!
1122 passed, 5 skipped, 181 subtests passed in 11.04s
============================ 159 passed in 36.58s =============================
```
