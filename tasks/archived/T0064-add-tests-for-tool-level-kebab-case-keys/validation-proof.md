## Walkthrough & Validation
Added [test_config_keys.py](../../../../tests/tools/test_config_keys.py): tool-level kebab keys, documented example configs for three tools, and an `agent-files check --config` kebab versus snake run.

The tests cover behavior implemented in T0057 and T0063, so they passed on first run; no failing-first proof applies.

Command: `pytest tests/tools/test_config_keys.py -q`, `ruff check src tests`

```text
......                                                                   [100%]
6 passed in 0.29s
All checks passed!
```
