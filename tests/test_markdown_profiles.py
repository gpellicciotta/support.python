"""Unit and integration tests for Markdown rule classes, registry, and profiles."""

from __future__ import annotations

import contextlib
import io
import json
from pathlib import Path
from unittest.mock import patch

import pytest

import support_python
from support_python.markdown import (
    ALL_RULE_CLASSES,
    DEFAULT_PROFILE,
    DEFAULT_REGISTRY,
    DEV_GUIDELINES_PROFILE,
    LintIssue,
    LintProfile,
    MarkdownLinter,
    Rule,
    RuleRegistry,
    TableAlignmentIssue,
    check_table_alignment,
    format_markdown_table,
    load_profile,
)
from support_python.markdown.lint import LintIssue as EngineLintIssue, MarkdownLinter as EngineMarkdownLinter
from support_python.markdown.profiles import PROFILES
from support_python.markdown.registry import LintContext
from support_python.tools import lint_markdown


def test_markdown_package_preserves_table_exports() -> None:
    """Ensure the support_python.markdown package and root re-export table and lint helpers."""
    table = format_markdown_table(["A", "B"], [["1", "2"]])
    assert "| A   | B   |" in table
    assert check_table_alignment(table) == []
    issue = TableAlignmentIssue(line_number=1, column_number=1, message="test")
    assert issue.line_number == 1
    assert MarkdownLinter is EngineMarkdownLinter
    assert LintIssue is EngineLintIssue
    assert support_python.MarkdownLinter is EngineMarkdownLinter
    assert support_python.LintIssue is EngineLintIssue


def test_rule_registry_contains_all_rules_and_validates_selection() -> None:
    """Verify RuleRegistry registration, lookup, ordering, and unknown rule rejection."""
    expected_ids = [f"MD{i:03d}" for i in range(1, 20)]
    assert len(ALL_RULE_CLASSES) == 19
    assert DEFAULT_REGISTRY.rule_ids() == expected_ids
    assert DEFAULT_REGISTRY.as_rules_dict() == MarkdownLinter.RULES

    rule1 = DEFAULT_REGISTRY.get("MD001")
    assert isinstance(rule1, Rule)
    assert rule1 is DEFAULT_REGISTRY.get("md001")
    assert rule1 is DEFAULT_REGISTRY.get("heading-increment")
    assert "MD015" in DEFAULT_REGISTRY
    assert "MD999" not in DEFAULT_REGISTRY

    selected = DEFAULT_REGISTRY.select(["md001", "MD017"])
    assert [r.rule_id for r in selected] == ["MD001", "MD017"]

    with pytest.raises(ValueError, match="Unknown rule ID"):
        DEFAULT_REGISTRY.select(["MD001", "MD999"])

    custom_reg = RuleRegistry()
    assert len(custom_reg) == 19
    ctx = LintContext(file_path=Path("a.md"), actual_file_path=Path("a.md"), project_root=Path("."), raw_bytes=b"", lines=[])
    assert Rule().check(ctx) == []


def test_each_rule_class_triggers_and_passes_with_stable_messages(tmp_path: Path) -> None:
    """Verify every MD001-MD019 rule class triggers and passes with unchanged IDs and messages."""
    (tmp_path / ".git").mkdir()
    (tmp_path / "existing.md").write_text("# Target\n\n## Sub\n", encoding="utf-8")
    (tmp_path / "scripts").mkdir()
    (tmp_path / "scripts" / "tool.py").write_text("# tool\n", encoding="utf-8")
    doc = tmp_path / "doc.md"
    clog = tmp_path / "CHANGELOG.md"

    cases: list[tuple[str, Path, bytes, bytes, str]] = [
        ("MD001", doc, b"# H1\n\n### H3\n", b"# H1\n\n## H2\n", "Heading level skipped from H1 to H3"),
        ("MD002", doc, b"# H1\n\n# Second H1\n", b"# H1\n\n## H2\n", "Multiple H1 headings found (H1 #2)"),
        ("MD003", doc, b"# H1\n\n## 1.2 Intro\n", b"# H1\n\n## Intro\n", "Numbered heading prefix found: '1.2 Intro'"),
        ("MD004", doc, b"# H1\n\n**Fake Heading**\n", b"# H1\n\nNormal **bold**.\n", "Bold text on own line used as heading"),
        ("MD005", doc, b"# H1\n\n* Item\n", b"# H1\n\n- Item\n", "Non-dash bullet indicator '*' used; use '-' instead"),
        ("MD006", doc, b"# H1\n\n- **All bold**\n", b"# H1\n\n- **Term:** Def\n", "Entire bullet item is bolded"),
        ("MD007", doc, b"# H1\n\n```\ncode\n```\n", b"# H1\n\n```py\ncode\n```\n", "Fenced code block lacks a language"),
        ("MD008", doc, b"# H1\n\nSee https://example.com now.\n", b"# H1\n\n[x](https://example.com)\n", "Raw URL found in prose"),
        ("MD009", doc, b"# H1\n\n[x](file:///tmp/a.md)\n", b"# H1\n\n[x](existing.md)\n", "Local file:/// URI used"),
        ("MD010", doc, b"# H1\n\n\tIndented\n", b"# H1\n\n    Indented\n", "Line contains hard tab character"),
        (
            "MD011",
            doc,
            b"# H1\n\nTrailing   \n",
            b"# H1\n\nClean  \n",
            "Line has trailing whitespace; at most two trailing spaces are allowed",
        ),
        ("MD012", doc, b"# H1\r\n\nLine\n", b"# H1\n\nLine\n", "File contains mixed line endings"),
        ("MD013", clog, b"# Log\n\n- Fixed T0012 bug\n", b"# Log\n\n- Fixed bug\n", "Task identifier 'T0012' found"),
        ("MD014", doc, b"# H1\n\n[x](missing.md)\n", b"# H1\n\n[x](existing.md#sub)\n", "Relative link 'missing.md'"),
        ("MD015", doc, b"# H1\n\n## Sub\n\nBody\n", b"# H1\n\n## Sub\nBody\n", "Heading 'Sub' (H2) must not be followed"),
        ("MD016", doc, b"# H1\n\nIntro:\n\n- Item\n", b"# H1\n\nIntro:\n- Item\n", "Sentence introducing a list"),
        (
            "MD017",
            doc,
            b"# H1\n\n| Col A | B |\n|:-|---|\n| 1 | 2 |\n",
            b"# H1\n\n| A   | B   |\n| :-- | :-- |\n",
            "not vertically",
        ),
        (
            "MD019",
            doc,
            b"# H1\n\nUse `scripts/tool.py`.\n",
            b"# H1\n\nUse [tool.py](scripts/tool.py).\n",
            "Repository file reference",
        ),
    ]

    for rule_id, path, bad_bytes, good_bytes, expected_msg in cases:
        rule = DEFAULT_REGISTRY.get(rule_id)
        assert rule is not None
        bad_issues = rule.lint(bad_bytes, file_path=path, project_root=tmp_path)
        assert len(bad_issues) >= 1, f"{rule_id} did not trigger"
        assert bad_issues[0].rule_id == rule_id
        assert bad_issues[0].rule_name == rule.name
        assert expected_msg in bad_issues[0].message

        good_issues = rule.lint(good_bytes, file_path=path, project_root=tmp_path)
        assert good_issues == [], f"{rule_id} triggered unexpectedly: {good_issues}"

    # MD018 (external link validation with mocked urlopen)
    rule18 = DEFAULT_REGISTRY.get("MD018")
    assert rule18 is not None
    import urllib.error

    with patch("urllib.request.urlopen") as mock_open:
        mock_open.side_effect = urllib.error.HTTPError("https://bad.org/x", 404, "Not Found", {}, None)
        issues18 = rule18.lint(b"# H1\n\n[Bad](https://bad.org/x)\n", file_path=doc, project_root=tmp_path)
        assert len(issues18) == 1
        assert issues18[0].rule_id == "MD018"
        assert "External link 'https://bad.org/x' failed validation: HTTP 404" in issues18[0].message

        mock_open.side_effect = None
        mock_open.return_value.__enter__.return_value.status = 200
        ok18 = rule18.lint(b"# H1\n\n[Good](https://good.org/x)\n", file_path=doc, project_root=tmp_path)
        assert ok18 == []


def test_profile_loading_default_dev_guidelines_missing_file_and_unknown_rule(tmp_path: Path) -> None:
    """Verify load_profile handles default, dev-guidelines, missing files, and unknown rule IDs."""
    assert "default" in PROFILES
    assert "dev-guidelines" in PROFILES
    assert "MD015" not in DEFAULT_PROFILE.enabled_rules
    assert not DEFAULT_PROFILE.historical_task_exemptions
    assert "MD015" in DEV_GUIDELINES_PROFILE.enabled_rules
    assert DEV_GUIDELINES_PROFILE.historical_task_exemptions

    # Missing file falls back to DEFAULT_PROFILE
    missing_profile = load_profile(tmp_path / ".markdown-lint.json")
    assert missing_profile == DEFAULT_PROFILE
    assert load_profile(tmp_path) == DEFAULT_PROFILE

    # Explicit dev-guidelines profile in .markdown-lint.json
    cfg_file = tmp_path / ".markdown-lint.json"
    cfg_file.write_text(json.dumps({"profile": "dev-guidelines"}), encoding="utf-8")
    loaded_dg = load_profile(cfg_file)
    assert loaded_dg == DEV_GUIDELINES_PROFILE

    # Default profile with custom rule adjustments
    cfg_file.write_text(json.dumps({"profile": "default", "enable": ["MD015"], "disable": ["MD018"]}), encoding="utf-8")
    custom = load_profile(cfg_file)
    assert isinstance(custom, LintProfile)
    assert "MD015" in custom.enabled_rules
    assert "MD018" not in custom.enabled_rules
    assert not custom.historical_task_exemptions

    # Config without a profile key uses default profile as base (MD015 stays off)
    cfg_file.write_text(json.dumps({"disable": ["MD018"]}), encoding="utf-8")
    no_prof_key = load_profile(cfg_file)
    assert no_prof_key.name == "default"
    assert "MD015" not in no_prof_key.enabled_rules
    assert "MD018" not in no_prof_key.enabled_rules
    assert not no_prof_key.historical_task_exemptions

    # Unknown rule ID raises ValueError
    cfg_file.write_text(json.dumps({"rules": ["MD001", "MD999"]}), encoding="utf-8")
    with pytest.raises(ValueError, match="MD999"):
        load_profile(cfg_file)

    # Unknown profile name raises ValueError
    cfg_file.write_text(json.dumps({"profile": "nonexistent"}), encoding="utf-8")
    with pytest.raises(ValueError, match="nonexistent"):
        load_profile(cfg_file)


def test_default_vs_dev_guidelines_profile_behavior_and_t0014_parity(tmp_path: Path) -> None:
    """Verify default vs dev-guidelines profile behavior and exact parity with T0014 output."""
    (tmp_path / ".git").mkdir()
    task_dir = tmp_path / ".plan" / "tasks"
    task_dir.mkdir(parents=True)
    hist_task = task_dir / "T0050-old-task.md"
    hist_task.write_bytes(
        b"---\nid: T0050\nstatus: completed\n---\n# T0050: Old\n\n## Goals\n\nSee [missing](missing.md) and `src/foo.py`.\n"
    )
    doc = tmp_path / "guide.md"
    doc.write_bytes(b"# Guide\n\n## Section\n\nParagraph after blank line.\n")

    default_linter = MarkdownLinter(profile="default", offline=True, project_root=tmp_path)
    dg_linter = MarkdownLinter(profile="dev-guidelines", offline=True, project_root=tmp_path)
    legacy_linter = MarkdownLinter(offline=True, project_root=tmp_path)

    # On guide.md: default ignores MD015, dev-guidelines flags MD015
    assert default_linter.lint_content(doc, doc.read_bytes()) == []
    dg_doc_issues = dg_linter.lint_content(doc, doc.read_bytes())
    assert [i.rule_id for i in dg_doc_issues] == ["MD015"]

    # On historical task: default flags MD014, dev-guidelines exempts historical task
    default_task_issues = default_linter.lint_content(hist_task, hist_task.read_bytes())
    assert [i.rule_id for i in default_task_issues] == ["MD014"]
    assert dg_linter.lint_content(hist_task, hist_task.read_bytes()) == []

    # Parity between dev-guidelines profile and T0014 default MarkdownLinter
    for target in (doc, hist_task):
        raw = target.read_bytes()
        assert dg_linter.lint_content(target, raw) == legacy_linter.lint_content(target, raw)

    # CLI with no config and no --profile uses default profile (does not report MD015 on guide.md)
    out_none, err_none = io.StringIO(), io.StringIO()
    with contextlib.redirect_stdout(out_none), contextlib.redirect_stderr(err_none):
        code_none = lint_markdown.main(["check", "--offline", str(doc)])
    assert code_none == 0
    assert "MD015" not in out_none.getvalue()

    # CLI with --profile default agrees with no-config behavior
    out_def, err_def = io.StringIO(), io.StringIO()
    with contextlib.redirect_stdout(out_def), contextlib.redirect_stderr(err_def):
        code_def = lint_markdown.main(["check", "--profile", "default", "--offline", str(doc)])
    assert code_def == 0
    assert "MD015" not in out_def.getvalue()

    # CLI with .markdown-lint.json lacking a profile key also uses default profile (MD015 stays off)
    cfg_path = tmp_path / ".markdown-lint.json"
    cfg_path.write_text(json.dumps({"disable": ["MD018"]}), encoding="utf-8")
    out_cfg_def, err_cfg_def = io.StringIO(), io.StringIO()
    with contextlib.redirect_stdout(out_cfg_def), contextlib.redirect_stderr(err_cfg_def):
        code_cfg_def = lint_markdown.main(["check", "--offline", str(doc)])
    assert code_cfg_def == 0
    assert "MD015" not in out_cfg_def.getvalue()

    # End-to-end CLI parity with legacy .markdown-lint.json set to dev-guidelines
    cfg_path.write_text(json.dumps({"profile": "dev-guidelines"}), encoding="utf-8")
    out, err = io.StringIO(), io.StringIO()
    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
        code = lint_markdown.main(["check", "--offline", str(tmp_path)])
    assert code == 1
    assert "MD015 [no-blank-line-after-subheading]" in out.getvalue()
    assert "T0050-old-task.md" not in out.getvalue()


def test_config_filename_constants_and_load_profile_fallback(tmp_path: Path) -> None:
    """Verify DEFAULT_CONFIG_FILENAME is .lint-markdown.json and LEGACY_CONFIG_FILENAME is .markdown-lint.json."""
    from support_python.markdown import profiles

    assert profiles.DEFAULT_CONFIG_FILENAME == ".lint-markdown.json"
    assert getattr(profiles, "LEGACY_CONFIG_FILENAME", None) == ".markdown-lint.json"

    # Directory lookup with only legacy file
    legacy_file = tmp_path / ".markdown-lint.json"
    legacy_file.write_text(json.dumps({"disable": ["MD018"]}), encoding="utf-8")
    prof_leg = load_profile(tmp_path)
    assert "MD018" not in prof_leg.enabled_rules

    # Directory lookup when both exist: .lint-markdown.json wins
    new_file = tmp_path / ".lint-markdown.json"
    new_file.write_text(json.dumps({"profile": "dev-guidelines"}), encoding="utf-8")
    prof_both = load_profile(tmp_path)
    assert prof_both == DEV_GUIDELINES_PROFILE


def test_kebab_case_profile_keys_match_snake_case_twin(tmp_path) -> None:
    import json

    snake = tmp_path / "snake.json"
    snake.write_text(
        json.dumps({"disabled_rules": ["MD018"], "historical_task_exemptions": False, "excludes": ["x"]}), encoding="utf-8"
    )
    kebab = tmp_path / "kebab.json"
    kebab.write_text(
        json.dumps({"disabled-rules": ["MD018"], "historical-task-exemptions": False, "excludes": ["x"]}), encoding="utf-8"
    )
    assert load_profile(kebab) == load_profile(snake)
    assert "MD018" not in load_profile(kebab).enabled_rules
    assert load_profile(kebab).historical_task_exemptions is False


def test_profile_with_both_key_spellings_prefers_kebab_case(tmp_path) -> None:
    import json

    cfg = tmp_path / "both.json"
    cfg.write_text(json.dumps({"disable_rules": ["MD018"], "disable-rules": ["MD019"]}), encoding="utf-8")
    enabled = load_profile(cfg).enabled_rules
    assert "MD019" not in enabled
    assert "MD018" in enabled
