"""Tests for support_python.cli module."""

from __future__ import annotations

from contextlib import redirect_stdout
import io
import unittest
from unittest.mock import patch

import support_python
import support_python.cli


class RemovedArgparseHelpersTests(unittest.TestCase):
    def test_removed_helpers_are_not_exposed(self) -> None:
        for name in ("build_action_parser", "print_help", "print_version", "format_version"):
            with self.subTest(name=name):
                self.assertFalse(hasattr(support_python.cli, name))
                self.assertNotIn(name, support_python.cli.__all__)
                self.assertFalse(hasattr(support_python, name))
                self.assertNotIn(name, support_python.__all__)


class BuildMetadataVersionTests(unittest.TestCase):
    def test_build_metadata_appends_hash_and_omits_when_missing(self) -> None:
        from support_python.cli import get_full_version, resolve_build_metadata

        resolve_build_metadata.cache_clear()
        with patch("support_python.cli.subprocess.run") as mock_run:
            mock_run.return_value.returncode = 0
            mock_run.return_value.stdout = "af31b0d\n"
            self.assertEqual(resolve_build_metadata(), "af31b0d")
            self.assertEqual(get_full_version("1.2.3-pre"), "1.2.3-pre+af31b0d")

        resolve_build_metadata.cache_clear()
        with patch("support_python.cli.subprocess.run", side_effect=OSError("git not found")):
            self.assertEqual(resolve_build_metadata(), "unknown")
            self.assertEqual(get_full_version("1.2.3-pre"), "1.2.3-pre")
        resolve_build_metadata.cache_clear()

    def test_build_metadata_does_not_default_to_process_cwd(self) -> None:
        from pathlib import Path
        from support_python.cli import resolve_build_metadata

        resolve_build_metadata.cache_clear()
        expected_dir = Path(__file__).resolve().parent.parent / "src" / "support_python"
        with patch("support_python.cli.subprocess.run") as mock_run:
            mock_run.return_value.returncode = 0
            mock_run.return_value.stdout = "deadbee\n"
            resolve_build_metadata()
            called_cwd = Path(mock_run.call_args.kwargs["cwd"]).resolve()
            self.assertEqual(called_cwd, expected_dir.resolve())
        resolve_build_metadata.cache_clear()


class ToolHarnessUnitTests(unittest.TestCase):
    def _make_harness(self, fallback_action: str | None = None):
        from support_python.cli import ToolHarness

        harness = ToolHarness(
            name="demo-tool",
            description="Demo CLI harness for unit testing.",
            version="2.0.0",
            copyright="Copyright (c) Test Corp",
            fallback_action=fallback_action,
            examples=["demo-tool run --target prod"],
            detailed_help="Additional detailed documentation.",
        )

        def configure_run(parser) -> None:
            parser.add_argument("--target", default="dev", help="Target environment")
            parser.add_argument("--fail", action="store_true", help="Simulate failure")

        def handle_run(args, logger) -> int:
            logger.info(f"Running on {args.target}")
            return 1 if args.fail else 0

        harness.add_action(
            "run",
            "execute deployment workflow",
            handler=handle_run,
            detail="Executes the full workflow against the selected target.",
            usage_suffix="[--target ENV] [--fail]",
            configure_parser=configure_run,
        )
        return harness

    def test_registering_actions_yields_banner_help_and_version(self) -> None:
        from support_python.cli import resolve_build_metadata

        resolve_build_metadata.cache_clear()
        with patch("support_python.cli.resolve_build_metadata", return_value="abc1234"):
            harness = self._make_harness()
            self.assertEqual(harness.format_version(), "demo-tool v2.0.0+abc1234 - Copyright (c) Test Corp")
            out = io.StringIO()
            with redirect_stdout(out):
                self.assertEqual(harness.run(["version"]), 0)
            self.assertEqual(out.getvalue().strip(), "demo-tool v2.0.0+abc1234 - Copyright (c) Test Corp")

            help_out = io.StringIO()
            with redirect_stdout(help_out):
                self.assertEqual(harness.run(["help", "--verbose"]), 0)
            help_text = help_out.getvalue()
            for expected in (
                "demo-tool v2.0.0+abc1234 - Copyright (c) Test Corp",
                "Demo CLI harness for unit testing.",
                "execute deployment workflow",
                "Detailed Action Descriptions:",
                "Executes the full workflow against the selected target.",
                "Exit codes:",
                "0   success",
                "1   operational or runtime execution error",
                "2   invalid arguments or syntax errors",
            ):
                self.assertIn(expected, help_text)

    def test_bare_invocation_prints_help_and_fallback_action_dispatches_non_flags(self) -> None:
        import contextlib

        harness = self._make_harness()
        out = io.StringIO()
        with redirect_stdout(out):
            self.assertEqual(harness.run([]), 0)
        self.assertIn("Usage:", out.getvalue())

        fb_harness = self._make_harness(fallback_action="run")
        fb_bare_out = io.StringIO()
        with redirect_stdout(fb_bare_out):
            self.assertEqual(fb_harness.run([]), 0)
        self.assertIn("Usage:", fb_bare_out.getvalue())

        fb_err = io.StringIO()
        with redirect_stdout(io.StringIO()), contextlib.redirect_stderr(fb_err):
            self.assertEqual(fb_harness.run(["--target", "staging"]), 2)
        self.assertIn("**[ERROR]** Unknown subcommand: '--target'", fb_err.getvalue())

    def test_handlers_propagate_exit_codes_and_invalid_args_return_two(self) -> None:
        import contextlib

        harness = self._make_harness()
        with redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
            self.assertEqual(harness.run(["run", "--target", "prod"]), 0)
            self.assertEqual(harness.run(["run", "--fail"]), 1)
            self.assertEqual(harness.run(["unknown-cmd"]), 2)
            self.assertEqual(harness.run(["run", "--nonexistent-flag"]), 2)

    def test_run_configures_utf8_output_once_before_action_dispatch(self) -> None:
        import contextlib

        events: list[str] = []
        harness = self._make_harness()
        harness.add_action("check-order", "check order", handler=lambda a, logger: (events.append("handler"), 0)[1])
        with (
            patch("support_python.cli.configure_utf8_output", side_effect=lambda: events.append("utf8"), create=True) as mock_utf8,
            redirect_stdout(io.StringIO()),
            contextlib.redirect_stderr(io.StringIO()),
        ):
            self.assertEqual(harness.run(["check-order"]), 0)
        self.assertEqual(mock_utf8.call_count, 1)
        self.assertEqual(events, ["utf8", "handler"])

    @staticmethod
    def _option_columns(help_text: str, labels: list[str]) -> dict[str, int]:
        """Return the column at which each labeled option line's help text starts."""
        columns: dict[str, int] = {}
        for line in help_text.splitlines():
            for label in labels:
                if line.startswith(f"  {label} "):
                    rest = line[2 + len(label) :]
                    columns[label] = 2 + len(label) + (len(rest) - len(rest.lstrip(" ")))
        return columns

    def test_long_global_option_label_keeps_aligned_separated_columns(self) -> None:
        harness = self._make_harness()
        harness.add_global_argument("--extremely-long-option-name", metavar="VALUE", help="global help text")
        label = "--extremely-long-option-name VALUE"
        help_text = harness.format_help()
        self.assertIn(f"{label}  ", help_text)
        columns = self._option_columns(help_text, [label, "--log-level LEVEL", "-h, --help"])
        self.assertEqual(len(set(columns.values())), 1, columns)
        self.assertEqual(columns[label], 2 + len(label) + 2)

    def test_long_action_option_label_keeps_aligned_separated_columns(self) -> None:
        harness = self._make_harness()

        def configure(parser) -> None:
            parser.add_argument("--extremely-long-action-option-name", help="action help text")

        harness.add_action("long", "long option action", handler=lambda a, logger: 0, configure_parser=configure)
        label = "--extremely-long-action-option-name"
        help_text = harness.format_action_help("long")
        self.assertIn(f"{label}  action help text", help_text)
        columns = self._option_columns(help_text, [label, "--log-level LEVEL", "-h, --help"])
        self.assertEqual(len(set(columns.values())), 1, columns)
        self.assertEqual(columns[label], 2 + len(label) + 2)

    def test_short_option_labels_keep_column_twenty_five(self) -> None:
        harness = self._make_harness()
        for help_text in (harness.format_help(), harness.format_action_help("run")):
            columns = self._option_columns(help_text, ["-h, --help", "--log-level LEVEL", "--target"])
            self.assertTrue(set(columns.values()) <= {25}, columns)
            self.assertIn("-h, --help", columns)

    def test_no_tool_module_calls_stream_reconfigure(self) -> None:
        from pathlib import Path

        tools_dir = Path(__file__).resolve().parent.parent / "src" / "support_python" / "tools"
        offending = [p.name for p in sorted(tools_dir.glob("*.py")) if "reconfigure(" in p.read_text(encoding="utf-8")]
        self.assertEqual(offending, [])


class ToolHarnessSubprocessIntegrationTests(unittest.TestCase):
    def test_demo_cli_subprocess_end_to_end(self) -> None:
        import os
        from pathlib import Path
        import subprocess
        import sys
        from tempfile import TemporaryDirectory

        src_dir = str(Path(__file__).resolve().parent.parent / "src")
        env = dict(os.environ)
        env["PYTHONPATH"] = f"{src_dir}{os.pathsep}{env['PYTHONPATH']}" if env.get("PYTHONPATH") else src_dir

        script_code = (
            "from __future__ import annotations\nimport sys\nfrom support_python.cli import ToolHarness\n"
            "harness = ToolHarness('subproc-demo', 'End-to-end subprocess demo CLI.', version='1.0.0')\n"
            "harness.add_action('work', 'run work action', handler=lambda a, l: (l.info(f'Hello {a.name}!'), 0)[1], "
            "configure_parser=lambda p: p.add_argument('--name', default='world'))\n"
            "harness.add_action('fail', 'run failing action', handler=lambda a, l: (l.error('Simulated operational failure'), 1)[1])\n"
            "if __name__ == '__main__':\n    sys.exit(harness.run())\n"
        )
        with TemporaryDirectory() as tmp:
            script_path = Path(tmp) / "demo_cli.py"
            log_path = Path(tmp) / "demo.log"
            script_path.write_text(script_code, encoding="utf-8")

            # Initialize a separate unrelated git repository as the subprocess working directory
            other_repo = Path(tmp) / "unrelated_repo"
            other_repo.mkdir()
            subprocess.run(["git", "init"], cwd=other_repo, capture_output=True, check=True)
            subprocess.run(["git", "config", "user.email", "test@example.com"], cwd=other_repo, capture_output=True, check=True)
            subprocess.run(["git", "config", "user.name", "Tester"], cwd=other_repo, capture_output=True, check=True)
            (other_repo / "README.md").write_text("unrelated\n", encoding="utf-8")
            subprocess.run(["git", "add", "README.md"], cwd=other_repo, capture_output=True, check=True)
            subprocess.run(["git", "commit", "-m", "Initial commit."], cwd=other_repo, capture_output=True, check=True)
            other_hash = subprocess.run(
                ["git", "rev-parse", "--short", "HEAD"], cwd=other_repo, capture_output=True, text=True, check=True
            ).stdout.strip()

            def run_cli(*cli_args: str):
                return subprocess.run(
                    [sys.executable, str(script_path), *cli_args],
                    cwd=other_repo,
                    capture_output=True,
                    text=True,
                    env=env,
                    timeout=10,
                )

            res_help = run_cli("help", "--verbose")
            self.assertEqual(res_help.returncode, 0)
            self.assertIn("subproc-demo v1.0.0 - Copyright (c) Giovanni Pellicciotta", res_help.stdout)
            self.assertNotIn(f"+{other_hash}", res_help.stdout)
            self.assertIn("Exit codes:", res_help.stdout)

            res_ver = run_cli("--version")
            self.assertEqual(res_ver.returncode, 0)
            self.assertEqual(res_ver.stdout.strip(), "subproc-demo v1.0.0 - Copyright (c) Giovanni Pellicciotta")

            res_work = run_cli("work", "--name", "Tester", "--log-file", str(log_path))
            self.assertEqual(res_work.returncode, 0)
            self.assertIn("Hello Tester!", res_work.stdout)
            log_content = log_path.read_text(encoding="utf-8")
            self.assertIn("**[INFO]**  Starting subproc-demo v1.0.0", log_content)
            self.assertIn("**[INFO]**  Hello Tester!", log_content)
            self.assertIn("with status: succeeded", log_content)

            res_fail = run_cli("fail", "--log-file", str(log_path))
            self.assertEqual(res_fail.returncode, 1)
            self.assertIn("**[ERROR]** Simulated operational failure", res_fail.stderr)
            self.assertIn("with status: failed", log_path.read_text(encoding="utf-8"))

            res_bad = run_cli("work", "--invalid-opt", "--log-file", str(log_path))
            self.assertEqual(res_bad.returncode, 2)
            self.assertIn("**[ERROR]**", res_bad.stderr)

    def test_tools_help_and_non_ascii_output_under_cp1252_pipe(self) -> None:
        import os
        from pathlib import Path
        import subprocess
        import sys

        src_dir = str(Path(__file__).resolve().parent.parent / "src")
        env = dict(os.environ)
        env["PYTHONPATH"] = f"{src_dir}{os.pathsep}{env['PYTHONPATH']}" if env.get("PYTHONPATH") else src_dir
        env["PYTHONIOENCODING"] = "cp1252"
        env.pop("PYTHONUTF8", None)

        for mod_name in ("processes", "agent_files", "lint_markdown", "git_repository_backup"):
            code = (
                f"from support_python.tools import {mod_name}\n"
                f"rc = {mod_name}.main(['help'])\n"
                "print('Non-ASCII check: \\u2713 \\u2014 \\u2603')\n"
                "raise SystemExit(rc)\n"
            )
            res = subprocess.run(
                [sys.executable, "-c", code],
                capture_output=True,
                env=env,
                timeout=10,
            )
            self.assertEqual(res.returncode, 0, res.stderr.decode("utf-8", errors="replace"))
            out_text = res.stdout.decode("utf-8")
            self.assertIn("Usage:", out_text)
            self.assertIn("Non-ASCII check: \u2713 \u2014 \u2603", out_text)


class ToolHarnessDebugImpliesVerboseTests(unittest.TestCase):
    def _make_harness(self):
        from support_python.cli import ToolHarness

        harness = ToolHarness(
            name="debug-tool",
            description="Debug harness test.",
            version="1.0.0",
            examples=["debug-tool run"],
            detailed_help="Extra details.",
        )
        seen: dict = {}

        def handle(args, logger) -> int:
            seen.update(verbose=args.verbose, logger_verbose=logger.verbose, level=logger.effective_level)
            return 0

        harness.add_action("run", "run the tool", handler=handle, detail="Runs the tool in detail.")
        return harness, seen

    def _run(self, harness, argv: list[str]) -> tuple[int, str]:
        import contextlib

        out = io.StringIO()
        with redirect_stdout(out), contextlib.redirect_stderr(io.StringIO()):
            code = harness.run(argv)
        return code, out.getvalue()

    def test_debug_alone_sets_args_verbose(self) -> None:
        harness, seen = self._make_harness()
        self.assertEqual(self._run(harness, ["run", "--debug"])[0], 0)
        self.assertEqual(seen, {"verbose": True, "logger_verbose": True, "level": "DEBUG"})

    def test_verbose_alone_keeps_info_threshold(self) -> None:
        harness, seen = self._make_harness()
        self.assertEqual(self._run(harness, ["run", "--verbose"])[0], 0)
        self.assertEqual(seen, {"verbose": True, "logger_verbose": True, "level": "INFO"})

    def test_log_level_wins_threshold_but_debug_still_implies_verbose(self) -> None:
        harness, seen = self._make_harness()
        self.assertEqual(self._run(harness, ["run", "--log-level", "WARN", "--debug"])[0], 0)
        self.assertEqual(seen, {"verbose": True, "logger_verbose": True, "level": "WARN"})

    def test_help_debug_matches_help_verbose(self) -> None:
        harness, _ = self._make_harness()
        for debug_argv, verbose_argv in (
            (["help", "--debug"], ["help", "--verbose"]),
            (["help", "run", "--debug"], ["help", "run", "--verbose"]),
            (["run", "--help", "--debug"], ["run", "--help", "--verbose"]),
        ):
            with self.subTest(argv=debug_argv):
                debug_out = self._run(harness, debug_argv)[1]
                self.assertEqual(debug_out, self._run(harness, verbose_argv)[1])
        self.assertIn("Detailed Action Descriptions:", self._run(harness, ["help", "--debug"])[1])

    def test_debug_option_help_mentions_verbose(self) -> None:
        harness, _ = self._make_harness()
        self.assertIn("enable debug output logging (implies --verbose)", harness.format_help())


class ToolHarnessJsonOutputTests(unittest.TestCase):
    def _make_harness(self):
        from support_python.cli import ToolHarness

        harness = ToolHarness(name="json-tool", description="JSON harness test.", version="1.0.0")
        seen: dict[str, bool] = {}

        def handle(args, logger) -> int:
            seen["json_output"] = logger.json_output
            logger.info("handler info")
            logger.emit_json({"ok": True})
            return 0

        harness.add_action("report", "report", handler=handle, configure_parser=ToolHarness.add_format_option)
        harness.add_action("plain", "plain", handler=handle)
        return harness, seen

    def _run(self, harness, argv: list[str]) -> tuple[int, str, str]:
        import contextlib

        out, err = io.StringIO(), io.StringIO()
        with redirect_stdout(out), contextlib.redirect_stderr(err):
            code = harness.run(argv)
        return code, out.getvalue(), err.getvalue()

    def test_add_format_option_registers_standard_option(self) -> None:
        import argparse

        from support_python.cli import ToolHarness

        parser = argparse.ArgumentParser()
        ToolHarness.add_format_option(parser)
        option = next(a for a in parser._actions if "--format" in a.option_strings)
        self.assertEqual((option.choices, option.default), (["text", "json"], "text"))
        self.assertEqual(option.help, "output format (text or json; default: text)")

        parser = argparse.ArgumentParser()
        ToolHarness.add_format_option(parser, default="json")
        option = next(a for a in parser._actions if "--format" in a.option_strings)
        self.assertEqual((option.default, option.help), ("json", "output format (text or json; default: json)"))

    def test_format_json_sets_json_output_and_keeps_stdout_pure(self) -> None:
        import json

        harness, seen = self._make_harness()
        code, out, err = self._run(harness, ["report", "--format", "json", "--verbose"])
        self.assertEqual(code, 0)
        self.assertTrue(seen["json_output"])
        self.assertEqual(json.loads(out), {"ok": True})
        for expected in ("Starting json-tool v1.0.0", "handler info", "Finished json-tool report"):
            self.assertIn(expected, err)

    def test_text_format_and_actions_without_format_leave_json_output_off(self) -> None:
        for argv in (["report"], ["report", "--format", "text"], ["plain"]):
            with self.subTest(argv=argv):
                harness, seen = self._make_harness()
                code, out, _ = self._run(harness, argv)
                self.assertEqual(code, 0)
                self.assertFalse(seen["json_output"])
                self.assertIn("handler info", out)

    def test_no_tool_module_subclasses_cli_logger(self) -> None:
        import re
        from pathlib import Path

        tools_dir = Path(__file__).resolve().parent.parent / "src" / "support_python" / "tools"
        pattern = re.compile(r"^class\s+\w+\([^)]*\bCliLogger\b[^)]*\)\s*:", re.MULTILINE)
        offending = [p.name for p in sorted(tools_dir.glob("*.py")) if pattern.search(p.read_text(encoding="utf-8"))]
        self.assertEqual(offending, [])


if __name__ == "__main__":
    unittest.main()
