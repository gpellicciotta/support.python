#!/usr/bin/env python3
"""
Unit tests for support_python.tools.agent_digest (`agent-digest`).
"""

from __future__ import annotations

import contextlib
import io
import os
import shutil
import subprocess
import sys
import sysconfig
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from support_python.logging import CliLogger
from support_python.tools import agent_digest as generate_agent_digest

TESTS_DIR = Path(__file__).resolve().parent.parent
SRC_DIR = TESTS_DIR.parent / "src"
FIXTURE_ROOT = TESTS_DIR / "fixtures" / "agent_digest"

SKILL_GUIDELINE = """---
skill:
  name: sample-guidelines
  description: Sample guidelines description.
---

# Sample Guidelines

- Sample rule.
"""


def resolve_console_script(name: str = "agent-digest") -> str:
    """Resolve an installed console script executable in the active Python environment."""
    search_dirs = [Path(sysconfig.get_path("scripts")), Path(sys.executable).parent]
    for scripts_dir in search_dirs:
        for suffix in ("", ".exe", ".cmd", ".bat"):
            candidate = scripts_dir / f"{name}{suffix}"
            if candidate.is_file():
                return str(candidate)
    raise AssertionError(f"Console script '{name}' not found in {search_dirs}")


def run_main(argv: list[str]) -> tuple[int, str, str]:
    """Run main() capturing stdout and stderr."""
    out, err = io.StringIO(), io.StringIO()
    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
        code = generate_agent_digest.main(argv)
    return code, out.getvalue(), err.getvalue()


def run_action(action, **kwargs) -> tuple[int, str, str]:
    """Run an action function capturing stdout and stderr."""
    out, err = io.StringIO(), io.StringIO()
    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
        code = action(**kwargs)
    return code, out.getvalue(), err.getvalue()


def make_sources(root: Path) -> tuple[Path, Path]:
    """Create a minimal guidelines directory with one core guideline and one skill guideline."""
    src_dir = root / "guidelines"
    skills_dir = root / "skills"
    src_dir.mkdir(parents=True)
    (src_dir / "general-guidelines.md").write_text(
        "# General Guidelines\n\n- Core rule.\n- See [Sample](ui-guidelines.md).\n",
        encoding="utf-8",
    )
    (src_dir / "ui-guidelines.md").write_text(SKILL_GUIDELINE, encoding="utf-8")
    return src_dir, skills_dir


def assert_stderr_lines_formatted(test: unittest.TestCase, stderr: str) -> None:
    """Assert every stderr line carries an 11-char severity indicator or a continuation indent."""
    lines = [line for line in stderr.splitlines() if line.strip()]
    test.assertTrue(lines, "Expected error output on stderr")
    for line in lines:
        test.assertTrue(
            line.startswith(("**[ERROR]** ", "**[WARN]**  ")) or line.startswith(" " * 12),
            f"Unformatted stderr line: {line!r}",
        )


class TestGenerateAgentDigestCli(unittest.TestCase):
    def setUp(self) -> None:
        self._repo_patch = mock.patch.object(generate_agent_digest, "REPO_ROOT", FIXTURE_ROOT)
        self._repo_patch.start()
        self.addCleanup(self._repo_patch.stop)

    def test_digest_defers_plan_rules_and_preserves_personal_rules(self) -> None:
        digest = generate_agent_digest.build_digest()
        self.assertIn("In projects managed with plan, follow plan's bundled skills for tasks, reviews, and evidence.", digest)
        for fragment in (
            "## Task Sizing",
            "Always create a companion task file",
            "to the task file",
            "in the task file before implementation",
            "under `### Tests`",
            "TDD execution steps",
            "Never use @dummy",
            "Record findings for sibling projects",
            "An automated loop pushes or deploys",
        ):
            with self.subTest(fragment=fragment):
                self.assertNotIn(fragment, digest)
        for fragment in (
            "Ask clarifying questions before proceeding",
            "Practice test-driven development",
            "Define concrete unit test cases",
            "Standing consent never covers reading external secrets",
            "Never fake, simulate, or fabricate",
        ):
            with self.subTest(fragment=fragment):
                self.assertIn(fragment, digest)

    def test_plan_owned_skills_are_not_generated(self) -> None:
        skills = generate_agent_digest.build_skills()
        for name in ("plan-task-usage-guidelines", "research-guidelines"):
            self.assertNotIn(name, set(skills))
        self.assertIn("testing-guidelines", skills)

    def test_bare_invocation_shows_help_without_generating(self) -> None:
        with mock.patch.object(generate_agent_digest, "action_generate", side_effect=AssertionError("generate ran")):
            code, out, err = run_main([])
        self.assertEqual(code, 0)
        self.assertEqual(err, "")
        self.assertRegex(out.splitlines()[0], r"^agent-digest v\S+ - Copyright \(c\) ")
        self.assertIn("Usage:", out)

    def test_help_lists_version_header_actions_logging_options_and_exit_codes(self) -> None:
        code, out, _ = run_main(["help"])
        self.assertEqual(code, 0)
        self.assertRegex(out.splitlines()[0], r"^agent-digest v\S+ - Copyright \(c\) ")
        for fragment in (
            "generate",
            "check",
            "validate",
            "--log-file",
            "--log-level",
            "--debug",
            "--verbose",
            "--max-bytes",
            "Exit codes:",
        ):
            self.assertIn(fragment, out)
        self.assertNotIn("Detailed Action Descriptions:", out)

    def test_help_verbose_documents_every_action(self) -> None:
        code, out, _ = run_main(["help", "--verbose"])
        self.assertEqual(code, 0)
        self.assertIn("Detailed Action Descriptions:", out)
        self.assertIn("Examples:", out)

    def test_action_specific_help_shows_only_target_action(self) -> None:
        for action in ("generate", "check", "validate"):
            with self.subTest(action=action):
                code, out, err = run_main([action, "--help"])
                self.assertEqual(code, 0)
                self.assertEqual(err, "")
                self.assertIn(f"Detailed Action Description: {action}", out)
                self.assertIn(f"Usage:\n  agent-digest {action} [options]", out)
                for other_action in ("generate", "check", "validate"):
                    if other_action != action:
                        self.assertNotIn(f"Detailed Action Description: {other_action}", out)

    def test_help_subcommand_with_action_argument(self) -> None:
        code, out, err = run_main(["help", "check"])
        self.assertEqual(code, 0)
        self.assertEqual(err, "")
        self.assertIn("Detailed Action Description: check", out)
        self.assertNotIn("Detailed Action Description: generate", out)

    def test_validate_emits_startup_and_completion_banners(self) -> None:
        code, out, _ = run_main(["validate", "--max-bytes", "100000"])
        self.assertEqual(code, 0)
        self.assertRegex(out, r"Starting agent-digest v\S+ with configuration:\n- Command: validate\n")
        self.assertIn("- Max bytes: 100000", out)
        self.assertRegex(out, r"Finished agent-digest validate in \d+\.\ds with status: succeeded")

    def test_log_file_receives_utc_timestamped_entries(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            log_path = Path(tmpdir) / "digest.log"
            code, _, _ = run_main(["validate", "--max-bytes", "100000", "--log-file", str(log_path)])
            self.assertEqual(code, 0)
            content = log_path.read_text(encoding="utf-8")
        self.assertRegex(content, r"^\[\d{4}-\d\d-\d\d \d\d:\d\d:\d\d\] \*\*\[INFO\]\*\*  Starting agent-digest")
        self.assertIn("with status: succeeded", content)

    def test_log_level_error_suppresses_info_output(self) -> None:
        code, out, err = run_main(["validate", "--max-bytes", "100000", "--log-level", "ERROR"])
        self.assertEqual(code, 0)
        self.assertEqual(out, "")
        self.assertEqual(err, "")

    def test_debug_flag_emits_debug_entries(self) -> None:
        code, out, _ = run_main(["validate", "--max-bytes", "100000", "--debug"])
        self.assertEqual(code, 0)
        self.assertIn("- Log level: DEBUG", out)
        self.assertRegex(out, r"(?m)^\*\*\[DEBUG\]\*\* ")

    def test_unknown_option_reports_formatted_error_and_exit_2(self) -> None:
        code, _, err = run_main(["validate", "--bogus"])
        self.assertEqual(code, 2)
        self.assertIn("--bogus", err)
        assert_stderr_lines_formatted(self, err)

    def test_unknown_option_logs_to_log_file(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            log_path = Path(tmpdir) / "error.log"
            code, _, err = run_main(["validate", "--bogus", "--log-file", str(log_path)])
            self.assertEqual(code, 2)
            self.assertIn("--bogus", err)
            self.assertTrue(log_path.exists())
            content = log_path.read_text(encoding="utf-8")
            self.assertIn("--bogus", content)
            self.assertRegex(content, r"\[\d{4}-\d\d-\d\d \d\d:\d\d:\d\d\] \*\*\[ERROR\]\*\* ")

    def test_unknown_action_logs_to_log_file(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            log_path = Path(tmpdir) / "error.log"
            code, _, err = run_main(["bogus", "--log-file", str(log_path)])
            self.assertEqual(code, 2)
            self.assertIn("Unknown subcommand: 'bogus'", err)
            self.assertTrue(log_path.exists())
            content = log_path.read_text(encoding="utf-8")
            self.assertIn("Unknown subcommand: 'bogus'", content)
            self.assertRegex(content, r"\[\d{4}-\d\d-\d\d \d\d:\d\d:\d\d\] \*\*\[ERROR\]\*\* ")

    def test_unknown_action_or_leading_option_reports_formatted_error_and_exit_2(self) -> None:
        for argv in (["bogus"], ["--bogus"]):
            with self.subTest(argv=argv):
                code, out, err = run_main(argv)
                self.assertEqual(code, 2)
                self.assertEqual(out, "")
                self.assertIn(f"Unknown subcommand: '{argv[0]}'", err)
                self.assertRegex(err, r"(?m)^ {12}Usage: agent-digest \{help\|version\|generate\|check\|validate\}")
                assert_stderr_lines_formatted(self, err)

    def test_size_budget_failure_reports_failed_completion(self) -> None:
        code, _, err = run_main(["validate", "--max-bytes", "10"])
        self.assertEqual(code, 1)
        self.assertIn("exceeds the hard budget limit", err)
        self.assertRegex(err, r"Finished agent-digest validate in \d+\.\ds with status: failed")
        assert_stderr_lines_formatted(self, err)


class TestGenerateAgentDigestLogging(unittest.TestCase):
    def test_check_lists_each_up_to_date_skill_only_when_verbose(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            src_dir, skills_dir = make_sources(Path(tmpdir))
            dirs = {"source_dir": src_dir, "skills_root": skills_dir}
            code, out, _ = run_action(generate_agent_digest.action_generate, logger=CliLogger(), **dirs)
            self.assertEqual(code, 0)
            self.assertIn("sample-guidelines/SKILL.md", out)

            code, out, err = run_action(generate_agent_digest.action_check, logger=CliLogger(), **dirs)
            self.assertEqual((code, err), (0, ""))
            self.assertNotIn("sample-guidelines/SKILL.md is up to date", out)
            self.assertIn("All 1 derived skill(s) are up to date.", out)

            code, out, _ = run_action(generate_agent_digest.action_check, logger=CliLogger(verbose=True), **dirs)
            self.assertEqual(code, 0)
            self.assertIn("sample-guidelines/SKILL.md is up to date", out)

    def test_check_reports_stale_files_and_diffs_with_severity_indicators(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            src_dir, skills_dir = make_sources(Path(tmpdir))
            dirs = {"source_dir": src_dir, "skills_root": skills_dir}
            run_action(generate_agent_digest.action_generate, logger=CliLogger(), **dirs)
            (skills_dir / "sample-guidelines" / "SKILL.md").write_text("stale\n", encoding="utf-8")
            (src_dir / "agent-digest.md").write_text("stale\n", encoding="utf-8")

            code, _, err = run_action(generate_agent_digest.action_check, logger=CliLogger(), **dirs)
        self.assertEqual(code, 1)
        self.assertIn("sample-guidelines/SKILL.md is out of date", err)
        self.assertIn("agent-digest.md is out of date", err)
        self.assertIn("-stale", err)
        assert_stderr_lines_formatted(self, err)

    def test_validate_reports_word_budget_violations_with_severity_indicators(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            src_dir, skills_dir = make_sources(Path(tmpdir))
            code, _, err = run_action(
                generate_agent_digest.action_validate,
                max_words=1,
                source_dir=src_dir,
                skills_root=skills_dir,
                logger=CliLogger(),
            )
        self.assertEqual(code, 1)
        self.assertIn("sentence word budget violation(s) in digest", err)
        self.assertIn("sentence word budget violation(s) in skill sample-guidelines", err)
        self.assertRegex(err, r"(?m)^ {12}Line \d+ \(\d+ words\): ")
        assert_stderr_lines_formatted(self, err)


class TestGenerateAgentDigestEndToEnd(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls._tmp = tempfile.TemporaryDirectory()
        cls.repo_root = Path(cls._tmp.name)
        (cls.repo_root / ".git").mkdir()
        shutil.copytree(FIXTURE_ROOT / "guidelines", cls.repo_root / "guidelines")
        shutil.copytree(FIXTURE_ROOT / "skills", cls.repo_root / "skills")

    @classmethod
    def tearDownClass(cls) -> None:
        cls._tmp.cleanup()

    def run_script(self, *args: str) -> subprocess.CompletedProcess:
        executable = resolve_console_script("agent-digest")
        return subprocess.run(
            [executable, *args],
            cwd=self.repo_root,
            env={**os.environ, "PYTHONPATH": str(SRC_DIR)},
            capture_output=True,
            text=True,
            encoding="utf-8",
            timeout=120,
        )

    def test_installed_agent_digest_version_prints_banner_and_exits_0(self) -> None:
        result = self.run_script("version")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertRegex(result.stdout.strip(), r"^agent-digest v\S+ - Copyright \(c\) ")

    def test_bare_invocation_prints_help(self) -> None:
        result = self.run_script()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertRegex(result.stdout.splitlines()[0], r"^agent-digest v\S+ - Copyright \(c\) ")
        self.assertNotIn("Generated ", result.stdout)

    def test_unknown_action_reports_formatted_error(self) -> None:
        result = self.run_script("bogus")
        self.assertEqual(result.returncode, 2)
        self.assertEqual(result.stdout, "")
        self.assertIn("Unknown subcommand: 'bogus'", result.stderr)
        assert_stderr_lines_formatted(self, result.stderr)

    def test_validate_succeeds_with_banners(self) -> None:
        result = self.run_script("validate")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("Starting agent-digest v", result.stdout)
        self.assertRegex(result.stdout, r"Finished agent-digest validate in \d+\.\ds with status: succeeded")


class TestGenerateAgentDigest(unittest.TestCase):
    def setUp(self) -> None:
        self._repo_patch = mock.patch.object(generate_agent_digest, "REPO_ROOT", FIXTURE_ROOT)
        self._repo_patch.start()
        self.addCleanup(self._repo_patch.stop)

    def test_plan_owned_links_remain_portable_without_local_sources(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            source_dir = Path(tmpdir)
            for name in sorted(generate_agent_digest.PLAN_OWNED_SKILLS):
                self.assertNotIn(f"{name}.md", generate_agent_digest.SOURCE_FILES)
                content = f"Follow [guidance](../../plan/src/plan/skills/{name}/SKILL.md)."
                rewritten = generate_agent_digest.rewrite_markdown_links(content, source_dir=source_dir)
                self.assertEqual(rewritten, f"Follow the `{name}` skill.")

    def test_build_digest_filters_blockquotes(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            tmppath = Path(tmpdir)
            # Create mock source files
            for filename in [
                "ai-agent-guidelines.md",
                "plan-task-usage-guidelines.md",
                "general-guidelines.md",
                "markdown-guidelines.md",
                "javascript-guidelines.md",
                "java-guidelines.md",
                "python-guidelines.md",
            ]:
                (tmppath / filename).write_text(
                    f"# Title for {filename}\n\n- Top-level directive.\n  > Rationale blockquote.\n",
                    encoding="utf-8",
                )

            digest = generate_agent_digest.build_digest(source_dir=tmppath)
            self.assertIn("## Title for ai-agent-guidelines.md", digest)
            self.assertIn("- Top-level directive.", digest)
            self.assertNotIn("Rationale blockquote", digest)

    def test_find_budget_violations(self) -> None:
        short_text = "- Valid short sentence."
        self.assertEqual(len(generate_agent_digest.find_budget_violations(short_text, max_words=20)), 0)

        long_sentence = "- This is a sentence with way too many words that will easily exceed the twenty word budget limit enforced by the guidelines protocol."
        violations = generate_agent_digest.find_budget_violations(long_sentence, max_words=20)
        self.assertEqual(len(violations), 1)
        self.assertEqual(violations[0][1], 23)

    def test_cli_help_and_version(self) -> None:
        self.assertEqual(generate_agent_digest.main(["help"]), 0)
        self.assertEqual(generate_agent_digest.main(["help", "--verbose"]), 0)
        self.assertEqual(generate_agent_digest.main(["--help"]), 0)
        self.assertEqual(generate_agent_digest.main(["version"]), 0)
        self.assertEqual(generate_agent_digest.main(["--version"]), 0)

    def test_check_size_budget(self) -> None:
        is_valid, count, limit = generate_agent_digest.check_size_budget("short text", max_bytes=100)
        self.assertTrue(is_valid)
        self.assertEqual(count, len("short text".encode("utf-8")))
        self.assertEqual(limit, 100)

        is_valid, count, limit = generate_agent_digest.check_size_budget("a" * 150, max_bytes=100)
        self.assertFalse(is_valid)
        self.assertEqual(count, 150)
        self.assertEqual(limit, 100)

    def test_action_validate_size_budget(self) -> None:
        # With high limit, validation succeeds if words are within budget
        self.assertEqual(generate_agent_digest.action_validate(max_words=50, max_bytes=100000), 0)
        # With tiny limit (e.g. 10 bytes), validation fails on size
        self.assertEqual(generate_agent_digest.action_validate(max_words=50, max_bytes=10), 1)

    def test_cli_max_bytes_option(self) -> None:
        self.assertEqual(generate_agent_digest.main(["validate", "--max-bytes", "100000"]), 0)
        self.assertEqual(generate_agent_digest.main(["validate", "--max-bytes", "10"]), 1)

    def test_build_skills_and_digest_exclusion(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            tmppath = Path(tmpdir)
            # Create a core guideline without skill:
            (tmppath / "ai-agent-guidelines.md").write_text(
                "# AI Agent Guidelines\n\n- Core behavioral rule.\n  > Rationale.\n",
                encoding="utf-8",
            )
            # Create other core files
            for fn in ["general-guidelines.md"]:
                (tmppath / fn).write_text(f"# {fn}\n\n- Core rule.\n", encoding="utf-8")

            # Create a skill guideline with skill: frontmatter
            (tmppath / "javascript-guidelines.md").write_text(
                """---
skill:
  name: javascript-guidelines
  description: JavaScript guidelines description.
---

# JavaScript Guidelines

- JS rule.
  > JS rationale.
- Repository link [tool](../scripts/tool.py).
""",
                encoding="utf-8",
            )

            # Test build_skills
            skills = generate_agent_digest.build_skills(source_dir=tmppath)
            self.assertIn("javascript-guidelines", skills)
            js_skill = skills["javascript-guidelines"]
            self.assertIn("name: javascript-guidelines", js_skill)
            self.assertIn("description: >-", js_skill)
            self.assertIn("- JS rule.", js_skill)
            self.assertNotIn("JS rationale.", js_skill)
            # Check repository link rewrite rule
            self.assertIn("[tool](https://github.com/gpellicciotta/dev-guidelines/blob/main/scripts/tool.py)", js_skill)

            # Test build_digest excludes the skill
            digest = generate_agent_digest.build_digest(source_dir=tmppath)
            self.assertIn("- Core behavioral rule.", digest)
            self.assertNotIn("- JS rule.", digest)
            self.assertNotIn("javascript-guidelines", digest)

    def test_strict_frontmatter_parser_valid(self) -> None:
        content = """---
skill:
  name: sample-skill
  description: >-
    First line of description.
    Second line of description.
  globs:
    - "*.py"
    - "*.md"
---
# Body
"""
        fm, body = generate_agent_digest.split_frontmatter(content)
        self.assertIsNotNone(fm)
        self.assertEqual(fm["skill"]["name"], "sample-skill")
        self.assertEqual(
            fm["skill"]["description"],
            "First line of description. Second line of description.",
        )
        self.assertEqual(fm["skill"]["globs"], ["*.py", "*.md"])
        self.assertEqual(body.strip(), "# Body")

    def test_strict_frontmatter_parser_rejects_invalid_syntax(self) -> None:
        bad_syntax = """---
skill:
  name: [invalid, inline, list]
---
# Body
"""
        with self.assertRaises(ValueError):
            generate_agent_digest.split_frontmatter(bad_syntax)

    def test_link_rewriting_rules(self) -> None:
        raw_body = """# Title
- Sibling skill: [Process Management Guidelines](process-management-guidelines.md).
- Sibling non-skill: [AI Agent Guidelines](ai-agent-guidelines.md).
- Own skill file: [playwright-recipes.md](../skills/testing-guidelines/references/playwright-recipes.md).
- Repo file: [lint-markdown.py](../scripts/lint-markdown.py).
- External: [SemVer](https://semver.org).
```markdown
- [lint-markdown.py](../scripts/lint-markdown.py)
```
"""
        # Testing skill rewrite
        rewritten_skill = generate_agent_digest.build_skill_content(
            "testing-guidelines",
            "Testing description",
            raw_body,
        )
        self.assertIn(
            "Sibling skill: the `process-management-guidelines` skill.",
            rewritten_skill,
        )
        self.assertIn("Sibling non-skill: AI Agent Guidelines.", rewritten_skill)
        self.assertIn(
            "Own skill file: [playwright-recipes.md](references/playwright-recipes.md).",
            rewritten_skill,
        )
        self.assertIn(
            "Repo file: [lint-markdown.py](https://github.com/gpellicciotta/dev-guidelines/blob/main/scripts/lint-markdown.py).",
            rewritten_skill,
        )
        self.assertIn("External: [SemVer](https://semver.org).", rewritten_skill)
        # Inside code fence, preserved
        self.assertIn("- [lint-markdown.py](../scripts/lint-markdown.py)", rewritten_skill)

    def test_action_validate_orphan_reference_files(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            skills_dir = Path(tmpdir) / "skills"
            test_skill_dir = skills_dir / "test-skill"
            refs_dir = test_skill_dir / "references"
            refs_dir.mkdir(parents=True)
            (test_skill_dir / "SKILL.md").write_text(
                "---\nname: test-skill\ndescription: test\n---\n# Test\n",
                encoding="utf-8",
            )
            orphan_file = refs_dir / "unlinked.md"
            orphan_file.write_text("# Unlinked\n", encoding="utf-8")

            # Must fail validation because unlinked.md is not linked in SKILL.md
            exit_code = generate_agent_digest.action_validate(skills_root=skills_dir)
            self.assertEqual(exit_code, 1)

    def test_action_validate_unknown_skill_keys(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            src_dir = Path(tmpdir) / "guidelines"
            src_dir.mkdir(parents=True)
            (src_dir / "sample-guidelines.md").write_text(
                """---
skill:
  name: sample-guidelines
  description: Sample
  unknown_key: value
---
# Sample
""",
                encoding="utf-8",
            )
            exit_code = generate_agent_digest.action_validate(source_dir=src_dir)
            self.assertEqual(exit_code, 1)

    def test_action_validate_escaping_links(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            skills_dir = Path(tmpdir) / "skills"
            test_skill_dir = skills_dir / "sample-skill"
            test_skill_dir.mkdir(parents=True)
            (test_skill_dir / "SKILL.md").write_text(
                "---\nname: sample-skill\ndescription: Sample\n---\n# Sample\n- Escaping link [bad](../outside.md).\n",
                encoding="utf-8",
            )
            exit_code = generate_agent_digest.action_validate(skills_root=skills_dir)
            self.assertEqual(exit_code, 1)

    def test_action_validate_coverage_general_guidelines(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            src_dir = Path(tmpdir) / "guidelines"
            src_dir.mkdir(parents=True)
            (src_dir / "general-guidelines.md").write_text(
                "# General Guidelines\n\n- No skills linked here.\n",
                encoding="utf-8",
            )
            (src_dir / "sample-guidelines.md").write_text(
                """---
skill:
  name: sample-guidelines
  description: Sample
---
# Sample
- Valid content.
""",
                encoding="utf-8",
            )
            exit_code = generate_agent_digest.action_validate(source_dir=src_dir)
            self.assertEqual(exit_code, 1)

    def test_all_guidelines_frontmatter_and_skills_integrity(self) -> None:
        repo_root = FIXTURE_ROOT
        guidelines_dir = repo_root / "guidelines"
        skills_dir = repo_root / "skills"

        skills = generate_agent_digest.build_skills(source_dir=guidelines_dir, skills_root=skills_dir)
        self.assertEqual(len(skills), 12)

        # Confirm testing-guidelines links playwright-recipes.md
        testing_skill = skills["testing-guidelines"]
        self.assertIn("[playwright-recipes.md](references/playwright-recipes.md)", testing_skill)
        self.assertNotIn("../skills/testing-guidelines", testing_skill)

        # Confirm markdown-guidelines rewrites lint-markdown.py link
        markdown_skill = skills["markdown-guidelines"]
        self.assertIn(
            "[lint-markdown.py](https://github.com/gpellicciotta/dev-guidelines/blob/main/scripts/lint-markdown.py)", markdown_skill
        )
        self.assertNotIn("../../scripts/lint-markdown.py", markdown_skill)

    def test_execution_evidence_rules_point_at_companion_validation_proof(self) -> None:
        repo_root = FIXTURE_ROOT
        testing_guideline_file = repo_root / "guidelines" / "testing-guidelines.md"
        testing_skill_file = repo_root / "skills" / "testing-guidelines" / "SKILL.md"

        self.assertTrue(testing_guideline_file.exists())
        self.assertTrue(testing_skill_file.exists())

        testing_guideline_content = testing_guideline_file.read_text(encoding="utf-8")
        testing_skill_content = testing_skill_file.read_text(encoding="utf-8")

        for label, content in (("guideline", testing_guideline_content), ("skill", testing_skill_content)):
            self.assertIn(
                "Paste the verbatim terminal output of that run into the companion `validation-proof.md` file's `## Walkthrough & Validation` section.",
                content,
                f"Missing companion validation-proof reference in testing {label}",
            )
            self.assertNotIn(
                "into the task file's `## Walkthrough & Validation` section",
                content,
                f"Stale task file inline walkthrough reference in testing {label}",
            )

    def test_execution_evidence_accepts_affected_tests_under_loop_verification(self) -> None:
        repo_root = FIXTURE_ROOT
        testing_guideline_file = repo_root / "guidelines" / "testing-guidelines.md"
        testing_skill_file = repo_root / "skills" / "testing-guidelines" / "SKILL.md"

        self.assertTrue(testing_guideline_file.exists())
        self.assertTrue(testing_skill_file.exists())

        testing_guideline_content = testing_guideline_file.read_text(encoding="utf-8")
        testing_skill_content = testing_skill_file.read_text(encoding="utf-8")

        for label, content in (("guideline", testing_guideline_content), ("skill", testing_skill_content)):
            self.assertIn(
                "Accept failing-first and affected-test runs as task evidence when a project's work loop owns full-suite verification.",
                content,
                f"Missing affected-test rule in testing {label}",
            )
            self.assertIn(
                "Inspect recorded affected-test evidence during review rather than rerunning entire test suites.",
                content,
                f"Missing reviewer affected-test rule in testing {label}",
            )

    def test_agent_files_get_digest_generator_returns_packaged_module_without_script(self) -> None:
        from support_python.tools import agent_files

        with tempfile.TemporaryDirectory() as tmpdir:
            repo_root = Path(tmpdir).resolve()
            (repo_root / ".git").mkdir()
            self.assertFalse((repo_root / "scripts" / "generate-agent-digest.py").exists())
            with mock.patch.object(agent_files, "REPO_ROOT", repo_root):
                generator = agent_files.get_digest_generator()
            self.assertIs(generator, generate_agent_digest)


if __name__ == "__main__":
    unittest.main()
