"""Unit and integration tests for lint-markdown rule plugins and the 'rules' action."""

from __future__ import annotations

import contextlib
import io
import json
from pathlib import Path
import shutil

import pytest

from support_python.markdown import MarkdownLinter, RuleRegistry, load_profile
from support_python.markdown.plugins import PluginError, load_plugins
from support_python.markdown.profiles import read_plugin_entries
from support_python.tools import lint_markdown
from tests.test_console_scripts import run_console_script

FIXTURES = Path(__file__).resolve().parent / "fixtures" / "markdown_plugins"
TODO_DOC = "# Notes\n\nThis paragraph has a TODO marker.\n"


def run_main(argv: list[str]) -> tuple[int, str, str]:
    """Run lint_markdown.main and capture its exit code, stdout, and stderr."""
    out, err = io.StringIO(), io.StringIO()
    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
        code = lint_markdown.main(argv)
    return code, out.getvalue(), err.getvalue()


def make_project(root: Path, config: dict | None = None) -> Path:
    """Create a project with a TODO document, the sample plugin under rules/, and an optional config."""
    (root / "rules").mkdir()
    shutil.copy(FIXTURES / "no_todo.py", root / "rules" / "no_todo.py")
    (root / "notes.md").write_text(TODO_DOC, encoding="utf-8")
    if config is not None:
        (root / ".lint-markdown.json").write_text(json.dumps(config), encoding="utf-8")
    return root


def write_plugin(root: Path, name: str, body: str) -> str:
    """Write a plugin module under root and return its file name."""
    (root / name).write_text(body, encoding="utf-8")
    return name


def lint_todo(registry: RuleRegistry) -> list[str]:
    """Lint the TODO document with every rule in registry and return the reported rule IDs."""
    linter = MarkdownLinter(offline=True, registry=registry)
    return [issue.rule_id for issue in linter.lint_content(Path("notes.md"), TODO_DOC.encode("utf-8"))]


def test_path_plugin_registers_rule_that_reports_issues() -> None:
    registry = RuleRegistry()
    sources = load_plugins(["no_todo.py"], registry, base_dir=FIXTURES)
    assert sources == {"X001": "no_todo.py"}
    assert "X001" in registry and "MD001" in registry
    assert lint_todo(registry) == ["X001"]


def test_module_plugin_registers_rule_that_reports_issues(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.syspath_prepend(str(FIXTURES))
    registry = RuleRegistry()
    assert load_plugins(["no_todo"], registry) == {"X001": "no_todo"}
    assert lint_todo(registry) == ["X001"]


def test_same_plugin_entry_listed_twice_loads_once() -> None:
    registry = RuleRegistry()
    entry = str(FIXTURES / "no_todo.py")
    assert load_plugins([entry, entry], registry) == {"X001": entry}


@pytest.mark.parametrize(
    ("name", "body", "message"),
    [
        ("broken.py", "def register(registry:\n", "failed to import"),
        ("no_register.py", "VALUE = 1\n", "does not define a callable 'register'"),
        ("raises.py", "def register(registry):\n    raise RuntimeError('boom')\n", "boom"),
        (
            "dup.py",
            "from support_python.markdown.rules import MD001HeadingIncrement\n"
            "def register(registry):\n    registry.register(MD001HeadingIncrement())\n",
            "rule ID 'MD001' is already registered",
        ),
    ],
)
def test_broken_plugin_raises_plugin_error_naming_the_entry(tmp_path: Path, name: str, body: str, message: str) -> None:
    write_plugin(tmp_path, name, body)
    with pytest.raises(PluginError) as excinfo:
        load_plugins([name], RuleRegistry(), base_dir=tmp_path)
    assert name in str(excinfo.value)
    assert message in str(excinfo.value)


def test_missing_plugin_file_and_module_raise_plugin_error(tmp_path: Path) -> None:
    with pytest.raises(PluginError, match=r"missing\.py.*not found"):
        load_plugins(["missing.py"], RuleRegistry(), base_dir=tmp_path)
    with pytest.raises(PluginError, match=r"no_such_plugin_module.*failed to import"):
        load_plugins(["no_such_plugin_module"], RuleRegistry())


def test_plugins_colliding_with_each_other_raise_plugin_error(tmp_path: Path) -> None:
    shutil.copy(FIXTURES / "no_todo.py", tmp_path / "copy_one.py")
    shutil.copy(FIXTURES / "no_todo.py", tmp_path / "copy_two.py")
    with pytest.raises(PluginError, match=r"copy_two\.py.*rule ID 'X001' is already registered"):
        load_plugins(["copy_one.py", "copy_two.py"], RuleRegistry(), base_dir=tmp_path)


def test_failed_plugin_leaves_registry_unchanged(tmp_path: Path) -> None:
    write_plugin(
        tmp_path,
        "partial.py",
        "from support_python.markdown.rules import MD001HeadingIncrement\n"
        "def register(registry):\n"
        "    from support_python.markdown import Rule\n"
        "    class Extra(Rule):\n        rule_id, name = 'X900', 'extra'\n"
        "    registry.register(Extra())\n"
        "    registry.register(MD001HeadingIncrement())\n",
    )
    registry = RuleRegistry()
    before = registry.rule_ids()
    with pytest.raises(PluginError):
        load_plugins(["partial.py"], registry, base_dir=tmp_path)
    assert registry.rule_ids() == before


def test_read_plugin_entries_validates_the_plugins_key(tmp_path: Path) -> None:
    config = tmp_path / ".lint-markdown.json"
    config.write_text(json.dumps({"plugins": ["rules/no_todo.py", "pkg.rules"]}), encoding="utf-8")
    assert read_plugin_entries(config) == ["rules/no_todo.py", "pkg.rules"]
    assert read_plugin_entries(None) == []
    assert read_plugin_entries(tmp_path / "absent.json") == []
    config.write_text(json.dumps({"plugins": "rules/no_todo.py"}), encoding="utf-8")
    with pytest.raises(ValueError, match="'plugins' must be a list"):
        read_plugin_entries(config)


def test_profile_accepts_plugins_key_and_toggles_plugin_rules(tmp_path: Path) -> None:
    registry = RuleRegistry()
    load_plugins(["no_todo.py"], registry, base_dir=FIXTURES)
    config = tmp_path / ".lint-markdown.json"
    config.write_text(json.dumps({"plugins": ["no_todo.py"]}), encoding="utf-8")
    assert "X001" in load_profile(config, registry=registry).enabled_rules
    assert "X001" in load_profile(None, profile="dev-guidelines", registry=registry).enabled_rules
    config.write_text(json.dumps({"plugins": ["no_todo.py"], "disable": ["X001"]}), encoding="utf-8")
    assert "X001" not in load_profile(config, registry=registry).enabled_rules
    config.write_text(json.dumps({"plugins": ["no_todo.py"], "rules": {"no-todo": False}}), encoding="utf-8")
    assert "X001" not in load_profile(config, registry=registry).enabled_rules


def test_check_loads_plugins_from_config(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.chdir(make_project(tmp_path, {"plugins": ["rules/no_todo.py"]}))
    code, out, _ = run_main(["check", "--offline", "notes.md"])
    assert code == 1
    assert "X001" in out and "no-todo" in out


def test_check_loads_plugins_from_option(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.chdir(make_project(tmp_path))
    code, out, _ = run_main(["check", "--offline", "--plugin", "rules/no_todo.py", "notes.md"])
    assert code == 1
    assert "X001" in out
    assert run_main(["check", "--offline", "notes.md"])[0] == 0


def test_check_resolves_config_plugins_relative_to_config_dir(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    make_project(tmp_path, {"plugins": ["rules/no_todo.py"]})
    (tmp_path / "docs").mkdir()
    monkeypatch.chdir(tmp_path / "docs")
    code, out, _ = run_main(["check", "--offline", "--config", "../.lint-markdown.json", "../notes.md"])
    assert code == 1
    assert "X001" in out


def test_check_reads_plugins_from_config_directory(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    make_project(tmp_path, {"plugins": ["rules/no_todo.py"]})
    (tmp_path / "docs").mkdir()
    monkeypatch.chdir(tmp_path / "docs")
    code, out, err = run_main(["check", "--offline", "--config", "..", "../notes.md"])
    assert code == 1, err
    assert "X001" in out


def test_check_loads_plugin_listed_in_config_and_option_once(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.chdir(make_project(tmp_path, {"plugins": ["rules/no_todo.py"]}))
    code, out, err = run_main(["check", "--offline", "--plugin", "rules/no_todo.py", "notes.md"])
    assert code == 1, err
    assert out.count("X001") == 1


def test_rules_action_reports_plugin_source_for_lowercase_rule_id(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.chdir(make_project(tmp_path))
    write_plugin(
        tmp_path,
        "lower.py",
        "from support_python.markdown import Rule\n"
        "class Lower(Rule):\n    rule_id, name = 'x002', 'lower-id'\n"
        "def register(registry):\n    registry.register(Lower())\n",
    )
    code, out, _ = run_main(["rules", "--format", "json", "--plugin", "lower.py"])
    assert code == 0
    by_name = {rule["name"]: rule for rule in json.loads(out)["rules"]}
    assert by_name["lower-id"]["source"] == "lower.py"
    assert by_name["lower-id"]["enabled"] is True


def test_profile_disable_turns_plugin_rule_off_in_check(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.chdir(make_project(tmp_path, {"plugins": ["rules/no_todo.py"], "disable": ["X001"]}))
    code, out, _ = run_main(["check", "--offline", "notes.md"])
    assert code == 0, out


@pytest.mark.parametrize(
    ("name", "body"),
    [
        ("broken.py", "def register(registry:\n"),
        ("no_register.py", "VALUE = 1\n"),
        (
            "dup.py",
            "from support_python.markdown.rules import MD001HeadingIncrement\n"
            "def register(registry):\n    registry.register(MD001HeadingIncrement())\n",
        ),
    ],
)
def test_check_and_rules_exit_2_naming_broken_plugin(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, name: str, body: str) -> None:
    monkeypatch.chdir(make_project(tmp_path))
    write_plugin(tmp_path, name, body)
    for argv in (["check", "--offline", "--plugin", name, "notes.md"], ["rules", "--plugin", name]):
        code, _, err = run_main(argv)
        assert code == 2, argv
        assert name in err, argv


def test_invalid_plugins_key_exits_2(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.chdir(make_project(tmp_path, {"plugins": [""]}))
    code, _, err = run_main(["check", "--offline", "notes.md"])
    assert code == 2
    assert "'plugins'" in err


def test_rules_action_lists_builtin_and_plugin_rules_as_text(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.chdir(make_project(tmp_path, {"plugins": ["rules/no_todo.py"]}))
    code, out, _ = run_main(["rules"])
    assert code == 0
    lines = out.splitlines()
    header = next(line for line in lines if line.startswith("id "))
    for column in ("name", "scope", "fixable", "enabled", "source"):
        assert column in header
    md001 = next(line for line in lines if line.startswith("MD001 "))
    assert "heading-increment" in md001 and "builtin" in md001
    x001 = next(line for line in lines if line.startswith("X001 "))
    assert x001.split()[1:] == ["no-todo", "prose", "no", "yes", "rules/no_todo.py"]
    md015 = next(line for line in lines if line.startswith("MD015 "))
    assert md015.split()[4] == "yes"


def test_rules_action_emits_json(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.chdir(make_project(tmp_path))
    code, out, _ = run_main(["rules", "--format", "json", "--plugin", "rules/no_todo.py", "--profile", "dev-guidelines"])
    assert code == 0
    rules = json.loads(out)["rules"]
    by_id = {rule["id"]: rule for rule in rules}
    assert len(rules) == 20
    assert by_id["X001"] == {
        "id": "X001",
        "name": "no-todo",
        "scope": "prose",
        "fixable": False,
        "enabled": True,
        "source": "rules/no_todo.py",
    }
    assert by_id["MD005"]["fixable"] is True
    assert by_id["MD015"]["enabled"] is True
    assert {rule["source"] for rule in rules if rule["id"] != "X001"} == {"builtin"}


def test_rules_action_reports_disabled_plugin_rule(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.chdir(make_project(tmp_path, {"plugins": ["rules/no_todo.py"], "disable": ["X001"]}))
    code, out, _ = run_main(["rules", "--format", "json"])
    assert code == 0
    by_id = {rule["id"]: rule for rule in json.loads(out)["rules"]}
    assert by_id["X001"]["enabled"] is False


def test_installed_console_script_loads_plugin_from_config(tmp_path: Path) -> None:
    make_project(tmp_path, {"plugins": ["rules/no_todo.py"]})
    check = run_console_script("lint-markdown", "check", "--offline", cwd=tmp_path)
    assert check.returncode == 1, check.stdout + check.stderr
    assert "X001" in check.stdout
    rules = run_console_script("lint-markdown", "rules", "--format", "json", cwd=tmp_path)
    assert rules.returncode == 0, rules.stderr
    assert "X001" in {rule["id"] for rule in json.loads(rules.stdout)["rules"]}
