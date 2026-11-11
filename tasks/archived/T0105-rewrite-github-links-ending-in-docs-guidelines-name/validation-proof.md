## Walkthrough & Validation

### Failing test before the change
```text
FAILED tests/tools/test_agent_digest.py::TestLinkBaseAndSkillLinks::test_github_docs_guidelines_urls_rewrite_to_skill_reference
AssertionError: 'Follow the `plan-task-usage-guidelines` skill.' not found in '## Core\n- Follow [Plan Task Usage](https://github.com/gpellicciotta/plan/blob/main/docs/guidelines/plan-task-usage-guidelines.md). ...'
1 failed in 3.13s
```

### Tests after the change
```text
$ python -m pytest tests/tools/test_agent_digest.py -q
54 passed, 23 subtests passed in 5.05s
$ python -m ruff check src tests
All checks passed!
```

### Integration scenario
Ran `agent-digest generate` then `check` on a guideline linking a `/docs/guidelines/plan-task-usage-guidelines.md` GitHub URL.
```text
Generated out.md (2 lines, 57 bytes).
## Core
- Follow the `plan-task-usage-guidelines` skill.
out.md is up to date and within budget (57 bytes).
```
