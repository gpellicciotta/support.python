"""Tests for support_python.cli module."""

from __future__ import annotations

from contextlib import redirect_stdout
import io
import unittest
from unittest.mock import patch

from support_python.cli import (
    build_action_parser,
    format_version,
    print_help,
    print_version,
)


class BuildActionParserTests(unittest.TestCase):
    def test_default_action_used_when_omitted(self) -> None:
        parser = build_action_parser("some-tool", "A tool", ["greet", "version"], default_action="greet")
        args = parser.parse_args([])
        self.assertEqual(args.action, "greet")
        self.assertFalse(args.help)
        self.assertFalse(args.version)
        self.assertFalse(args.verbose)
        self.assertFalse(args.debug)

    def test_rejects_unknown_action(self) -> None:
        parser = build_action_parser("some-tool", "A tool", ["greet", "version"], default_action="greet")
        with self.assertRaises(SystemExit):
            parser.parse_args(["not-an-action"])


class PrintVersionAndHelpTests(unittest.TestCase):
    def test_format_version(self) -> None:
        self.assertEqual(
            format_version("some-tool", "1.2.3", author="Some Author"),
            "some-tool v1.2.3 - Copyright (c) Some Author",
        )

    def test_print_version_uses_standard_template(self) -> None:
        buffer = io.StringIO()
        with redirect_stdout(buffer):
            print_version("some-tool", "1.2.3", author="Some Author")
        self.assertEqual(buffer.getvalue().strip(), "some-tool v1.2.3 - Copyright (c) Some Author")

    def test_print_help_lists_custom_exit_codes(self) -> None:
        parser = build_action_parser("some-tool", "A tool", ["run"], default_action="run")
        buffer = io.StringIO()
        with redirect_stdout(buffer):
            print_help("some-tool", "1.2.3", "A tool", parser, exit_codes=[(0, "OK"), (2, "Bad input")], author="Some Author")
        output = buffer.getvalue()
        self.assertIn("some-tool v1.2.3 - Copyright (c) Some Author", output)
        self.assertIn("0  OK", output)
        self.assertIn("2  Bad input", output)


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


if __name__ == "__main__":
    unittest.main()
