#!/usr/bin/env python3
"""
Unit and end-to-end tests for support_python.tools.agent_digest (`agent-digest`).
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
DEV_GUIDELINES_LINK_BASE = "https://github.com/gpellicciotta/dev-guidelines/blob/main/"

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


def run_action(action, *args, **kwargs) -> tuple[int, str, str]:
    """Run an action function capturing stdout and stderr."""
    out, err = io.StringIO(), io.StringIO()
    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
        code = action(*args, **kwargs)
    return code, out.getvalue(), err.getvalue()


def make_sources(root: Path) -> tuple[Path, Path, Path]:
    """Create a minimal guidelines directory with one core guideline and one skill guideline."""
    src_dir = root / "guidelines"
    digest_path = src_dir / "agent-digest.md"
    skills_dir = root / "skills"
    src_dir.mkdir(parents=True)
    (src_dir / "general-guidelines.md").write_text(
        "# General Guidelines\n\n- Core rule.\n- See [Sample](ui-guidelines.md).\n",
        encoding="utf-8",
    )
    (src_dir / "ui-guidelines.md").write_text(SKILL_GUIDELINE, encoding="utf-8")
    return src_dir, digest_path, skills_dir


def assert_stderr_lines_formatted(test: unittest.TestCase, stderr: str) -> None:
    """Assert every stderr line carries an 11-char severity indicator or a continuation indent."""
    lines = [line for line in stderr.splitlines() if line.strip()]
    test.assertTrue(lines, "Expected error output on stderr")
    for line in lines:
        test.assertTrue(
            line.startswith(("**[ERROR]** ", "**[WARN]**  ")) or line.startswith(" " * 12),
            f"Unformatted stderr line: {line!r}",
        )


class TestAgentDigestConstantsRemoval(unittest.TestCase):
    def test_dev_guidelines_specific_constants_are_removed(self) -> None:
        for removed_attr in ("SOURCE_FILES", "GUIDELINES_DIR", "DIGEST_PATH", "SKILLS_DIR", "PLAN_OWNED_SKILLS"):
            with self.subTest(attr=removed_attr):
                self.assertFalse(
                    hasattr(generate_agent_digest, removed_attr),
                    f"{removed_attr} should be removed from agent_digest",
                )


class TestPathCollectionAndOrdering(unittest.TestCase):
    def test_collect_input_files_handles_files_recursive_dirs_hidden_dirs_and_duplicates(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            docs = root / "docs"
            nested = docs / "sub"
            hidden = docs / ".hidden"
            nested.mkdir(parents=True)
            hidden.mkdir(parents=True)

            f_top = root / "top.md"
            f_a = docs / "a.md"
            f_b = docs / "b.md"
            f_sub = nested / "c.md"
            f_hidden = hidden / "secret.md"
            f_txt = docs / "ignored.txt"

            for f in (f_top, f_a, f_b, f_sub, f_hidden):
                f.write_text("# Doc\n\n- Short rule.\n", encoding="utf-8")
            f_txt.write_text("not markdown\n", encoding="utf-8")

            collected = generate_agent_digest.collect_input_files(
                [f_top, docs, f_a, f_top],
                digest_path=root / "agent-digest.md",
                skills_dir=root / "agent-skills",
            )
            self.assertEqual(
                collected,
                [f_top.resolve(), f_a.resolve(), f_b.resolve(), f_sub.resolve()],
            )

    def test_collect_input_files_excludes_digest_and_skills_dir_inside_input_dir(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            digest_path = root / "agent-digest.md"
            skills_dir = root / "agent-skills"
            skill_sub = skills_dir / "sample-skill"
            skill_sub.mkdir(parents=True)

            source_md = root / "guide.md"
            source_md.write_text("# Guide\n\n- Directive.\n", encoding="utf-8")
            digest_path.write_text("## Old Digest\n", encoding="utf-8")
            (skill_sub / "SKILL.md").write_text("---\nname: sample-skill\n---\n# Skill\n", encoding="utf-8")
            (skill_sub / "refs.md").write_text("# Ref\n", encoding="utf-8")

            collected = generate_agent_digest.collect_input_files(
                [root],
                digest_path=digest_path,
                skills_dir=skills_dir,
            )
            self.assertEqual(collected, [source_md.resolve()])

    def test_missing_or_non_markdown_paths_exit_2(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            txt_file = root / "notes.txt"
            txt_file.write_text("plain text\n", encoding="utf-8")
            missing = root / "does-not-exist.md"

            for action in ("generate", "check"):
                for bad_path in (missing, txt_file):
                    with self.subTest(action=action, path=bad_path.name):
                        code, _, err = run_main([action, str(bad_path)])
                        self.assertEqual(code, 2)
                        self.assertIn(bad_path.name, err)
                        assert_stderr_lines_formatted(self, err)

    def test_generate_and_check_without_paths_report_usage_error_and_exit_2(self) -> None:
        for action in ("generate", "check"):
            with self.subTest(action=action):
                code, out, err = run_main([action])
                self.assertEqual(code, 2)
                self.assertEqual(out, "")
                self.assertIn("Usage: agent-digest", err)
                assert_stderr_lines_formatted(self, err)

    def test_index_ordering_orders_indexed_then_unindexed_with_stable_ties(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            guidelines = root / "guidelines"
            guidelines.mkdir()

            file_a = guidelines / "a.md"
            file_b = guidelines / "b.md"
            file_c = guidelines / "c.md"
            extra = root / "extra.md"

            file_a.write_text("# File A\n\n- Rule A.\n", encoding="utf-8")
            file_b.write_text("---\nindex: 1\n---\n# File B\n\n- Rule B.\n", encoding="utf-8")
            file_c.write_text("---\nindex: 1\n---\n# File C\n\n- Rule C.\n", encoding="utf-8")
            extra.write_text("---\nindex: 0\n---\n# Extra\n\n- Rule Extra.\n", encoding="utf-8")

            ordered = generate_agent_digest.collect_input_files([guidelines, extra])
            self.assertEqual(
                ordered,
                [extra.resolve(), file_b.resolve(), file_c.resolve(), file_a.resolve()],
            )

            digest = generate_agent_digest.build_digest([guidelines, extra])
            pos_extra = digest.index("## Extra")
            pos_b = digest.index("## File B")
            pos_c = digest.index("## File C")
            pos_a = digest.index("## File A")
            self.assertLess(pos_extra, pos_b)
            self.assertLess(pos_b, pos_c)
            self.assertLess(pos_c, pos_a)

    def test_non_integer_index_exits_1_and_names_file(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            bad_file = root / "bad-index.md"
            bad_file.write_text("---\nindex: first\n---\n# Bad\n\n- Rule.\n", encoding="utf-8")

            for action in ("generate", "check"):
                with self.subTest(action=action):
                    code, _, err = run_main(
                        [
                            action,
                            str(bad_file),
                            "--digest",
                            str(root / "out.md"),
                            "--skills-dir",
                            str(root / "skills"),
                        ]
                    )
                    self.assertEqual(code, 1)
                    self.assertIn("bad-index.md", err)
                    assert_stderr_lines_formatted(self, err)


class TestOutputOptionsAndDefaults(unittest.TestCase):
    def test_generate_uses_default_digest_and_skills_dir_in_cwd(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            src_dir = root / "src_docs"
            src_dir.mkdir()
            (src_dir / "core.md").write_text("# Core\n\n- Short rule.\n", encoding="utf-8")
            (src_dir / "skill.md").write_text(SKILL_GUIDELINE, encoding="utf-8")

            orig_cwd = Path.cwd()
            os.chdir(root)
            try:
                code, _, err = run_main(["generate", "src_docs"])
                self.assertEqual(code, 0, err)
                self.assertTrue((root / "agent-digest.md").is_file())
                self.assertIn("## Core", (root / "agent-digest.md").read_text(encoding="utf-8"))
                self.assertTrue((root / "agent-skills" / "sample-guidelines" / "SKILL.md").is_file())

                check_code, _, check_err = run_main(["check", "src_docs"])
                self.assertEqual(check_code, 0, check_err)
            finally:
                os.chdir(orig_cwd)

    def test_generate_respects_custom_digest_and_skills_dir_options(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            src_dir = root / "guidelines"
            src_dir.mkdir()
            (src_dir / "core.md").write_text("# Core\n\n- Short rule.\n", encoding="utf-8")
            (src_dir / "skill.md").write_text(SKILL_GUIDELINE, encoding="utf-8")

            custom_digest = root / "out" / "custom-digest.md"
            custom_skills = root / "out" / "custom-skills"

            code, _, err = run_main(
                [
                    "generate",
                    str(src_dir),
                    "--digest",
                    str(custom_digest),
                    "--skills-dir",
                    str(custom_skills),
                ]
            )
            self.assertEqual(code, 0, err)
            self.assertTrue(custom_digest.is_file())
            self.assertTrue((custom_skills / "sample-guidelines" / "SKILL.md").is_file())


class TestLinkBaseAndSkillLinks(unittest.TestCase):
    def test_github_and_relative_skill_md_urls_rewrite_to_skill_reference(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            core = root / "core.md"
            skill = root / "testing.md"
            core.write_text(
                "# Core\n\n"
                "- Follow [Plan Task Usage](https://github.com/gpellicciotta/plan/blob/main/src/plan/skills/plan-task-usage-guidelines/SKILL.md).\n"
                "- Follow [Custom Skill](../other/skills/custom-skill/SKILL.md).\n",
                encoding="utf-8",
            )
            skill.write_text(
                "---\n"
                "skill:\n"
                "  name: testing-guidelines\n"
                "  description: Testing.\n"
                "---\n"
                "# Testing\n\n"
                "- Follow [Research](https://github.com/gpellicciotta/plan/blob/main/src/plan/skills/research-guidelines/SKILL.md).\n",
                encoding="utf-8",
            )

            digest = generate_agent_digest.build_digest([core, skill])
            skills = generate_agent_digest.build_skills([core, skill])

            self.assertIn("Follow the `plan-task-usage-guidelines` skill.", digest)
            self.assertIn("Follow the `custom-skill` skill.", digest)
            self.assertIn("Follow the `research-guidelines` skill.", skills["testing-guidelines"])

    def test_link_base_override_and_missing_origin_keeps_relative_links(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            (root / ".git").mkdir()
            docs = root / "guidelines"
            docs.mkdir()
            (root / "scripts").mkdir()
            (root / "scripts" / "tool.py").write_text("# tool\n", encoding="utf-8")

            core = docs / "core.md"
            core.write_text("# Core\n\n- Run [tool.py](../scripts/tool.py).\n", encoding="utf-8")

            # Without origin remote and without --link-base, link stays relative
            digest_no_base = generate_agent_digest.build_digest([core])
            self.assertIn("[tool.py](../scripts/tool.py)", digest_no_base)

            # And check reports the relative link in digest
            digest_out = root / "agent-digest.md"
            skills_out = root / "agent-skills"
            run_main(["generate", str(core), "--digest", str(digest_out), "--skills-dir", str(skills_out)])
            code, _, err = run_main(["check", str(core), "--digest", str(digest_out), "--skills-dir", str(skills_out)])
            self.assertEqual(code, 1)
            self.assertIn("Relative markdown link in digest: ../scripts/tool.py", err)

            # With --link-base override, link is rewritten and check passes
            custom_base = "https://github.com/acme/project/blob/develop/"
            run_main(
                [
                    "generate",
                    str(core),
                    "--digest",
                    str(digest_out),
                    "--skills-dir",
                    str(skills_out),
                    "--link-base",
                    custom_base,
                ]
            )
            self.assertIn(
                "[tool.py](https://github.com/acme/project/blob/develop/scripts/tool.py)",
                digest_out.read_text(encoding="utf-8"),
            )
            code_ok, _, err_ok = run_main(
                [
                    "check",
                    str(core),
                    "--digest",
                    str(digest_out),
                    "--skills-dir",
                    str(skills_out),
                    "--link-base",
                    custom_base,
                ]
            )
            self.assertEqual(code_ok, 0, err_ok)

    def test_derive_link_base_from_origin_remote_and_branch(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            repo = Path(tmpdir)
            subprocess.run(["git", "init", "-b", "main"], cwd=repo, check=True, capture_output=True)
            subprocess.run(
                ["git", "remote", "add", "origin", "https://github.com/gpellicciotta/dev-guidelines.git"],
                cwd=repo,
                check=True,
                capture_output=True,
            )
            derived = generate_agent_digest.derive_link_base(repo)
            self.assertEqual(derived, "https://github.com/gpellicciotta/dev-guidelines/blob/main/")


class TestMergedCheckAction(unittest.TestCase):
    def test_check_fails_on_stale_digest_stale_skill_budget_violation_and_unlinked_skill(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            src_dir, digest_path, skills_dir = make_sources(root)

            # Generate fresh outputs
            code, _, err = run_main(["generate", str(src_dir), "--digest", str(digest_path), "--skills-dir", str(skills_dir)])
            self.assertEqual(code, 0, err)

            # Fresh check passes with --skill-index
            code, _, err = run_main(
                [
                    "check",
                    str(src_dir),
                    "--digest",
                    str(digest_path),
                    "--skills-dir",
                    str(skills_dir),
                    "--skill-index",
                    str(src_dir / "general-guidelines.md"),
                ]
            )
            self.assertEqual(code, 0, err)

            # 1. Stale digest fails check
            digest_path.write_text("stale digest\n", encoding="utf-8")
            code, _, err = run_main(["check", str(src_dir), "--digest", str(digest_path), "--skills-dir", str(skills_dir)])
            self.assertEqual(code, 1)
            self.assertIn("agent-digest.md is out of date", err)

            # Restore digest, make skill stale -> fails check
            run_main(["generate", str(src_dir), "--digest", str(digest_path), "--skills-dir", str(skills_dir)])
            (skills_dir / "sample-guidelines" / "SKILL.md").write_text("stale skill\n", encoding="utf-8")
            code, _, err = run_main(["check", str(src_dir), "--digest", str(digest_path), "--skills-dir", str(skills_dir)])
            self.assertEqual(code, 1)
            self.assertIn("sample-guidelines/SKILL.md is out of date", err)

            # Restore skill, test word budget violation (--max-words 1)
            run_main(["generate", str(src_dir), "--digest", str(digest_path), "--skills-dir", str(skills_dir)])
            code, _, err = run_main(
                [
                    "check",
                    str(src_dir),
                    "--digest",
                    str(digest_path),
                    "--skills-dir",
                    str(skills_dir),
                    "--max-words",
                    "1",
                ]
            )
            self.assertEqual(code, 1)
            self.assertIn("sentence word budget violation(s)", err)

            # Test byte budget violation (--max-bytes 10)
            code, _, err = run_main(
                [
                    "check",
                    str(src_dir),
                    "--digest",
                    str(digest_path),
                    "--skills-dir",
                    str(skills_dir),
                    "--max-bytes",
                    "10",
                ]
            )
            self.assertEqual(code, 1)
            self.assertIn("exceeds the hard budget limit", err)

            # Test unlinked skill with --skill-index
            index_file = src_dir / "general-guidelines.md"
            index_file.write_text("# General Guidelines\n\n- Core rule without skill link.\n", encoding="utf-8")
            run_main(["generate", str(src_dir), "--digest", str(digest_path), "--skills-dir", str(skills_dir)])
            # Without --skill-index, check passes
            code_no_idx, _, err_no_idx = run_main(
                ["check", str(src_dir), "--digest", str(digest_path), "--skills-dir", str(skills_dir)]
            )
            self.assertEqual(code_no_idx, 0, err_no_idx)
            # With --skill-index, check fails
            code_idx, _, err_idx = run_main(
                [
                    "check",
                    str(src_dir),
                    "--digest",
                    str(digest_path),
                    "--skills-dir",
                    str(skills_dir),
                    "--skill-index",
                    str(index_file),
                ]
            )
            self.assertEqual(code_idx, 1)
            self.assertIn("ui-guidelines.md", err_idx)

    def test_check_rejects_unknown_frontmatter_keys_and_orphan_reference_files(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            src_dir, digest_path, skills_dir = make_sources(root)

            # Unknown top-level key
            (src_dir / "general-guidelines.md").write_text(
                "---\nauthor: test\n---\n# General\n\n- Short rule.\n- See [Sample](ui-guidelines.md).\n",
                encoding="utf-8",
            )
            # Unknown key under skill:
            (src_dir / "ui-guidelines.md").write_text(
                "---\nskill:\n  name: sample-guidelines\n  description: Sample.\n  extra_key: bad\n---\n# Sample\n\n- Rule.\n",
                encoding="utf-8",
            )
            run_main(["generate", str(src_dir), "--digest", str(digest_path), "--skills-dir", str(skills_dir)])
            orphan = skills_dir / "sample-guidelines" / "references" / "orphan.md"
            orphan.parent.mkdir(parents=True)
            orphan.write_text("# Orphan\n", encoding="utf-8")

            code, _, err = run_main(["check", str(src_dir), "--digest", str(digest_path), "--skills-dir", str(skills_dir)])
            self.assertEqual(code, 1)
            self.assertIn("author", err)
            self.assertIn("extra_key", err)
            self.assertIn("Orphan reference file 'references/orphan.md'", err)


class TestGenerateAgentDigestCli(unittest.TestCase):
    def test_bare_invocation_shows_help_without_generating(self) -> None:
        with mock.patch.object(generate_agent_digest, "action_generate", side_effect=AssertionError("generate ran")):
            code, out, err = run_main([])
        self.assertEqual(code, 0)
        self.assertEqual(err, "")
        self.assertRegex(out.splitlines()[0], r"^agent-digest v\S+ - Copyright \(c\) ")
        self.assertIn("Usage:", out)

    def test_help_lists_version_header_actions_options_and_exit_codes(self) -> None:
        code, out, _ = run_main(["help"])
        self.assertEqual(code, 0)
        self.assertRegex(out.splitlines()[0], r"^agent-digest v\S+ - Copyright \(c\) ")
        for fragment in (
            "generate",
            "check",
            "--digest",
            "--skills-dir",
            "--link-base",
            "--max-words",
            "--max-bytes",
            "--skill-index",
            "--log-file",
            "--log-level",
            "--debug",
            "--verbose",
            "Exit codes:",
        ):
            self.assertIn(fragment, out)
        self.assertNotRegex(out, r"(?m)^\s+validate\s")
        self.assertNotIn("Detailed Action Descriptions:", out)

    def test_help_verbose_documents_every_action(self) -> None:
        code, out, _ = run_main(["help", "--verbose"])
        self.assertEqual(code, 0)
        self.assertIn("Detailed Action Descriptions:", out)
        self.assertIn("Examples:", out)

    def test_action_specific_help_shows_only_target_action(self) -> None:
        for action in ("generate", "check"):
            with self.subTest(action=action):
                code, out, err = run_main([action, "--help"])
                self.assertEqual(code, 0)
                self.assertEqual(err, "")
                self.assertIn(f"Detailed Action Description: {action}", out)
                self.assertIn(f"Usage:\n  agent-digest {action} <PATH>...", out)
                for other_action in ("generate", "check"):
                    if other_action != action:
                        self.assertNotIn(f"Detailed Action Description: {other_action}", out)

    def test_help_subcommand_with_action_argument(self) -> None:
        code, out, err = run_main(["help", "check"])
        self.assertEqual(code, 0)
        self.assertEqual(err, "")
        self.assertIn("Detailed Action Description: check", out)
        self.assertNotIn("Detailed Action Description: generate", out)

    def test_validate_is_rejected_as_unknown_subcommand_exiting_2(self) -> None:
        code, out, err = run_main(["validate"])
        self.assertEqual(code, 2)
        self.assertEqual(out, "")
        self.assertIn("Unknown subcommand: 'validate'", err)
        self.assertRegex(err, r"(?m)^ {12}Usage: agent-digest \{help\|version\|generate\|check\}")
        assert_stderr_lines_formatted(self, err)

    def test_check_emits_startup_and_completion_banners_and_logs_to_file(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            src_dir, digest_path, skills_dir = make_sources(Path(tmpdir))
            run_main(["generate", str(src_dir), "--digest", str(digest_path), "--skills-dir", str(skills_dir)])
            log_path = Path(tmpdir) / "digest.log"
            code, out, err = run_main(
                [
                    "check",
                    str(src_dir),
                    "--digest",
                    str(digest_path),
                    "--skills-dir",
                    str(skills_dir),
                    "--max-bytes",
                    "100000",
                    "--log-file",
                    str(log_path),
                    "--verbose",
                ]
            )
            self.assertEqual(code, 0, err)
            self.assertRegex(out, r"Starting agent-digest v\S+ with configuration:\n- Command: check\n")
            self.assertIn("- Max bytes: 100000", out)
            self.assertRegex(out, r"Finished agent-digest check in \d+\.\ds with status: succeeded")
            content = log_path.read_text(encoding="utf-8")
            self.assertRegex(content, r"^\[\d{4}-\d\d-\d\d \d\d:\d\d:\d\d\] \*\*\[INFO\]\*\*  Starting agent-digest")
            self.assertIn("with status: succeeded", content)

    def test_log_level_error_suppresses_info_output_and_debug_emits_debug(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            src_dir, digest_path, skills_dir = make_sources(Path(tmpdir))
            base_args = [
                "check",
                str(src_dir),
                "--digest",
                str(digest_path),
                "--skills-dir",
                str(skills_dir),
            ]
            run_main(["generate", str(src_dir), "--digest", str(digest_path), "--skills-dir", str(skills_dir)])
            code, out, err = run_main([*base_args, "--log-level", "ERROR"])
            self.assertEqual(code, 0)
            self.assertEqual(out, "")
            self.assertEqual(err, "")

            code_dbg, out_dbg, _ = run_main([*base_args, "--debug", "--verbose"])
            self.assertEqual(code_dbg, 0)
            self.assertIn("- Log level: DEBUG", out_dbg)
            self.assertRegex(out_dbg, r"(?m)^\*\*\[DEBUG\]\*\* ")

    def test_unknown_option_reports_formatted_error_and_exit_2(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            log_path = Path(tmpdir) / "error.log"
            code, _, err = run_main(["check", "--bogus", "--log-file", str(log_path)])
            self.assertEqual(code, 2)
            self.assertIn("--bogus", err)
            assert_stderr_lines_formatted(self, err)
            self.assertTrue(log_path.exists())
            self.assertIn("--bogus", log_path.read_text(encoding="utf-8"))

    def test_check_lists_each_up_to_date_skill_only_when_verbose(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            src_dir, digest_path, skills_dir = make_sources(Path(tmpdir))
            opts = {"paths": [src_dir], "digest_path": digest_path, "skills_dir": skills_dir}
            code, out, _ = run_action(generate_agent_digest.action_generate, logger=CliLogger(), **opts)
            self.assertEqual(code, 0)
            self.assertIn("sample-guidelines/SKILL.md", out)

            code, out, err = run_action(generate_agent_digest.action_check, logger=CliLogger(), **opts)
            self.assertEqual((code, err), (0, ""))
            self.assertNotIn("sample-guidelines/SKILL.md is up to date", out)
            self.assertIn("All 1 derived skill(s) are up to date.", out)

            code, out, _ = run_action(generate_agent_digest.action_check, logger=CliLogger(verbose=True), **opts)
            self.assertEqual(code, 0)
            self.assertIn("sample-guidelines/SKILL.md is up to date", out)


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

    def test_installed_agent_digest_version_and_bare_help(self) -> None:
        res_ver = self.run_script("version")
        self.assertEqual(res_ver.returncode, 0, res_ver.stderr)
        self.assertRegex(res_ver.stdout.strip(), r"^agent-digest v\S+ - Copyright \(c\) ")

        res_bare = self.run_script()
        self.assertEqual(res_bare.returncode, 0, res_bare.stderr)
        self.assertNotIn("Generated ", res_bare.stdout)

    def test_check_succeeds_on_fixture_checkout_with_explicit_options(self) -> None:
        result = self.run_script(
            "check",
            "guidelines",
            "--digest",
            "guidelines/agent-digest.md",
            "--skills-dir",
            "skills",
            "--skill-index",
            "guidelines/general-guidelines.md",
            "--link-base",
            DEV_GUIDELINES_LINK_BASE,
            "--verbose",
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("Starting agent-digest v", result.stdout)
        self.assertRegex(result.stdout, r"Finished agent-digest check in \d+\.\ds with status: succeeded")


if __name__ == "__main__":
    unittest.main()
