#!/usr/bin/env python3
"""
Regression tests for support_python.tools.agent_files (`agent-files`) deterministic guarded-block sync.

Run directly with: pytest tests/tools/test_agent_files.py
"""

from __future__ import annotations

import contextlib
import io
import json
import os
import shutil
import stat
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from support_python.tools import agent_files as sync_mod

SRC_DIR = Path(__file__).resolve().parents[2] / "src"
_MODULE_PATH = SRC_DIR / "support_python" / "tools" / "agent_files.py"


class BuildGuardedBlockTests(unittest.TestCase):
    def test_wraps_digest_with_markers(self) -> None:
        block = sync_mod.build_guarded_block("Some digest content.")
        self.assertTrue(block.startswith(sync_mod.MARKER_BEGIN))
        self.assertTrue(block.endswith(sync_mod.MARKER_END))
        self.assertIn("Some digest content.", block)


class ApplyGuardedBlockTests(unittest.TestCase):
    def setUp(self) -> None:
        self.block = sync_mod.build_guarded_block("DIGEST-V1")

    def test_first_time_insert_into_empty_file(self) -> None:
        result = sync_mod.apply_guarded_block("", self.block)
        self.assertEqual(result, self.block.strip() + "\n")

    def test_first_time_insert_puts_digest_first_and_preserves_trailing_content(self) -> None:
        existing = "# My Personal Notes\n\n- Do not push without asking.\n"
        result = sync_mod.apply_guarded_block(existing, self.block)
        self.assertTrue(result.startswith(sync_mod.MARKER_BEGIN))
        # Trailing personal content must survive byte-for-byte, just relocated after the block.
        self.assertIn("# My Personal Notes\n\n- Do not push without asking.", result)
        self.assertLess(result.index(sync_mod.MARKER_END), result.index("My Personal Notes"))

    def test_replaces_existing_block_in_place_leaving_surrounding_content_untouched(self) -> None:
        old_block = sync_mod.build_guarded_block("DIGEST-OLD")
        existing = f"{old_block}\n\n# Personal Section\n\n- Keep this.\n"
        new_block = sync_mod.build_guarded_block("DIGEST-NEW")

        result = sync_mod.apply_guarded_block(existing, new_block)

        self.assertIn("DIGEST-NEW", result)
        self.assertNotIn("DIGEST-OLD", result)
        self.assertIn("# Personal Section\n\n- Keep this.", result)

    def test_idempotent_when_content_already_matches(self) -> None:
        existing = f"{self.block}\n\n# Personal\n"
        result = sync_mod.apply_guarded_block(existing, self.block)
        self.assertEqual(result, existing.strip() + "\n")

    def test_raises_when_only_begin_marker_present(self) -> None:
        broken = f"{sync_mod.MARKER_BEGIN}\nsome content, no end marker\n"
        with self.assertRaises(ValueError):
            sync_mod.apply_guarded_block(broken, self.block)

    def test_raises_when_only_end_marker_present(self) -> None:
        broken = f"some content\n{sync_mod.MARKER_END}\n"
        with self.assertRaises(ValueError):
            sync_mod.apply_guarded_block(broken, self.block)

    def test_raises_when_end_marker_precedes_begin_marker(self) -> None:
        broken = f"{sync_mod.MARKER_END}\nstuff\n{sync_mod.MARKER_BEGIN}\n"
        with self.assertRaises(ValueError):
            sync_mod.apply_guarded_block(broken, self.block)


class SyncToolTests(unittest.TestCase):
    def _make_tool(self, target_file: Path) -> "sync_mod.Tool":
        return sync_mod.Tool("fake-tool", "fake-cmd", target_file, lambda p, t, timeout: [])

    def test_update_writes_new_file_with_digest_first(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            target = Path(tmp_dir) / "AGENT.md"
            tool = self._make_tool(target)
            block = sync_mod.build_guarded_block("DIGEST")

            with contextlib.redirect_stdout(io.StringIO()):
                ok = sync_mod.sync_tool(tool, block, "sync", sync_mod.StderrRoutingLogger(None))

            self.assertTrue(ok)
            content = target.read_text(encoding="utf-8")
            self.assertTrue(content.startswith(sync_mod.MARKER_BEGIN))
            self.assertIn("DIGEST", content)

    def test_update_backs_up_existing_file_before_overwriting(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            target = Path(tmp_dir) / "AGENT.md"
            target.write_text("# Personal\n\n- old note\n", encoding="utf-8")
            tool = self._make_tool(target)
            block = sync_mod.build_guarded_block("DIGEST")

            with contextlib.redirect_stdout(io.StringIO()):
                sync_mod.sync_tool(tool, block, "sync", sync_mod.StderrRoutingLogger(None))

            backups = list(Path(tmp_dir).glob("AGENT.md.bak-*"))
            self.assertEqual(len(backups), 1)
            self.assertIn("old note", backups[0].read_text(encoding="utf-8"))

    def test_update_is_idempotent_on_second_run(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            target = Path(tmp_dir) / "AGENT.md"
            tool = self._make_tool(target)
            block = sync_mod.build_guarded_block("DIGEST")

            with contextlib.redirect_stdout(io.StringIO()):
                sync_mod.sync_tool(tool, block, "sync", sync_mod.StderrRoutingLogger(None))
                backups_after_first = list(Path(tmp_dir).glob("AGENT.md.bak-*"))
                out = io.StringIO()
                with contextlib.redirect_stdout(out):
                    ok = sync_mod.sync_tool(tool, block, "sync", sync_mod.StderrRoutingLogger(None))

            self.assertTrue(ok)
            self.assertIn("already up to date", out.getvalue())
            # No new backup should be made for a no-op run.
            backups_after_second = list(Path(tmp_dir).glob("AGENT.md.bak-*"))
            self.assertEqual(len(backups_after_first), len(backups_after_second))

    def test_diff_does_not_write_and_reports_pending_change(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            target = Path(tmp_dir) / "AGENT.md"
            tool = self._make_tool(target)
            block = sync_mod.build_guarded_block("DIGEST")

            with contextlib.redirect_stdout(io.StringIO()) as out:
                ok = sync_mod.sync_tool(tool, block, "check", sync_mod.StderrRoutingLogger(None))

            self.assertFalse(ok)
            self.assertFalse(target.exists())
            self.assertIn("pending changes", out.getvalue())

    def test_diff_reports_up_to_date_when_no_change_needed(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            target = Path(tmp_dir) / "AGENT.md"
            tool = self._make_tool(target)
            block = sync_mod.build_guarded_block("DIGEST")
            target.write_text(block.strip() + "\n", encoding="utf-8")

            with contextlib.redirect_stdout(io.StringIO()) as out:
                ok = sync_mod.sync_tool(tool, block, "check", sync_mod.StderrRoutingLogger(None))

            self.assertTrue(ok)
            self.assertIn("already up to date", out.getvalue())


class FormatDurationTests(unittest.TestCase):
    def test_sub_minute_shows_one_decimal_seconds(self) -> None:
        self.assertEqual(sync_mod.format_duration(12.3), "12.3s")

    def test_over_a_minute_shows_minutes_and_seconds(self) -> None:
        self.assertEqual(sync_mod.format_duration(75), "1m 15s")

    def test_over_an_hour_shows_hours_minutes_seconds(self) -> None:
        self.assertEqual(sync_mod.format_duration(3725), "1h 02m 05s")


class FormatSeverityIndicatorTests(unittest.TestCase):
    def test_info_and_warn_are_padded_to_five_characters(self) -> None:
        self.assertEqual(sync_mod.format_severity_indicator("INFO"), "**[INFO]** ")
        self.assertEqual(sync_mod.format_severity_indicator("WARN"), "**[WARN]** ")

    def test_error_and_debug_are_not_padded(self) -> None:
        self.assertEqual(sync_mod.format_severity_indicator("ERROR"), "**[ERROR]**")
        self.assertEqual(sync_mod.format_severity_indicator("DEBUG"), "**[DEBUG]**")

    def test_none_level_is_empty(self) -> None:
        self.assertEqual(sync_mod.format_severity_indicator(None), "")


class StderrRoutingLoggerTests(unittest.TestCase):
    def test_appends_across_reopen_instead_of_overwriting(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            log_path = Path(tmp_dir) / "test.log"
            with contextlib.redirect_stdout(io.StringIO()):
                logger = sync_mod.StderrRoutingLogger(log_path)
                logger.log("first")
                logger.close()
                logger = sync_mod.StderrRoutingLogger(log_path)
                logger.log("second")
                logger.close()

            content = log_path.read_text(encoding="utf-8")
            self.assertIn("first", content)
            self.assertIn("second", content)

    def test_debug_message_reaches_file_only_when_debug_enabled(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            log_path = Path(tmp_dir) / "test.log"
            with contextlib.redirect_stdout(io.StringIO()) as out:
                logger = sync_mod.StderrRoutingLogger(log_path, debug=True)
                logger.log("secret detail", level="DEBUG")
                logger.close()

            self.assertIn("**[DEBUG]** secret detail", out.getvalue())
            self.assertIn("secret detail", log_path.read_text(encoding="utf-8"))

    def test_debug_message_discarded_entirely_when_debug_disabled(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            log_path = Path(tmp_dir) / "test.log"
            with contextlib.redirect_stdout(io.StringIO()) as out:
                logger = sync_mod.StderrRoutingLogger(log_path, debug=False)
                logger.log("should not appear anywhere", level="DEBUG")
                logger.close()

            self.assertNotIn("should not appear anywhere", out.getvalue())
            if log_path.exists():
                self.assertNotIn("should not appear anywhere", log_path.read_text(encoding="utf-8"))
            else:
                self.assertFalse(log_path.exists())

    def test_file_lines_carry_timestamp_stdout_lines_do_not(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            log_path = Path(tmp_dir) / "test.log"
            with contextlib.redirect_stdout(io.StringIO()) as out:
                logger = sync_mod.StderrRoutingLogger(log_path)
                logger.log("hello", level="INFO")
                logger.close()

            file_content = log_path.read_text(encoding="utf-8")
            self.assertRegex(file_content, r"^\[\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}\] \*\*\[INFO\]\*\*\s+hello")
            self.assertNotRegex(out.getvalue(), r"\d{4}-\d{2}-\d{2}")


class MainCliLoggingTests(unittest.TestCase):
    def test_version_output_format_and_exit_code(self) -> None:
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            code = sync_mod.main(["--version"])
        self.assertEqual(code, 0)
        output = out.getvalue().strip()
        self.assertEqual(output.count("\n"), 0)
        self.assertRegex(output, r"^agent-files v\d+\.\d+\.\d+.* - .+$")

    def test_version_subcommand_output_format_and_exit_code(self) -> None:
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            code = sync_mod.main(["version"])
        self.assertEqual(code, 0)
        output = out.getvalue().strip()
        self.assertEqual(output.count("\n"), 0)
        self.assertRegex(output, r"^agent-files v\d+\.\d+\.\d+.* - .+$")

    def test_version_and_help_do_not_create_a_log_file(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            log_path = Path(tmp_dir) / "should-not-exist.log"
            with contextlib.redirect_stdout(io.StringIO()):
                sync_mod.main(["--version", "--log-file", str(log_path)])
                sync_mod.main(["help", "--log-file", str(log_path)])
            self.assertFalse(log_path.exists())

    def test_list_writes_tools_table_to_log_file(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            log_path = Path(tmp_dir) / "list.log"
            out = io.StringIO()
            with contextlib.redirect_stdout(out):
                code = sync_mod.main(["list", "--log-file", str(log_path)])
            self.assertEqual(code, 0)
            self.assertIn("Configured AI tools", out.getvalue())
            self.assertTrue(log_path.exists())
            content = log_path.read_text(encoding="utf-8")
            self.assertIn("Configured AI tools", content)
            self.assertRegex(content, r"\[\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}\] Configured AI tools")

    def test_check_writes_start_and_end_banner_to_log_file(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            log_path = Path(tmp_dir) / "sync.log"
            digest_path = Path(tmp_dir) / "agent-digest.md"
            digest_path.write_text("Some digest text.", encoding="utf-8")
            fake_target = Path(tmp_dir) / "FAKE_AGENTS.md"
            fake_tool = sync_mod.Tool("fake-tool", "fake-cmd", fake_target, lambda p, t, timeout: [])

            original_digest, original_tools = sync_mod.DIGEST_PATH, sync_mod.TOOLS
            sync_mod.DIGEST_PATH = digest_path
            sync_mod.TOOLS = [fake_tool]
            try:
                with contextlib.redirect_stdout(io.StringIO()):
                    sync_mod.main(["check", "--log-file", str(log_path)])
            finally:
                sync_mod.DIGEST_PATH = original_digest
                sync_mod.TOOLS = original_tools

            content = log_path.read_text(encoding="utf-8")
            self.assertIn("Starting agent-files v", content)
            self.assertIn("- Command: check", content)
            self.assertIn("- Tools selected: fake-tool", content)
            self.assertIn("- Dry run: false", content)
            self.assertIn("Finished agent-files check in", content)
            # The fake target file does not exist yet, so check reports pending changes and exits 1.
            self.assertIn("with status: failed", content)


def _run_main(argv: list[str]) -> tuple[int, str, str]:
    """Run main() with argv, returning the exit code and captured stdout and stderr."""
    out, err = io.StringIO(), io.StringIO()
    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
        code = sync_mod.main(argv)
    return code, out.getvalue(), err.getvalue()


class HarnessHelpTests(unittest.TestCase):
    def assert_full_help(self, text: str) -> None:
        self.assertRegex(text.splitlines()[0], r"^agent-files v\d+\.\d+\.\d+.* - .+$")
        for section in ("Usage:", "Actions:", "Options:", "Exit codes:"):
            self.assertIn(section, text)
        for action in ("list", "sync", "check", "review", "version", "help"):
            self.assertRegex(text, rf"(?m)^  {action}\s{{2,}}\S")
        for removed in ("update", "diff"):
            self.assertNotRegex(text, rf"(?m)^  {removed}\s{{2,}}\S")
        for option in ("--dry-run", "--no-prune", "--timeout", "--log-file", "--log-level", "--verbose", "--debug"):
            self.assertRegex(text, rf"(?m)^  (-\w, )?{option}\b")
        self.assertRegex(text, r"(?m)^  --timeout SECONDS\s+\S")
        self.assertNotIn("Run with --verbose for full option details", text)

    def test_bare_invocation_shows_full_help_and_exits_zero(self) -> None:
        code, out, err = _run_main([])
        self.assertEqual(code, 0)
        self.assertEqual(err, "")
        self.assert_full_help(out)

    def test_non_verbose_help_documents_actions_and_options(self) -> None:
        for argv in (["help"], ["--help"], ["-h"]):
            with self.subTest(argv=argv):
                code, out, _ = _run_main(argv)
                self.assertEqual(code, 0)
                self.assert_full_help(out)
                self.assertNotIn("Detailed Action Descriptions:", out)

    def test_verbose_help_adds_action_details_and_examples(self) -> None:
        code, out, _ = _run_main(["help", "--verbose"])
        self.assertEqual(code, 0)
        self.assert_full_help(out)
        self.assertIn("Detailed Action Descriptions:", out)
        self.assertIn("Examples:", out)
        self.assertIn("agent-files check claude-code", out)
        self.assertIn("agent-files sync --dry-run", out)
        self.assertNotIn("agent-files diff", out)
        self.assertNotIn("agent-files update", out)

    def test_help_does_not_document_a_default_log_file(self) -> None:
        for argv in (["help"], ["help", "--verbose"]):
            with self.subTest(argv=argv):
                _, out, _ = _run_main(argv)
                self.assertNotIn("agent-files.log", out)

    def test_action_specific_help_shows_only_target_action(self) -> None:
        for action in ("list", "sync", "check", "review"):
            with self.subTest(action=action):
                code, out, err = _run_main([action, "--help"])
                self.assertEqual(code, 0)
                self.assertEqual(err, "")
                self.assertIn(f"Detailed Action Description: {action}", out)
                self.assertIn(f"Usage:\n  agent-files {action}", out)
                for other_action in ("list", "sync", "check", "review"):
                    if other_action != action:
                        self.assertNotIn(f"Detailed Action Description: {other_action}", out)

    def test_help_subcommand_with_action_argument(self) -> None:
        code, out, err = _run_main(["help", "sync"])
        self.assertEqual(code, 0)
        self.assertEqual(err, "")
        self.assertIn("Detailed Action Description: sync", out)
        self.assertNotIn("Detailed Action Description: review", out)


class HarnessErrorFormattingTests(unittest.TestCase):
    def test_unknown_action_logs_indicator_error_with_indented_usage(self) -> None:
        code, out, err = _run_main(["bogus"])
        self.assertEqual(code, 2)
        self.assertEqual(out, "")
        lines = err.splitlines()
        self.assertEqual(lines[0], "**[ERROR]** Unknown subcommand: 'bogus'")
        self.assertTrue(lines[1].startswith(" " * 12 + "Usage: agent-files {"))

    def test_update_and_diff_are_rejected_as_unknown_actions_exiting_two(self) -> None:
        for legacy_verb in ("update", "diff"):
            with self.subTest(verb=legacy_verb):
                code, out, err = _run_main([legacy_verb])
                self.assertEqual(code, 2)
                self.assertEqual(out, "")
                lines = err.splitlines()
                self.assertEqual(lines[0], f"**[ERROR]** Unknown subcommand: '{legacy_verb}'")
                self.assertTrue(lines[1].startswith(" " * 12 + "Usage: agent-files {"))

    def test_invalid_option_logs_indicator_error_and_exits_two(self) -> None:
        code, _, err = _run_main(["check", "--bogus"])
        self.assertEqual(code, 2)
        lines = err.splitlines()
        self.assertTrue(lines[0].startswith("**[ERROR]** "), lines[0])
        self.assertIn("--bogus", lines[0])
        self.assertTrue(lines[1].startswith(" " * 12 + "Usage: agent-files check"))

    def test_unknown_tool_name_logs_indicator_error_and_exits_two(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            log_path = Path(tmp_dir) / "sync.log"
            code, out, err = _run_main(["check", "no-such-tool", "--log-file", str(log_path)])
            self.assertFalse(log_path.exists())
        self.assertEqual(code, 2)
        self.assertEqual(out, "")
        lines = err.splitlines()
        self.assertTrue(lines[0].startswith("**[ERROR]** argument TOOL: unknown tool name 'no-such-tool'"), lines[0])
        self.assertTrue(lines[1].startswith(" " * 12 + "Usage: agent-files check [TOOL ...]"))

    def test_missing_digest_logs_indicator_error_and_exits_one(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            root = Path(tmp_dir)
            fake_tool = sync_mod.Tool("fake-tool", "fake-cmd", root / "FAKE_AGENTS.md", lambda p, t, to: [])
            with (
                mock.patch.object(sync_mod, "DIGEST_PATH", root / "missing-digest.md"),
                mock.patch.object(sync_mod, "TOOLS", [fake_tool]),
                mock.patch.object(sync_mod, "get_digest_generator", return_value=None),
            ):
                code, _, err = _run_main(["check", "--log-file", str(root / "sync.log")])
        self.assertEqual(code, 1)
        error_lines = [line for line in err.splitlines() if "agent-digest.md not found" in line]
        self.assertEqual(len(error_lines), 1)
        self.assertTrue(error_lines[0].startswith("**[ERROR]** "), error_lines[0])


class DefaultLogFileTests(unittest.TestCase):
    def test_check_without_log_file_option_creates_no_log_file(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            root = Path(tmp_dir)
            digest_path = root / "agent-digest.md"
            digest_path.write_text("Some digest text.", encoding="utf-8")
            fake_tool = sync_mod.Tool("fake-tool", "fake-cmd", root / "FAKE_AGENTS.md", lambda p, t, to: [])
            original_cwd = Path.cwd()
            os.chdir(root)
            try:
                with (
                    mock.patch.object(sync_mod, "DIGEST_PATH", digest_path),
                    mock.patch.object(sync_mod, "SKILLS_DIR", root / "skills"),
                    mock.patch.object(sync_mod, "TOOLS", [fake_tool]),
                    mock.patch.object(sync_mod, "get_digest_generator", return_value=None),
                ):
                    code, out, _ = _run_main(["check"])
            finally:
                os.chdir(original_cwd)
            self.assertEqual(code, 1)
            self.assertIn("- Log file: none", out)
            self.assertEqual(list(root.glob("*.log")), [])
            self.assertFalse((sync_mod.REPO_ROOT / "agent-files.log").exists())


class EntryPointTests(unittest.TestCase):
    def test_bare_script_invocation_prints_full_help(self) -> None:
        result = subprocess.run(
            [sys.executable, str(_MODULE_PATH)],
            env={**os.environ, "PYTHONPATH": str(SRC_DIR)},
            capture_output=True,
            text=True,
            encoding="utf-8",
            timeout=60,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("Actions:", result.stdout)
        self.assertIn("--dry-run", result.stdout)


class EnsureDigestTests(unittest.TestCase):
    def test_ensure_digest_warns_on_diff_when_out_of_date(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            digest_path = Path(tmp_dir) / "agent-digest.md"
            digest_path.write_text("old digest", encoding="utf-8")
            log_path = Path(tmp_dir) / "test.log"
            logger = sync_mod.StderrRoutingLogger(log_path)

            mock_generator = mock.Mock()
            mock_generator.build_digest.return_value = "new digest"

            orig_path = sync_mod.DIGEST_PATH
            sync_mod.DIGEST_PATH = digest_path
            try:
                with mock.patch.object(sync_mod, "get_digest_generator", return_value=mock_generator):
                    result = sync_mod.ensure_digest("check", logger)
            finally:
                sync_mod.DIGEST_PATH = orig_path
                logger.close()

            self.assertEqual(result, "old digest")
            log_content = log_path.read_text(encoding="utf-8")
            self.assertIn("is out of date compared to source guidelines", log_content)

    def test_ensure_digest_regenerates_on_update_when_out_of_date(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            digest_path = Path(tmp_dir) / "agent-digest.md"
            digest_path.write_text("old digest", encoding="utf-8")
            log_path = Path(tmp_dir) / "test.log"
            logger = sync_mod.StderrRoutingLogger(log_path)

            mock_generator = mock.Mock()
            mock_generator.build_digest.return_value = "new digest"

            orig_path = sync_mod.DIGEST_PATH
            sync_mod.DIGEST_PATH = digest_path
            try:
                with mock.patch.object(sync_mod, "get_digest_generator", return_value=mock_generator):
                    result = sync_mod.ensure_digest("sync", logger)
            finally:
                sync_mod.DIGEST_PATH = orig_path
                logger.close()

            self.assertEqual(result, "new digest")
            self.assertEqual(digest_path.read_text(encoding="utf-8"), "new digest")
            log_content = log_path.read_text(encoding="utf-8")
            self.assertIn("Regenerated agent-digest.md from source guidelines", log_content)


class SkillDiscoveryTests(unittest.TestCase):
    def test_get_available_skills_finds_valid_skill_directories(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            root = Path(tmp_dir)
            skill1 = root / "skill-one"
            skill1.mkdir()
            (skill1 / "SKILL.md").write_text("---\nname: skill-one\n---\n", encoding="utf-8")

            skill2 = root / "skill-two"
            skill2.mkdir()
            (skill2 / "SKILL.md").write_text("---\nname: skill-two\n---\n", encoding="utf-8")

            # Non-skill directory (missing SKILL.md)
            (root / "not-a-skill").mkdir()

            # Loose file
            (root / "random.txt").write_text("hello", encoding="utf-8")

            skills = sync_mod.get_available_skills(root)
            self.assertEqual(len(skills), 2)
            self.assertEqual([s.name for s in skills], ["skill-one", "skill-two"])

    def test_get_available_skills_returns_empty_when_dir_missing(self) -> None:
        skills = sync_mod.get_available_skills(Path("nonexistent_path_12345"))
        self.assertEqual(skills, [])


class CompareSkillTreesTests(unittest.TestCase):
    def test_detects_new_skill_not_installed(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            src = Path(tmp_dir) / "src_skill"
            src.mkdir()
            (src / "SKILL.md").write_text("skill content", encoding="utf-8")
            dest = Path(tmp_dir) / "nonexistent"

            diffs, _ = sync_mod.compare_skill_trees(src, dest)
            self.assertEqual(len(diffs), 1)
            self.assertIn("not yet installed", diffs[0])

    def test_detects_content_mismatch_and_missing_files(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            src = Path(tmp_dir) / "src_skill"
            src.mkdir()
            (src / "SKILL.md").write_text("version 2", encoding="utf-8")
            (src / "extra.md").write_text("extra", encoding="utf-8")

            dest = Path(tmp_dir) / "dest_skill"
            dest.mkdir()
            (dest / "SKILL.md").write_text("version 1", encoding="utf-8")

            diffs, _ = sync_mod.compare_skill_trees(src, dest)
            self.assertEqual(len(diffs), 2)
            self.assertTrue(any("missing file in target: extra.md" in d for d in diffs))
            self.assertTrue(any("content mismatch: SKILL.md" in d for d in diffs))

    def test_clean_when_trees_identical(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            src = Path(tmp_dir) / "src_skill"
            src.mkdir()
            (src / "SKILL.md").write_text("identical", encoding="utf-8")
            sub = src / "sub"
            sub.mkdir()
            (sub / "doc.txt").write_text("subdoc", encoding="utf-8")

            dest = Path(tmp_dir) / "dest_skill"
            dest.mkdir()
            (dest / "SKILL.md").write_text("identical", encoding="utf-8")
            dest_sub = dest / "sub"
            dest_sub.mkdir()
            (dest_sub / "doc.txt").write_text("subdoc", encoding="utf-8")

            diffs, _ = sync_mod.compare_skill_trees(src, dest)
            self.assertEqual(diffs, [])


class SyncToolSkillsTests(unittest.TestCase):
    def test_sync_tool_skills_copies_skill_on_update(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            src_root = Path(tmp_dir) / "skills"
            skill_dir = src_root / "my-skill"
            skill_dir.mkdir(parents=True)
            (skill_dir / "SKILL.md").write_text("skill text", encoding="utf-8")

            target_skills_dir = Path(tmp_dir) / "tool_skills"
            fake_tool = sync_mod.Tool(
                "fake-tool",
                "fake-cmd",
                Path(tmp_dir) / "AGENT.md",
                lambda p, t, to: [],
                skills_dir=target_skills_dir,
            )

            logger = sync_mod.StderrRoutingLogger(None)
            with contextlib.redirect_stdout(io.StringIO()):
                ok = sync_mod.sync_tool_skills(fake_tool, [skill_dir], "sync", logger)

            self.assertTrue(ok)
            installed_skill = target_skills_dir / "my-skill" / "SKILL.md"
            self.assertTrue(installed_skill.is_file())
            self.assertEqual(installed_skill.read_text(encoding="utf-8"), "skill text")

    def test_sync_tool_skills_returns_false_on_diff_when_pending(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            src_root = Path(tmp_dir) / "skills"
            skill_dir = src_root / "my-skill"
            skill_dir.mkdir(parents=True)
            (skill_dir / "SKILL.md").write_text("skill text", encoding="utf-8")

            target_skills_dir = Path(tmp_dir) / "tool_skills"
            fake_tool = sync_mod.Tool(
                "fake-tool",
                "fake-cmd",
                Path(tmp_dir) / "AGENT.md",
                lambda p, t, to: [],
                skills_dir=target_skills_dir,
            )

            logger = sync_mod.StderrRoutingLogger(None)
            with contextlib.redirect_stdout(io.StringIO()):
                ok = sync_mod.sync_tool_skills(fake_tool, [skill_dir], "check", logger)

            self.assertFalse(ok)


class SkillPruningTests(unittest.TestCase):
    """Stale skill and stale file pruning, always against temporary directories."""

    def _setup(self, tmp_dir: str, manifest_skills: list[str] | None = None) -> tuple["sync_mod.Tool", list[Path], Path]:
        src_root = Path(tmp_dir) / "skills"
        skill_dir = src_root / "kept-skill"
        skill_dir.mkdir(parents=True)
        (skill_dir / "SKILL.md").write_text("skill text", encoding="utf-8")

        target = Path(tmp_dir) / "tool_skills"
        for name in ("kept-skill", "renamed-skill", "plan-task-usage", "ui-verification", "synced"):
            (target / name).mkdir(parents=True)
            (target / name / "SKILL.md").write_text("skill text", encoding="utf-8")
        if manifest_skills is not None:
            (target / sync_mod.SKILLS_MANIFEST_NAME).write_text(
                json.dumps({"schema_version": 1, "source": "dev-guidelines", "skills": manifest_skills}),
                encoding="utf-8",
            )

        tool = sync_mod.Tool("fake-tool", "fake-cmd", Path(tmp_dir) / "AGENT.md", lambda p, t, to: [], skills_dir=target)
        return tool, [skill_dir], target

    def _run(self, tool: "sync_mod.Tool", skills: list[Path], action: str, prune: bool = True) -> tuple[bool, str]:
        with contextlib.redirect_stdout(io.StringIO()) as out, contextlib.redirect_stderr(io.StringIO()) as err:
            ok = sync_mod.sync_tool_skills(tool, skills, action, sync_mod.StderrRoutingLogger(None), prune=prune)
        return ok, out.getvalue() + err.getvalue()

    def test_update_prunes_manifest_listed_skill_missing_from_source(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            tool, skills, target = self._setup(tmp_dir, ["kept-skill", "renamed-skill"])

            ok, output = self._run(tool, skills, "sync")

            self.assertTrue(ok)
            self.assertIn("sync: pruned stale skill 'renamed-skill'", output)
            self.assertFalse((target / "renamed-skill").exists())
            self.assertTrue((target / "kept-skill" / "SKILL.md").is_file())
            # Legacy names are only a bootstrap fallback; an existing manifest does not list them.
            self.assertTrue((target / "plan-task-usage").is_dir())
            self.assertTrue((target / "synced").is_dir())
            manifest = json.loads((target / sync_mod.SKILLS_MANIFEST_NAME).read_text(encoding="utf-8"))
            self.assertEqual(manifest, {"schema_version": 1, "source": "dev-guidelines", "skills": ["kept-skill"]})

    def test_update_prunes_plan_owned_skills_and_preserves_unlisted_skills(self) -> None:
        names = ("plan-task-usage-guidelines", "research-guidelines")
        with tempfile.TemporaryDirectory() as tmp_dir:
            tool, skills, target = self._setup(tmp_dir, ["kept-skill", *names])
            for name in names:
                (target / name).mkdir()
                (target / name / "SKILL.md").write_text("old skill", encoding="utf-8")
            ok, output = self._run(tool, skills, "sync")
            self.assertTrue(ok)
            for name in names:
                self.assertFalse((target / name).exists())
                self.assertIn(f"pruned stale skill '{name}'", output)
            self.assertTrue((target / "synced").is_dir())
            manifest = json.loads((target / sync_mod.SKILLS_MANIFEST_NAME).read_text(encoding="utf-8"))
            self.assertEqual(manifest["skills"], ["kept-skill"])

    def test_diff_reports_stale_skill_as_pending_without_deleting(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            tool, skills, target = self._setup(tmp_dir, ["kept-skill", "renamed-skill"])
            manifest_before = (target / sync_mod.SKILLS_MANIFEST_NAME).read_text(encoding="utf-8")

            ok, output = self._run(tool, skills, "check")

            self.assertFalse(ok)
            self.assertIn("stale skill 'renamed-skill' would be removed", output)
            self.assertTrue((target / "renamed-skill").is_dir())
            self.assertEqual((target / sync_mod.SKILLS_MANIFEST_NAME).read_text(encoding="utf-8"), manifest_before)

    def test_legacy_names_are_pruned_when_no_manifest_exists(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            tool, skills, target = self._setup(tmp_dir)

            ok, output = self._run(tool, skills, "sync")

            self.assertTrue(ok)
            self.assertIn("[WARN]", output)
            self.assertFalse((target / "plan-task-usage").exists())
            self.assertFalse((target / "ui-verification").exists())
            # Never listed anywhere, so never owned.
            self.assertTrue((target / "renamed-skill").is_dir())
            self.assertTrue((target / "synced").is_dir())
            self.assertTrue((target / sync_mod.SKILLS_MANIFEST_NAME).is_file())

    def test_malformed_manifest_warns_and_falls_back_to_legacy_list(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            tool, skills, target = self._setup(tmp_dir)
            (target / sync_mod.SKILLS_MANIFEST_NAME).write_text("{not json", encoding="utf-8")

            ok, output = self._run(tool, skills, "sync")

            self.assertTrue(ok)
            self.assertIn("[WARN]", output)
            self.assertIn("malformed", output)
            self.assertFalse((target / "ui-verification").exists())
            self.assertTrue((target / "renamed-skill").is_dir())

    def test_unlisted_directory_survives_every_action(self) -> None:
        for action, prune in (("check", True), ("sync", True), ("sync", False)):
            with self.subTest(action=action, prune=prune), tempfile.TemporaryDirectory() as tmp_dir:
                tool, skills, target = self._setup(tmp_dir, ["kept-skill", "renamed-skill"])
                self._run(tool, skills, action, prune=prune)
                self.assertTrue((target / "synced" / "SKILL.md").is_file())

    def test_no_prune_deletes_nothing_and_keeps_ownership(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            tool, skills, target = self._setup(tmp_dir, ["kept-skill", "renamed-skill"])
            (target / "kept-skill" / "old.md").write_text("old", encoding="utf-8")

            ok, output = self._run(tool, skills, "sync", prune=False)

            self.assertTrue(ok)
            self.assertIn("stale skill 'renamed-skill' kept (--no-prune)", output)
            self.assertIn("old.md", output)
            self.assertTrue((target / "renamed-skill").is_dir())
            self.assertTrue((target / "kept-skill" / "old.md").is_file())
            manifest = json.loads((target / sync_mod.SKILLS_MANIFEST_NAME).read_text(encoding="utf-8"))
            self.assertEqual(manifest["skills"], ["kept-skill", "renamed-skill"])

    def test_stale_file_inside_existing_skill_is_reported_and_removed(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            tool, skills, target = self._setup(tmp_dir, ["kept-skill"])
            stale = target / "kept-skill" / "references" / "old.md"
            stale.parent.mkdir()
            stale.write_text("old", encoding="utf-8")

            ok, output = self._run(tool, skills, "check")
            self.assertFalse(ok)
            self.assertIn("stale file in target: references/old.md", output)
            self.assertTrue(stale.is_file())

            ok, _ = self._run(tool, skills, "sync")
            self.assertTrue(ok)
            self.assertFalse(stale.exists())
            self.assertFalse(stale.parent.exists())
            self.assertTrue((target / "kept-skill" / "SKILL.md").is_file())

    def test_refuses_manifest_entry_that_is_not_a_direct_child(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            outside = Path(tmp_dir) / "outside"
            outside.mkdir()
            (outside / "keep.txt").write_text("keep", encoding="utf-8")
            tool, skills, target = self._setup(tmp_dir, ["kept-skill", "../outside", "synced/SKILL.md"])

            ok, output = self._run(tool, skills, "sync")

            self.assertFalse(ok)
            self.assertIn("[ERROR]", output)
            self.assertTrue((outside / "keep.txt").is_file())
            self.assertTrue((target / "synced" / "SKILL.md").is_file())

    def test_failed_deletion_logs_error_and_fails_the_tool(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            tool, skills, target = self._setup(tmp_dir, ["kept-skill", "renamed-skill"])

            with mock.patch.object(sync_mod.shutil, "rmtree", side_effect=PermissionError("locked")):
                ok, output = self._run(tool, skills, "sync")

            self.assertFalse(ok)
            self.assertIn("[ERROR]", output)
            self.assertIn("FAILED to prune stale skill 'renamed-skill'", output)
            self.assertTrue((target / "renamed-skill").is_dir())


class LegacySkillsDirTests(unittest.TestCase):
    """Cleanup of a deprecated skills directory after a tool's skills target moved."""

    def _setup(self, tmp_dir: str, legacy_manifest: list[str] | None) -> tuple["sync_mod.Tool", list[Path], Path, Path]:
        skill_dir = Path(tmp_dir) / "skills" / "kept-skill"
        skill_dir.mkdir(parents=True)
        (skill_dir / "SKILL.md").write_text("skill text", encoding="utf-8")

        legacy = Path(tmp_dir) / "legacy_skills"
        for name in ("kept-skill", "renamed-skill", ".system"):
            (legacy / name).mkdir(parents=True)
            (legacy / name / "SKILL.md").write_text("skill text", encoding="utf-8")
        if legacy_manifest is not None:
            (legacy / sync_mod.SKILLS_MANIFEST_NAME).write_text(
                json.dumps({"schema_version": 1, "source": "dev-guidelines", "skills": legacy_manifest}),
                encoding="utf-8",
            )

        # The new target is shared with other installers and already holds a same-named legacy skill.
        target = Path(tmp_dir) / "shared_skills"
        (target / "ui-verification").mkdir(parents=True)

        tool = sync_mod.Tool(
            "fake-tool",
            "fake-cmd",
            Path(tmp_dir) / "AGENT.md",
            lambda p, t, to: [],
            skills_dir=target,
            native_skill_discovery=True,
            legacy_skills_dirs=(legacy,),
            bootstrap_skill_names=(),
        )
        return tool, [skill_dir], target, legacy

    def _run(self, tool: "sync_mod.Tool", skills: list[Path], action: str, prune: bool = True) -> tuple[bool, str]:
        with contextlib.redirect_stdout(io.StringIO()) as out, contextlib.redirect_stderr(io.StringIO()) as err:
            ok = sync_mod.sync_tool_skills(tool, skills, action, sync_mod.StderrRoutingLogger(None), prune=prune)
        return ok, out.getvalue() + err.getvalue()

    def test_update_moves_skills_and_removes_owned_copies_from_legacy_dir(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            tool, skills, target, legacy = self._setup(tmp_dir, ["kept-skill", "renamed-skill"])

            ok, output = self._run(tool, skills, "sync")

            self.assertTrue(ok)
            self.assertTrue((target / "kept-skill" / "SKILL.md").is_file())
            self.assertIn(f"sync: pruned stale skill 'kept-skill' from {legacy}", output)
            self.assertFalse((legacy / "kept-skill").exists())
            self.assertFalse((legacy / "renamed-skill").exists())
            self.assertTrue((legacy / ".system" / "SKILL.md").is_file())
            self.assertFalse((legacy / sync_mod.SKILLS_MANIFEST_NAME).exists())
            manifest = json.loads((target / sync_mod.SKILLS_MANIFEST_NAME).read_text(encoding="utf-8"))
            self.assertEqual(manifest["skills"], ["kept-skill"])

            # A second run finds nothing left to do and stays quiet about the missing legacy manifest.
            ok, output = self._run(tool, skills, "check")
            self.assertTrue(ok)
            self.assertNotIn("[WARN]", output)

    def test_diff_reports_legacy_copies_as_pending_without_deleting(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            tool, skills, target, legacy = self._setup(tmp_dir, ["kept-skill", "renamed-skill"])

            ok, output = self._run(tool, skills, "check")

            self.assertFalse(ok)
            self.assertIn(f"stale skill 'renamed-skill' in {legacy} would be removed", output)
            self.assertTrue((legacy / "kept-skill").is_dir())
            self.assertTrue((legacy / "renamed-skill").is_dir())
            self.assertTrue((legacy / sync_mod.SKILLS_MANIFEST_NAME).is_file())
            self.assertFalse((target / "kept-skill").exists())

    def test_no_prune_keeps_legacy_copies_and_rewrites_their_manifest(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            tool, skills, target, legacy = self._setup(tmp_dir, ["kept-skill", "renamed-skill", "already-gone"])

            ok, output = self._run(tool, skills, "sync", prune=False)

            self.assertTrue(ok)
            self.assertIn("kept (--no-prune)", output)
            self.assertTrue((legacy / "kept-skill").is_dir())
            self.assertTrue((legacy / "renamed-skill").is_dir())
            manifest = json.loads((legacy / sync_mod.SKILLS_MANIFEST_NAME).read_text(encoding="utf-8"))
            self.assertEqual(manifest["skills"], ["kept-skill", "renamed-skill"])

    def test_empty_bootstrap_list_prunes_nothing_from_target_without_manifest(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            tool, skills, target, _ = self._setup(tmp_dir, ["kept-skill"])

            ok, _ = self._run(tool, skills, "sync")

            self.assertTrue(ok)
            self.assertTrue((target / "ui-verification").is_dir())

    def test_unowned_same_named_legacy_directory_warns_and_survives(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            tool, skills, _, legacy = self._setup(tmp_dir, None)

            ok, output = self._run(tool, skills, "sync")

            self.assertTrue(ok)
            self.assertIn("[WARN]", output)
            self.assertIn("possible duplicate skill 'kept-skill'", output)
            self.assertTrue((legacy / "kept-skill").is_dir())
            self.assertTrue((legacy / "renamed-skill").is_dir())
            self.assertTrue((legacy / ".system").is_dir())

    def test_failed_legacy_deletion_logs_error_and_fails_the_tool(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            tool, skills, _, legacy = self._setup(tmp_dir, ["kept-skill"])

            with mock.patch.object(sync_mod.shutil, "rmtree", side_effect=PermissionError("locked")):
                ok, output = self._run(tool, skills, "sync")

            self.assertFalse(ok)
            self.assertIn("[ERROR]", output)
            self.assertTrue((legacy / "kept-skill").is_dir())
            self.assertTrue((legacy / sync_mod.SKILLS_MANIFEST_NAME).is_file())


class DryRunCliTests(unittest.TestCase):
    def test_sync_dry_run_writes_and_deletes_nothing(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            root = Path(tmp_dir)
            digest_path = root / "agent-digest.md"
            digest_path.write_text("Some digest text.", encoding="utf-8")
            skill_dir = root / "skills" / "kept-skill"
            skill_dir.mkdir(parents=True)
            (skill_dir / "SKILL.md").write_text("---\nname: kept-skill\n---\n", encoding="utf-8")
            target = root / "tool_skills"
            (target / "ui-verification").mkdir(parents=True)
            fake_target = root / "FAKE_AGENTS.md"
            fake_tool = sync_mod.Tool("fake-tool", "fake-cmd", fake_target, lambda p, t, to: [], skills_dir=target)

            with (
                mock.patch.object(sync_mod, "DIGEST_PATH", digest_path),
                mock.patch.object(sync_mod, "SKILLS_DIR", root / "skills"),
                mock.patch.object(sync_mod, "TOOLS", [fake_tool]),
                mock.patch.object(sync_mod, "get_digest_generator", return_value=None),
                contextlib.redirect_stdout(io.StringIO()) as out,
            ):
                exit_code = sync_mod.main(["sync", "--dry-run", "--log-file", str(root / "sync.log")])

            self.assertEqual(exit_code, 1)
            self.assertIn("stale skill 'ui-verification' would be removed", out.getvalue())
            self.assertTrue((target / "ui-verification").is_dir())
            self.assertFalse((target / "kept-skill").exists())
            self.assertFalse((target / sync_mod.SKILLS_MANIFEST_NAME).exists())
            self.assertFalse(fake_target.exists())


class ParseSkillMetadataTests(unittest.TestCase):
    def test_parses_multiline_folded_frontmatter(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            skill_dir = Path(tmp_dir) / "testing-guidelines"
            skill_dir.mkdir()
            (skill_dir / "SKILL.md").write_text(
                "---\n"
                "name: testing-guidelines\n"
                "description: >-\n"
                "  Automates multi-modal UI verification using Playwright,\n"
                "  combining DOM and Accessibility tree assertions.\n"
                "---\n\n"
                "# Content\n",
                encoding="utf-8",
            )

            meta = sync_mod.parse_skill_metadata(skill_dir)
            self.assertIsNotNone(meta)
            assert meta is not None
            self.assertEqual(meta.name, "testing-guidelines")
            self.assertEqual(
                meta.description,
                "Automates multi-modal UI verification using Playwright, combining DOM and Accessibility tree assertions.",
            )

    def test_parses_single_line_frontmatter(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            skill_dir = Path(tmp_dir) / "simple-skill"
            skill_dir.mkdir()
            (skill_dir / "SKILL.md").write_text(
                "---\nname: 'simple-skill'\ndescription: 'Does a simple task.'\n---\n",
                encoding="utf-8",
            )

            meta = sync_mod.parse_skill_metadata(skill_dir)
            self.assertIsNotNone(meta)
            assert meta is not None
            self.assertEqual(meta.name, "simple-skill")
            self.assertEqual(meta.description, "Does a simple task.")

    def test_returns_none_for_missing_file_or_invalid_frontmatter(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            skill_dir = Path(tmp_dir) / "empty-dir"
            skill_dir.mkdir()
            self.assertIsNone(sync_mod.parse_skill_metadata(skill_dir))

            (skill_dir / "SKILL.md").write_text("# No frontmatter\n", encoding="utf-8")
            self.assertIsNone(sync_mod.parse_skill_metadata(skill_dir))


class FormatDisplaySkillPathTests(unittest.TestCase):
    def test_formats_tilde_path_when_under_home(self) -> None:
        home = Path.home()
        skills_dir = home / ".claude" / "skills"
        formatted = sync_mod.format_display_skill_path(skills_dir, "testing-guidelines")
        self.assertEqual(formatted, "~/.claude/skills/testing-guidelines/SKILL.md")

    def test_falls_back_to_posix_path_when_outside_home(self) -> None:
        skills_dir = Path("/custom/external/skills")
        formatted = sync_mod.format_display_skill_path(skills_dir, "testing-guidelines")
        self.assertTrue(formatted.endswith("custom/external/skills/testing-guidelines/SKILL.md"))


class BuildSkillsCatalogTests(unittest.TestCase):
    def test_returns_empty_for_tools_with_native_skill_discovery(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            skill_dir = Path(tmp_dir) / "test-skill"
            skill_dir.mkdir()
            (skill_dir / "SKILL.md").write_text(
                "---\nname: test-skill\ndescription: Verifies test components.\n---\n",
                encoding="utf-8",
            )
            tool = sync_mod.Tool(
                "any-tool",
                "any-cmd",
                Path(tmp_dir) / "AGENT.md",
                lambda p, t, to: [],
                skills_dir=Path(tmp_dir) / "tool_skills",
                native_skill_discovery=True,
            )
            self.assertEqual(sync_mod.build_skills_catalog(tool, [skill_dir]), "")

    def test_configured_tools_declare_native_skill_discovery(self) -> None:
        flags = {tool.name: tool.native_skill_discovery for tool in sync_mod.TOOLS}
        self.assertEqual(flags, {"claude-code": True, "antigravity": True, "codex-cli": True})

    def test_codex_targets_documented_directory_and_cleans_deprecated_one(self) -> None:
        codex = next(tool for tool in sync_mod.TOOLS if tool.name == "codex-cli")
        self.assertEqual(codex.skills_dir, Path.home() / ".agents" / "skills")
        self.assertEqual(codex.legacy_skills_dirs, (Path.home() / ".codex" / "skills",))
        self.assertEqual(codex.bootstrap_skill_names, ())

    def test_returns_empty_when_no_skills_or_no_skills_dir(self) -> None:
        tool_no_dir = sync_mod.Tool(
            "claude-code",
            "claude",
            Path.home() / ".claude" / "CLAUDE.md",
            lambda p, t, to: [],
            skills_dir=None,
        )
        self.assertEqual(sync_mod.build_skills_catalog(tool_no_dir, [Path("skills/testing-guidelines")]), "")

        tool_with_dir = sync_mod.Tool(
            "claude-code",
            "claude",
            Path.home() / ".claude" / "CLAUDE.md",
            lambda p, t, to: [],
            skills_dir=Path.home() / ".claude" / "skills",
        )
        self.assertEqual(sync_mod.build_skills_catalog(tool_with_dir, []), "")

    def test_generates_catalog_for_tools_without_native_skill_discovery(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            skill_dir = Path(tmp_dir) / "test-skill"
            skill_dir.mkdir()
            (skill_dir / "SKILL.md").write_text(
                "---\nname: test-skill\ndescription: Verifies test components.\n---\n",
                encoding="utf-8",
            )

            other_tool = sync_mod.Tool(
                "other-tool",
                "other",
                Path.home() / ".other" / "AGENTS.md",
                lambda p, t, to: [],
                skills_dir=Path.home() / ".other" / "skills",
            )
            catalog = sync_mod.build_skills_catalog(other_tool, [skill_dir])
            self.assertIn("## Available Skills", catalog)
            self.assertIn("- **test-skill**: Verifies test components.", catalog)
            self.assertIn("Read `~/.other/skills/test-skill/SKILL.md`.", catalog)


class BuildGuardedBlockWithCatalogTests(unittest.TestCase):
    def test_appends_catalog_within_markers(self) -> None:
        digest = "## AI Guidelines\n- Be explicit."
        catalog = "## Available Skills\n- **skill**: Read `~/.claude/skills/skill/SKILL.md`."
        block = sync_mod.build_guarded_block(digest, catalog)

        self.assertTrue(block.startswith(sync_mod.MARKER_BEGIN))
        self.assertTrue(block.endswith(sync_mod.MARKER_END))
        self.assertIn(digest, block)
        self.assertIn(catalog, block)


def _hide(path: Path) -> None:
    """Set the Windows Hidden attribute on path, keeping its other attributes."""
    import ctypes

    attributes = path.stat().st_file_attributes | stat.FILE_ATTRIBUTE_HIDDEN
    if not ctypes.windll.kernel32.SetFileAttributesW(str(path), attributes):
        raise ctypes.WinError()


def _is_hidden(path: Path) -> bool:
    return bool(path.stat().st_file_attributes & stat.FILE_ATTRIBUTE_HIDDEN)


class WriteTextInPlaceTests(unittest.TestCase):
    def test_creates_missing_file(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            target = Path(tmp_dir) / "new.md"

            sync_mod.write_text_in_place(target, "fresh content\n", newline="\n")

            self.assertEqual(target.read_bytes(), b"fresh content\n")

    def test_overwrites_longer_file_without_trailing_old_bytes(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            target = Path(tmp_dir) / "existing.md"
            target.write_bytes(b"a much longer original content that must disappear\n")

            sync_mod.write_text_in_place(target, "short\n", newline="\n")

            self.assertEqual(target.read_bytes(), b"short\n")

    def test_keeps_requested_newline_mode(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            lf_target = Path(tmp_dir) / "lf.md"
            native_target = Path(tmp_dir) / "native.md"
            lf_target.write_bytes(b"old\n")
            native_target.write_bytes(b"old\n")

            sync_mod.write_text_in_place(lf_target, "one\ntwo\n", newline="\n")
            sync_mod.write_text_in_place(native_target, "one\ntwo\n")

            self.assertEqual(lf_target.read_bytes(), b"one\ntwo\n")
            expected_native = f"one{os.linesep}two{os.linesep}".encode()
            self.assertEqual(native_target.read_bytes(), expected_native)


class CopyFileInPlaceTests(unittest.TestCase):
    def test_overwrites_longer_file_and_copies_modification_time(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            src = Path(tmp_dir) / "src.md"
            dst = Path(tmp_dir) / "dst.md"
            src.write_bytes(b"new\n")
            dst.write_bytes(b"a much longer original content\n")
            os.utime(src, (1_600_000_000, 1_600_000_000))

            result = sync_mod.copy_file_in_place(str(src), str(dst))

            self.assertEqual(result, str(dst))
            self.assertEqual(dst.read_bytes(), b"new\n")
            self.assertEqual(int(dst.stat().st_mtime), 1_600_000_000)


@unittest.skipUnless(sys.platform == "win32", "the Hidden attribute exists only on Windows")
class HiddenTargetFileTests(unittest.TestCase):
    """Windows refuses mode "w" on an existing hidden file, so every write site must write in place."""

    def _make_skill(self, root: Path, text: str) -> Path:
        skill_dir = root / "skills" / "my-skill"
        skill_dir.mkdir(parents=True)
        (skill_dir / "SKILL.md").write_text(text, encoding="utf-8")
        return skill_dir

    def test_sync_tool_update_rewrites_hidden_target(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            target = Path(tmp_dir) / "AGENT.md"
            target.write_text("# Personal\n", encoding="utf-8")
            _hide(target)
            tool = sync_mod.Tool("fake-tool", "fake-cmd", target, lambda p, t, timeout: [])
            block = sync_mod.build_guarded_block("DIGEST")

            with contextlib.redirect_stdout(io.StringIO()):
                ok = sync_mod.sync_tool(tool, block, "sync", sync_mod.StderrRoutingLogger(None))

            self.assertTrue(ok)
            self.assertIn("DIGEST", target.read_text(encoding="utf-8"))
            self.assertIn("# Personal", target.read_text(encoding="utf-8"))
            self.assertTrue(_is_hidden(target))

    def test_write_skills_manifest_rewrites_hidden_manifest(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            skills_dir = Path(tmp_dir)
            manifest = skills_dir / sync_mod.SKILLS_MANIFEST_NAME
            sync_mod.write_skills_manifest(skills_dir, ["old-skill"])
            _hide(manifest)

            sync_mod.write_skills_manifest(skills_dir, ["new-skill"])

            self.assertEqual(json.loads(manifest.read_text(encoding="utf-8"))["skills"], ["new-skill"])
            self.assertTrue(_is_hidden(manifest))

    def test_sync_tool_skills_update_overwrites_hidden_skill_file(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            root = Path(tmp_dir)
            skill_dir = self._make_skill(root, "new skill text")
            installed = root / "tool_skills" / "my-skill" / "SKILL.md"
            installed.parent.mkdir(parents=True)
            installed.write_text("old skill text that is longer", encoding="utf-8")
            _hide(installed)
            tool = sync_mod.Tool("fake-tool", "fake-cmd", root / "AGENT.md", lambda p, t, to: [], skills_dir=root / "tool_skills")

            with contextlib.redirect_stdout(io.StringIO()):
                ok = sync_mod.sync_tool_skills(tool, [skill_dir], "sync", sync_mod.StderrRoutingLogger(None))

            self.assertTrue(ok)
            self.assertEqual(installed.read_text(encoding="utf-8"), "new skill text")
            self.assertTrue(_is_hidden(installed))

    def test_main_update_succeeds_with_hidden_agent_skill_and_manifest_files(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            root = Path(tmp_dir)
            digest_path = root / "agent-digest.md"
            digest_path.write_text("Fresh digest text.", encoding="utf-8")
            self._make_skill(root, "---\nname: my-skill\n---\nnew skill text\n")
            tool_skills = root / "tool_skills"
            installed = tool_skills / "my-skill" / "SKILL.md"
            installed.parent.mkdir(parents=True)
            installed.write_text("old skill text that is longer than the new one", encoding="utf-8")
            manifest = tool_skills / sync_mod.SKILLS_MANIFEST_NAME
            sync_mod.write_skills_manifest(tool_skills, ["my-skill", "stale-skill"])
            agent_file = root / "AGENT.md"
            agent_file.write_text("# Personal\n", encoding="utf-8")
            for path in (agent_file, installed, manifest):
                _hide(path)
            tool = sync_mod.Tool("fake-tool", "fake-cmd", agent_file, lambda p, t, to: [], skills_dir=tool_skills)

            with (
                mock.patch.object(sync_mod, "DIGEST_PATH", digest_path),
                mock.patch.object(sync_mod, "SKILLS_DIR", root / "skills"),
                mock.patch.object(sync_mod, "TOOLS", [tool]),
                mock.patch.object(sync_mod, "get_digest_generator", return_value=None),
                contextlib.redirect_stdout(io.StringIO()) as out,
            ):
                exit_code = sync_mod.main(["sync", "--log-file", str(root / "sync.log")])

            self.assertEqual(exit_code, 0, out.getvalue())
            self.assertIn("Fresh digest text.", agent_file.read_text(encoding="utf-8"))
            self.assertEqual(installed.read_text(encoding="utf-8"), "---\nname: my-skill\n---\nnew skill text\n")
            self.assertEqual(json.loads(manifest.read_text(encoding="utf-8"))["skills"], ["my-skill"])
            for path in (agent_file, installed, manifest):
                self.assertTrue(_is_hidden(path), path)


class RepoRootResolutionTests(unittest.TestCase):
    def test_resolves_repo_root_digest_skills_and_generator_from_working_directory(self) -> None:
        from support_python.tools import agent_digest

        with tempfile.TemporaryDirectory() as tmp_dir:
            repo_root = Path(tmp_dir).resolve()
            (repo_root / ".git").mkdir()
            digest_file = repo_root / "guidelines" / "agent-digest.md"
            digest_file.parent.mkdir(parents=True)
            digest_file.write_text("Dynamic repo digest.", encoding="utf-8")
            skill_file = repo_root / "skills" / "sample-skill" / "SKILL.md"
            skill_file.parent.mkdir(parents=True)
            skill_file.write_text("---\nname: sample-skill\n---\n", encoding="utf-8")
            nested_dir = repo_root / "nested" / "sub"
            nested_dir.mkdir(parents=True)

            original_cwd = Path.cwd()
            os.chdir(nested_dir)
            try:
                self.assertEqual(sync_mod.find_project_root(), repo_root)
                self.assertEqual(sync_mod._resolve_repo_root(), repo_root)
                self.assertEqual(sync_mod.load_digest(), "Dynamic repo digest.")
                skills = sync_mod.get_available_skills()
                self.assertEqual([s.name for s in skills], ["sample-skill"])
                self.assertFalse((repo_root / "scripts" / "generate-agent-digest.py").exists())
                generator = sync_mod.get_digest_generator()
                self.assertIs(generator, agent_digest)
                self.assertEqual(generator.find_project_root(Path.cwd()), repo_root)
                self.assertFalse(hasattr(generator, "SOURCE_FILES"))
            finally:
                os.chdir(original_cwd)

    def test_check_and_sync_repo_root_regenerate_digest_from_unrelated_cwd(self) -> None:
        fixture_root = Path(__file__).resolve().parents[1] / "fixtures" / "agent_digest"
        with tempfile.TemporaryDirectory() as tmp_dir:
            root = Path(tmp_dir).resolve()
            copy_dir = root / "guidelines-copy"
            shutil.copytree(fixture_root, copy_dir)
            (copy_dir / ".git").mkdir()

            digest_file = copy_dir / "guidelines" / "agent-digest.md"
            skill_file = copy_dir / "skills" / "python-guidelines" / "SKILL.md"
            expected_digest = digest_file.read_text(encoding="utf-8")
            expected_skill = skill_file.read_text(encoding="utf-8")
            digest_file.write_text("Stale digest content.\n", encoding="utf-8")
            skill_file.write_text("Stale skill content.\n", encoding="utf-8")

            cwd_repo = root / "unrelated-repo"
            (cwd_repo / ".git").mkdir(parents=True)

            target_md = root / "targets" / "CLAUDE.md"
            target_skills = root / "targets" / "skills"
            fake_tool = sync_mod.Tool(
                "fake-tool",
                "nonexistent-fake-cmd-xyz",
                target_md,
                lambda p, t, to: [],
                skills_dir=target_skills,
                native_skill_discovery=True,
            )

            original_cwd = Path.cwd()
            os.chdir(cwd_repo)
            try:
                with mock.patch.object(sync_mod, "TOOLS", [fake_tool]):
                    _, check_out, check_err = _run_main(["check", "--repo-root", str(copy_dir)])
                    self.assertIn(
                        "agent-digest.md is out of date compared to source guidelines (run 'agent-digest' or 'agent-files sync' to synchronize)",
                        check_out + check_err,
                    )
                    self.assertEqual(digest_file.read_text(encoding="utf-8"), "Stale digest content.\n")

                    sync_code, sync_out, sync_err = _run_main(["sync", "--repo-root", str(copy_dir)])
                    self.assertEqual(sync_code, 0, sync_out + sync_err)
                    self.assertIn("Regenerated agent-digest.md from source guidelines", sync_out + sync_err)
                    self.assertEqual(digest_file.read_text(encoding="utf-8"), expected_digest)
                    self.assertEqual(skill_file.read_text(encoding="utf-8"), expected_skill)
                    self.assertEqual([p.relative_to(cwd_repo) for p in cwd_repo.rglob("*")], [Path(".git")])
            finally:
                os.chdir(original_cwd)


class SupportPythonAgentFilesCliTests(unittest.TestCase):
    def test_agent_files_subcommands_dispatch(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            root = Path(tmp_dir).resolve()
            digest_path = root / "agent-digest.md"
            digest_path.write_text("CLI subcommand digest.", encoding="utf-8")
            fake_target = root / "FAKE_AGENTS.md"
            fake_tool = sync_mod.Tool("fake-tool", "nonexistent-fake-cmd-xyz", fake_target, lambda p, t, to: [])

            with (
                mock.patch.object(sync_mod, "DIGEST_PATH", digest_path),
                mock.patch.object(sync_mod, "SKILLS_DIR", root / "skills"),
                mock.patch.object(sync_mod, "TOOLS", [fake_tool]),
                mock.patch.object(sync_mod, "get_digest_generator", return_value=None),
            ):
                list_out = io.StringIO()
                with contextlib.redirect_stdout(list_out):
                    self.assertEqual(sync_mod.main(["list"]), 0)
                self.assertIn("Configured AI tools", list_out.getvalue())

                check_pending_out = io.StringIO()
                with contextlib.redirect_stdout(check_pending_out):
                    self.assertEqual(sync_mod.main(["check"]), 1)
                self.assertFalse(fake_target.exists())

                sync_dry_out = io.StringIO()
                with contextlib.redirect_stdout(sync_dry_out):
                    self.assertEqual(sync_mod.main(["sync", "--dry-run"]), 1)
                self.assertIn("pending changes", sync_dry_out.getvalue())
                self.assertFalse(fake_target.exists())

                sync_out = io.StringIO()
                with contextlib.redirect_stdout(sync_out):
                    self.assertEqual(sync_mod.main(["sync"]), 0)
                self.assertTrue(fake_target.is_file())
                self.assertIn("CLI subcommand digest.", fake_target.read_text(encoding="utf-8"))

                check_out = io.StringIO()
                with contextlib.redirect_stdout(check_out):
                    self.assertEqual(sync_mod.main(["check"]), 0)
                self.assertIn("already up to date", check_out.getvalue())

                review_out = io.StringIO()
                with contextlib.redirect_stdout(review_out):
                    self.assertEqual(sync_mod.main(["review"]), 0)
                self.assertIn("skip: 'nonexistent-fake-cmd-xyz' not found", review_out.getvalue())

    def test_list_json_output_parses_and_contains_documented_keys(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            root = Path(tmp_dir).resolve()
            fake_target, fake_skills = root / "FAKE_AGENTS.md", root / "fake_skills"
            fake_tool = sync_mod.Tool(
                "fake-tool", "nonexistent-fake-cmd-xyz", fake_target, lambda p, t, to: [], skills_dir=fake_skills
            )
            with mock.patch.object(sync_mod, "TOOLS", [fake_tool]):
                code, out, err = _run_main(["list", "--format", "json"])
            self.assertEqual((code, err), (0, ""))
            entry = json.loads(out)[0]
            self.assertEqual(
                entry,
                {
                    "tool": "fake-tool",
                    "command": "nonexistent-fake-cmd-xyz",
                    "available": False,
                    "executable": "not found",
                    "version": "not found",
                    "instructions_file": str(fake_target),
                    "skills_dir": str(fake_skills),
                },
            )

    def test_check_json_output_parses_and_reports_pending_and_up_to_date(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            root = Path(tmp_dir).resolve()
            digest_path = root / "agent-digest.md"
            digest_path.write_text("JSON check digest.", encoding="utf-8")
            skill_dir = root / "skills" / "sample-skill"
            skill_dir.mkdir(parents=True)
            (skill_dir / "SKILL.md").write_text("---\nname: sample-skill\n---\nSkill body\n", encoding="utf-8")
            fake_target, fake_skills = root / "FAKE_AGENTS.md", root / "fake_skills"
            fake_tool = sync_mod.Tool(
                "fake-tool",
                "nonexistent-fake-cmd-xyz",
                fake_target,
                lambda p, t, to: [],
                skills_dir=fake_skills,
                native_skill_discovery=True,
            )
            with (
                mock.patch.object(sync_mod, "DIGEST_PATH", digest_path),
                mock.patch.object(sync_mod, "SKILLS_DIR", root / "skills"),
                mock.patch.object(sync_mod, "TOOLS", [fake_tool]),
                mock.patch.object(sync_mod, "get_digest_generator", return_value=None),
            ):
                code_pending, out_pending, err_pending = _run_main(["check", "--format", "json"])
                self.assertEqual(code_pending, 1, err_pending)
                self.assertFalse(fake_target.exists())
                pending_data = json.loads(out_pending)
                self.assertEqual((pending_data[0]["tool"], pending_data[0]["status"]), ("fake-tool", "changes-pending"))
                self.assertTrue(len(pending_data[0]["changes"]) >= 1)

                self.assertEqual(_run_main(["sync"])[0], 0)
                code_clean, out_clean, err_clean = _run_main(["check", "--format", "json"])
                self.assertEqual((code_clean, err_clean), (0, ""))
                self.assertEqual(json.loads(out_clean), [{"tool": "fake-tool", "status": "up-to-date", "changes": []}])

                # Text and JSON check agree on stale files under --no-prune.
                (fake_skills / "sample-skill" / "extra.md").write_text("stale", encoding="utf-8")
                code_np_txt, out_np_txt, _ = _run_main(["check", "--no-prune"])
                code_np_json, out_np_json, _ = _run_main(["check", "--no-prune", "--format", "json"])
                self.assertEqual((code_np_txt, code_np_json), (1, 1))
                self.assertIn("stale file in target: extra.md", out_np_txt)
                np_entry = json.loads(out_np_json)[0]
                self.assertEqual(np_entry["status"], "changes-pending")
                self.assertTrue(any("stale file in target: extra.md" in c for c in np_entry["changes"]))

                # Invalid guarded-block markers report status: unavailable and exit 1 in both modes.
                (fake_skills / "sample-skill" / "extra.md").unlink()
                fake_target.write_text(f"{sync_mod.MARKER_BEGIN}\nbroken markers without end\n", encoding="utf-8")
                code_err_txt, _, _ = _run_main(["check"])
                code_err_json, out_err_json, _ = _run_main(["check", "--format", "json"])
                self.assertEqual((code_err_txt, code_err_json), (1, 1))
                err_entry = json.loads(out_err_json)[0]
                self.assertEqual(err_entry["status"], "unavailable")
                self.assertTrue(any("invalid target" in c for c in err_entry["changes"]))


class AgentFilesConfigTests(unittest.TestCase):
    def test_load_config_defaults_when_no_file_present(self) -> None:
        from support_python.tools import agent_files_config as cfg_mod

        self.assertEqual(cfg_mod.DEFAULT_CONFIG_FILENAME, ".agent-files.json")
        with tempfile.TemporaryDirectory() as tmp_dir:
            root = Path(tmp_dir).resolve()
            cfg = cfg_mod.load_agent_files_config(repo_root=root)
            self.assertEqual((cfg.repo_root, cfg.digest_path), (root, root / "guidelines" / "agent-digest.md"))
            self.assertEqual((cfg.skills_dir, cfg.marker), (root / "skills", "dev-guidelines"))
            self.assertEqual((cfg.marker_begin, cfg.marker_end), (sync_mod.MARKER_BEGIN, sync_mod.MARKER_END))
            self.assertEqual((cfg.manifest_source, cfg.manifest_name), ("dev-guidelines", ".dev-guidelines-skills.json"))
            self.assertEqual(cfg.legacy_skill_names, ("plan-task-usage", "ui-verification"))
            reg = cfg_mod.ToolRegistry(cfg.tools)
            for name in ("claude", "claude-code", "antigravity", "codex", "codex-cli"):
                self.assertIsNotNone(reg.get(name), name)

    def test_config_discovery_prefers_dotfile_and_warns_on_legacy(self) -> None:
        from support_python.tools import agent_files_config as cfg_mod

        with tempfile.TemporaryDirectory() as tmp_dir:
            root = Path(tmp_dir).resolve()
            dot_cfg = root / ".agent-files.json"
            legacy_cfg = root / "agent-files.json"

            # 1. Only .agent-files.json present -> reads without warning.
            dot_cfg.write_text(json.dumps({"marker": "dot-marker"}), encoding="utf-8")
            err_buf = io.StringIO()
            with contextlib.redirect_stderr(err_buf):
                cfg1 = cfg_mod.load_agent_files_config(repo_root=root)
            self.assertEqual(cfg1.marker, "dot-marker")
            self.assertEqual(err_buf.getvalue(), "")

            # 2. Only legacy agent-files.json present -> reads and logs a WARN mentioning v3.0.0 (and reaches --log-file).
            dot_cfg.unlink()
            legacy_cfg.write_text(json.dumps({"marker": "legacy-marker"}), encoding="utf-8")
            log_file = root / "legacy.log"
            code_l, _, err_l = _run_main(["list", "--repo-root", str(root), "--log-file", str(log_file)])
            self.assertEqual(code_l, 0)
            for text in (err_l, log_file.read_text(encoding="utf-8")):
                self.assertIn("**[WARN]**", text)
                self.assertIn(".agent-files.json", text)
                self.assertIn("v3.0.0", text)

            # 3. Both present -> uses .agent-files.json and warns that legacy file is ignored.
            dot_cfg.write_text(json.dumps({"marker": "dot-wins"}), encoding="utf-8")
            err_buf = io.StringIO()
            with contextlib.redirect_stderr(err_buf):
                cfg3 = cfg_mod.load_agent_files_config(repo_root=root)
            self.assertEqual(cfg3.marker, "dot-wins")
            self.assertIn("**[WARN]**", err_buf.getvalue())
            self.assertIn("ignored", err_buf.getvalue().lower())

    def test_load_config_overrides_from_json_and_cli_flags(self) -> None:
        from support_python.tools import agent_files_config as cfg_mod

        with tempfile.TemporaryDirectory() as tmp_dir:
            root = Path(tmp_dir).resolve()
            cfg_file = root / ".agent-files.json"
            cfg_file.write_text(
                json.dumps(
                    {
                        "repo_root": ".",
                        "digest_path": "custom/digest.md",
                        "skills_dir": "custom/skills",
                        "marker": "custom-rules",
                        "manifest_source": "custom-rules",
                        "legacy_skill_names": ["old-skill-a"],
                    }
                ),
                encoding="utf-8",
            )
            cfg = cfg_mod.load_agent_files_config(cfg_file)
            self.assertEqual((cfg.repo_root, cfg.digest_path), (root, root / "custom" / "digest.md"))
            self.assertEqual((cfg.skills_dir, cfg.marker), (root / "custom" / "skills", "custom-rules"))
            self.assertEqual((cfg.marker_begin, cfg.marker_end), ("<!-- BEGIN custom-rules -->", "<!-- END custom-rules -->"))
            self.assertEqual((cfg.manifest_source, cfg.manifest_name), ("custom-rules", ".custom-rules-skills.json"))
            self.assertEqual(cfg.legacy_skill_names, ("old-skill-a",))

            flag_digest, flag_target = root / "flag" / "digest.md", root / "flag" / "CLAUDE.md"
            flag_digest.parent.mkdir(parents=True)
            flag_digest.write_text("Flag override digest.", encoding="utf-8")
            cfg_file.write_text(
                json.dumps(
                    {
                        "tools": [
                            {"name": "claude-code", "command": "claude", "target_file": str(flag_target), "aliases": ["claude"]}
                        ],
                        "replace_tools": True,
                    }
                ),
                encoding="utf-8",
            )
            help_code, help_out, _ = _run_main(["help"])
            self.assertEqual(help_code, 0)
            self.assertIn("  --digest PATH          guidelines digest file path override", help_out)
            code, out, err = _run_main(
                [
                    "sync",
                    "claude",
                    "--config",
                    str(cfg_file),
                    "--digest-path",
                    str(flag_digest),
                    "--marker",
                    "flag-marker",
                    "--manifest-source",
                    "flag-source",
                    "--legacy-skill",
                    "legacy-one",
                ]
            )
            self.assertEqual(code, 0, out + err)
            written = flag_target.read_text(encoding="utf-8")
            for expected in ("<!-- BEGIN flag-marker -->", "Flag override digest.", "<!-- END flag-marker -->"):
                self.assertIn(expected, written)

    def test_load_config_missing_file_raises_file_not_found(self) -> None:
        from support_python.tools import agent_files_config as cfg_mod

        with tempfile.TemporaryDirectory() as tmp_dir:
            with self.assertRaises(FileNotFoundError):
                cfg_mod.load_agent_files_config(Path(tmp_dir) / "does-not-exist.json")

    def test_load_config_invalid_schema_raises_value_error(self) -> None:
        from support_python.tools import agent_files_config as cfg_mod

        with tempfile.TemporaryDirectory() as tmp_dir:
            root = Path(tmp_dir)
            for idx, payload in enumerate(
                ("{not valid json", '{"not_a_valid_field": 1}', '{"legacy_skill_names": "x"}', '{"tools": [{"name": "x"}]}')
            ):
                p = root / f"bad-{idx}.json"
                p.write_text(payload, encoding="utf-8")
                with self.assertRaises(ValueError):
                    cfg_mod.load_agent_files_config(p)


class SecondProjectMarkerAndManifestTests(unittest.TestCase):
    def test_second_fixture_project_syncs_without_touching_dev_guidelines(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            root = Path(tmp_dir).resolve()
            target_md, target_skills = root / "targets" / "CLAUDE.md", root / "targets" / "skills"
            tool_entry = {
                "name": "test-tool",
                "command": "test-cmd",
                "target_file": str(target_md),
                "skills_dir": str(target_skills),
                "native_skill_discovery": True,
            }

            dg_root = root / "dev-guidelines"
            (dg_root / "guidelines").mkdir(parents=True)
            (dg_root / "guidelines" / "agent-digest.md").write_text("Dev guidelines digest content.", encoding="utf-8")
            (dg_root / "skills" / "dg-skill").mkdir(parents=True)
            (dg_root / "skills" / "dg-skill" / "SKILL.md").write_text("---\nname: dg-skill\n---\nDG\n", encoding="utf-8")
            dg_cfg = dg_root / ".agent-files.json"
            dg_cfg.write_text(json.dumps({"tools": [tool_entry], "replace_tools": True}), encoding="utf-8")

            code, out, err = _run_main(["sync", "--config", str(dg_cfg)])
            self.assertEqual(code, 0, out + err)

            p2_root = root / "second-project"
            p2_digest = p2_root / "docs" / "team-digest.md"
            p2_digest.parent.mkdir(parents=True)
            p2_digest.write_text("Team specific digest v1.", encoding="utf-8")
            p2_skill_old = p2_root / "team-skills" / "team-skill-old" / "SKILL.md"
            p2_skill_old.parent.mkdir(parents=True)
            p2_skill_old.write_text("---\nname: team-skill-old\n---\nOld\n", encoding="utf-8")
            p2_cfg = p2_root / ".agent-files.json"
            p2_cfg.write_text(
                json.dumps(
                    {
                        "digest_path": "docs/team-digest.md",
                        "skills_dir": "team-skills",
                        "marker": "team-guidelines",
                        "manifest_source": "team-guidelines",
                        "tools": [tool_entry],
                        "replace_tools": True,
                    }
                ),
                encoding="utf-8",
            )

            code, out, err = _run_main(["sync", "--config", str(p2_cfg)])
            self.assertEqual(code, 0, out + err)
            combined = target_md.read_text(encoding="utf-8")
            for text in (
                sync_mod.MARKER_BEGIN,
                "Dev guidelines digest content.",
                "<!-- BEGIN team-guidelines -->",
                "Team specific digest v1.",
            ):
                self.assertIn(text, combined)
            self.assertTrue((target_skills / ".dev-guidelines-skills.json").is_file())
            self.assertTrue((target_skills / ".team-guidelines-skills.json").is_file())

            p2_digest.write_text("Team specific digest v2.", encoding="utf-8")
            shutil.rmtree(p2_skill_old.parent)
            p2_skill_new = p2_root / "team-skills" / "team-skill-new" / "SKILL.md"
            p2_skill_new.parent.mkdir(parents=True)
            p2_skill_new.write_text("---\nname: team-skill-new\n---\nNew\n", encoding="utf-8")

            code, out, err = _run_main(["sync", "--config", str(p2_cfg)])
            self.assertEqual(code, 0, out + err)
            updated = target_md.read_text(encoding="utf-8")
            self.assertIn("Dev guidelines digest content.", updated)
            self.assertIn("Team specific digest v2.", updated)
            self.assertNotIn("Team specific digest v1.", updated)
            self.assertTrue((target_skills / "dg-skill" / "SKILL.md").is_file())
            self.assertFalse((target_skills / "team-skill-old").exists())
            self.assertTrue((target_skills / "team-skill-new" / "SKILL.md").is_file())
            self.assertEqual(_run_main(["sync", "--dry-run", "--config", str(dg_cfg)])[0], 0)


class ToolRegistryAndAddedToolTests(unittest.TestCase):
    def test_added_registry_entry_is_listed_and_synced_like_builtin_tools(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            root = Path(tmp_dir).resolve()
            (root / "guidelines").mkdir(parents=True)
            (root / "guidelines" / "agent-digest.md").write_text("Registry test digest.", encoding="utf-8")
            (root / "skills" / "reg-skill").mkdir(parents=True)
            (root / "skills" / "reg-skill" / "SKILL.md").write_text("---\nname: reg-skill\n---\nBody\n", encoding="utf-8")
            custom_target, custom_skills = root / "custom_home" / "CURSOR.md", root / "custom_home" / "skills"
            cfg_file = root / "agent-files.json"
            cfg_file.write_text(
                json.dumps(
                    {
                        "tools": [
                            {
                                "name": "cursor-agent",
                                "command": "nonexistent-cursor-bin",
                                "target_file": str(custom_target),
                                "skills_dir": str(custom_skills),
                                "native_skill_discovery": True,
                            }
                        ]
                    }
                ),
                encoding="utf-8",
            )
            list_out = io.StringIO()
            with contextlib.redirect_stdout(list_out):
                self.assertEqual(sync_mod.main(["list", "--config", str(cfg_file)]), 0)
            self.assertIn("cursor-agent", list_out.getvalue())
            self.assertIn("claude-code", list_out.getvalue())

            with contextlib.redirect_stdout(io.StringIO()):
                self.assertEqual(sync_mod.main(["sync", "cursor-agent", "--config", str(cfg_file)]), 0)
            self.assertIn("Registry test digest.", custom_target.read_text(encoding="utf-8"))
            self.assertTrue((custom_skills / "reg-skill" / "SKILL.md").is_file())
            with contextlib.redirect_stdout(io.StringIO()) as dry_out:
                self.assertEqual(sync_mod.main(["sync", "cursor-agent", "--dry-run", "--config", str(cfg_file)]), 0)
            self.assertIn("already up to date", dry_out.getvalue())

    def test_installed_agent_files_sync_and_check_integration(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            root = Path(tmp_dir).resolve()
            for d in (root / ".git", root / "guidelines", root / "skills" / "int-skill"):
                d.mkdir(parents=True)
            (root / "guidelines" / "agent-digest.md").write_text("Integration fixture digest.", encoding="utf-8")
            (root / "skills" / "int-skill" / "SKILL.md").write_text("---\nname: int-skill\n---\nSkill\n", encoding="utf-8")
            target_file, target_skills = root / "targets" / "CLAUDE.md", root / "targets" / "skills"
            tool_cfg = {
                "name": "claude-code",
                "command": "claude",
                "target_file": str(target_file),
                "skills_dir": str(target_skills),
                "native_skill_discovery": True,
            }
            (root / ".agent-files.json").write_text(json.dumps({"replace_tools": True, "tools": [tool_cfg]}), encoding="utf-8")
            env = {**os.environ, "PYTHONPATH": str(SRC_DIR)}
            exe = shutil.which("agent-files", path=str(Path(sys.executable).parent))
            cmd = [exe] if exe else [sys.executable, str(_MODULE_PATH)]

            res_sync = subprocess.run([*cmd, "sync"], cwd=root, env=env, capture_output=True, text=True, timeout=30)
            self.assertEqual(res_sync.returncode, 0, res_sync.stderr)
            self.assertTrue(target_file.is_file())
            res_clean = subprocess.run([*cmd, "check"], cwd=root, env=env, capture_output=True, text=True, timeout=30)
            self.assertEqual(res_clean.returncode, 0, res_clean.stderr)
            target_file.write_text("Edited target file causing drift.\n", encoding="utf-8")
            res_dirty = subprocess.run([*cmd, "check"], cwd=root, env=env, capture_output=True, text=True, timeout=30)
            self.assertEqual(res_dirty.returncode, 1, res_dirty.stderr)


if __name__ == "__main__":
    unittest.main()
