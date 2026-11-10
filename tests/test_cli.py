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

    def test_build_metadata_reads_install_time_commit_from_direct_url(self) -> None:
        import json
        from pathlib import Path
        from unittest.mock import MagicMock
        from support_python.cli import get_full_version, resolve_build_metadata

        resolve_build_metadata.cache_clear()
        mock_dist = MagicMock()
        mock_dist.read_text.return_value = json.dumps(
            {
                "url": "https://github.com/gpellicciotta/support.python.git",
                "vcs_info": {"commit_id": "341b3f3ff018a43bdc29410e1429a2c0f108c865", "vcs": "git"},
            }
        )
        installed_dir = Path("C:/app/.venv/Lib/site-packages/support_python")
        with (
            patch("importlib.metadata.distribution", return_value=mock_dist),
            patch("support_python.cli.__file__", str(installed_dir / "cli.py")),
        ):
            self.assertEqual(resolve_build_metadata(), "341b3f3")
            self.assertEqual(resolve_build_metadata(installed_dir), "341b3f3")
            self.assertEqual(get_full_version("2.0.0", cwd=installed_dir), "2.0.0+341b3f3")
        resolve_build_metadata.cache_clear()

    def test_foreign_repo_with_venv_keeps_own_hash(self) -> None:
        from pathlib import Path
        import subprocess
        from tempfile import TemporaryDirectory
        from support_python.cli import get_full_version, resolve_build_metadata

        resolve_build_metadata.cache_clear()
        with TemporaryDirectory() as tmp:
            foreign_repo = Path(tmp) / "consumer_repo"
            foreign_repo.mkdir()
            subprocess.run(["git", "init"], cwd=foreign_repo, capture_output=True, check=True)
            subprocess.run(["git", "config", "user.email", "tester@example.com"], cwd=foreign_repo, capture_output=True, check=True)
            subprocess.run(["git", "config", "user.name", "Tester"], cwd=foreign_repo, capture_output=True, check=True)
            (foreign_repo / "README.md").write_text("Consumer repo\n", encoding="utf-8")
            subprocess.run(["git", "add", "README.md"], cwd=foreign_repo, capture_output=True, check=True)
            subprocess.run(["git", "commit", "-m", "Consumer commit"], cwd=foreign_repo, capture_output=True, check=True)
            expected_hash = subprocess.run(
                ["git", "rev-parse", "--short", "HEAD"], cwd=foreign_repo, capture_output=True, text=True, check=True
            ).stdout.strip()

            installed_pkg = foreign_repo / ".venv" / "Lib" / "site-packages" / "support_python"
            installed_pkg.mkdir(parents=True)
            cli_py = installed_pkg / "cli.py"
            cli_py.write_text("# dummy\n", encoding="utf-8")

            with patch("support_python.cli.__file__", str(cli_py)):
                self.assertEqual(resolve_build_metadata(foreign_repo), expected_hash)
                self.assertEqual(get_full_version("1.0.0", cwd=foreign_repo), f"1.0.0+{expected_hash}")

                resolve_build_metadata.cache_clear()
                self.assertEqual(resolve_build_metadata(installed_pkg), "unknown")
                self.assertEqual(get_full_version("2.0.0", cwd=installed_pkg), "2.0.0")

                resolve_build_metadata.cache_clear()
                self.assertEqual(resolve_build_metadata(installed_pkg / "tools"), "unknown")
                self.assertEqual(get_full_version("2.0.0", cwd=installed_pkg / "tools"), "2.0.0")
        resolve_build_metadata.cache_clear()

    def test_source_or_editable_checkout_returns_checkout_hash(self) -> None:
        from pathlib import Path
        import subprocess
        from support_python.cli import get_full_version, resolve_build_metadata

        resolve_build_metadata.cache_clear()
        repo_root = Path(__file__).resolve().parent.parent
        expected_hash = subprocess.run(
            ["git", "rev-parse", "--short", "HEAD"], cwd=repo_root, capture_output=True, text=True, check=True
        ).stdout.strip()

        self.assertEqual(resolve_build_metadata(), expected_hash)
        pkg_dir = repo_root / "src" / "support_python"
        self.assertEqual(resolve_build_metadata(pkg_dir), expected_hash)
        tools_dir = pkg_dir / "tools"
        self.assertEqual(resolve_build_metadata(tools_dir), expected_hash)
        self.assertEqual(resolve_build_metadata(repo_root), expected_hash)
        self.assertTrue(get_full_version("2.0.15-pre").startswith(f"2.0.15-pre+{expected_hash}"))
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

        err = io.StringIO()
        with redirect_stdout(io.StringIO()), contextlib.redirect_stderr(err):
            self.assertEqual(harness.run(["--target", "staging"]), 2)
        self.assertIn("**[ERROR]** Unknown subcommand: '--target'", err.getvalue())

    def test_fallback_action_runs_when_the_command_line_starts_with_an_option(self) -> None:
        harness = self._make_harness(fallback_action="run")
        out = io.StringIO()
        with redirect_stdout(out):
            self.assertEqual(harness.run(["--target", "staging", "--verbose"]), 0)
        self.assertIn("Running on staging", out.getvalue())

    def test_leading_options_keep_a_named_action(self) -> None:
        harness = self._make_harness(fallback_action="run")
        out = io.StringIO()
        with redirect_stdout(out):
            self.assertEqual(harness.run(["--verbose", "run", "--target", "prod"]), 0)
            self.assertEqual(harness.run(["--log-level", "DEBUG", "version"]), 0)
            self.assertEqual(harness.run(["--verbose", "help"]), 0)
        self.assertIn("Running on prod", out.getvalue())
        self.assertIn("demo-tool v2.0.0", out.getvalue())
        self.assertIn("Usage:", out.getvalue())

    def test_leading_options_use_each_actions_arity_and_skip_action_names(self) -> None:
        harness = self._make_harness(fallback_action="run")
        listed: list[object] = []

        def configure_list(parser) -> None:
            parser.add_argument("--maybe", nargs="?", const="yes")
            parser.add_argument("-f", "--filter")

        harness.add_action(
            "list", "list targets", lambda args, logger: listed.append(args.filter) or 0, configure_parser=configure_list
        )
        with redirect_stdout(io.StringIO()):
            self.assertEqual(harness.run(["--filter", "prod", "list"]), 0)
            self.assertEqual(harness.run(["--maybe", "--log-level", "DEBUG", "list"]), 0)
            self.assertEqual(harness.run(["--maybe", "list"]), 0)
            self.assertEqual(harness.run(["--filt", "staging", "list"]), 0)
            self.assertEqual(harness.run(["-vf", "dev", "list"]), 0)
            self.assertEqual(harness.run(["-vfqa", "list"]), 0)
        self.assertEqual(listed, ["prod", None, None, "staging", "dev", "qa"])

    def test_leading_global_values_keep_the_help_target(self) -> None:
        harness = self._make_harness(fallback_action="run")
        out = io.StringIO()
        with redirect_stdout(out):
            self.assertEqual(harness.run(["--log-level", "DEBUG", "help", "run"]), 0)
        self.assertIn("Executes the full workflow against the selected target.", out.getvalue())

    def test_leading_option_with_an_invalid_value_still_exits_two(self) -> None:
        import contextlib

        harness = self._make_harness(fallback_action="run")
        with redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
            self.assertEqual(harness.run(["--log-level", "LOUD"]), 2)

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

    def test_version_output_maps_trailing_rc0_to_pre(self) -> None:
        from support_python.cli import ToolHarness

        harness = ToolHarness("demo", "Demo.", version="3.0.0rc0")
        self.assertTrue(harness.format_version().startswith("demo v3.0.0-pre"))

    def test_version_output_preserves_other_versions(self) -> None:
        from support_python.cli import ToolHarness

        for ver in ("3.0.0rc1", "3.0.0", "3.0.0-pre"):
            with self.subTest(version=ver):
                harness = ToolHarness("demo", "Demo.", version=ver)
                self.assertTrue(harness.format_version().startswith(f"demo v{ver}"))

    def test_default_banner_omits_copyright_suffix(self) -> None:
        from support_python.cli import APP_AUTHOR, COPYRIGHT, ToolHarness

        self.assertEqual(APP_AUTHOR, "")
        self.assertEqual(COPYRIGHT, "")

        with patch("support_python.cli.resolve_build_metadata", return_value="unknown"):
            harness = ToolHarness("plain-tool", "Plain description.", version="1.0.0")
            self.assertEqual(harness.format_version(), "plain-tool v1.0.0")
            self.assertTrue(harness.format_help().startswith("plain-tool v1.0.0\n\nPlain description."))

    def test_explicit_copyright_keeps_suffix(self) -> None:
        from support_python.cli import ToolHarness

        with patch("support_python.cli.resolve_build_metadata", return_value="unknown"):
            harness = ToolHarness("custom-tool", "Custom description.", version="1.0.0", copyright="Copyright (c) Someone")
            self.assertEqual(harness.format_version(), "custom-tool v1.0.0 - Copyright (c) Someone")
            self.assertTrue(harness.format_help().startswith("custom-tool v1.0.0 - Copyright (c) Someone\n\nCustom description."))


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
            self.assertTrue(res_help.stdout.startswith("subproc-demo v1.0.0\n"))
            self.assertNotIn("Copyright", res_help.stdout)
            self.assertNotIn(f"+{other_hash}", res_help.stdout)
            self.assertIn("Exit codes:", res_help.stdout)

            res_ver = run_cli("--version")
            self.assertEqual(res_ver.returncode, 0)
            self.assertEqual(res_ver.stdout.strip(), "subproc-demo v1.0.0")

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

    def test_demo_cli_subprocess_version_maps_trailing_rc0_to_pre(self) -> None:
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
            "harness = ToolHarness('demo', 'Demo CLI.', version='3.0.0rc0')\n"
            "if __name__ == '__main__':\n    sys.exit(harness.run())\n"
        )
        with TemporaryDirectory() as tmp:
            script_path = Path(tmp) / "demo_cli.py"
            script_path.write_text(script_code, encoding="utf-8")

            def run_cli(*cli_args: str):
                return subprocess.run(
                    [sys.executable, str(script_path), *cli_args],
                    capture_output=True,
                    text=True,
                    env=env,
                    timeout=10,
                )

            res = run_cli("--version")
            self.assertEqual(res.returncode, 0)
            self.assertTrue(res.stdout.startswith("demo v3.0.0-pre"))

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

    def test_installed_wheel_in_foreign_repo_venv_shows_no_foreign_hash(self) -> None:
        from pathlib import Path
        import subprocess
        import sys
        from tempfile import TemporaryDirectory

        repo_root = Path(__file__).resolve().parent.parent
        with TemporaryDirectory() as tmp:
            foreign_repo = Path(tmp) / "foreign_repo"
            foreign_repo.mkdir()
            subprocess.run(["git", "init"], cwd=foreign_repo, capture_output=True, check=True)
            subprocess.run(["git", "config", "user.email", "tester@example.com"], cwd=foreign_repo, capture_output=True, check=True)
            subprocess.run(["git", "config", "user.name", "Tester"], cwd=foreign_repo, capture_output=True, check=True)
            (foreign_repo / "README.md").write_text("Foreign project\n", encoding="utf-8")
            subprocess.run(["git", "add", "README.md"], cwd=foreign_repo, capture_output=True, check=True)
            subprocess.run(["git", "commit", "-m", "Initial foreign commit"], cwd=foreign_repo, capture_output=True, check=True)
            foreign_hash = subprocess.run(
                ["git", "rev-parse", "--short", "HEAD"], cwd=foreign_repo, capture_output=True, text=True, check=True
            ).stdout.strip()

            venv_dir = foreign_repo / ".venv"
            subprocess.run([sys.executable, "-m", "venv", str(venv_dir)], check=True)
            py_exe = venv_dir / ("Scripts/python.exe" if sys.platform == "win32" else "bin/python")

            whl_dir = Path(tmp) / "whl"
            subprocess.run(
                [sys.executable, "-m", "build", "--wheel", "-o", str(whl_dir), str(repo_root)],
                capture_output=True,
                check=True,
            )
            whl = next(whl_dir.glob("*.whl"))
            subprocess.run([str(py_exe), "-m", "pip", "install", "--no-deps", str(whl)], capture_output=True, check=True)

            agent_files_bin = venv_dir / ("Scripts/agent-files.exe" if sys.platform == "win32" else "bin/agent-files")
            for arg in ("version", "--version"):
                with self.subTest(arg=arg):
                    res = subprocess.run([str(agent_files_bin), arg], cwd=foreign_repo, capture_output=True, text=True, timeout=15)
                    self.assertEqual(res.returncode, 0, res.stderr)
                    self.assertNotIn(foreign_hash, res.stdout)
                    self.assertIn("agent-files v", res.stdout)
                    self.assertIn("Giovanni Pellicciotta", res.stdout)


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


class ToolVersionReportingTests(unittest.TestCase):
    """Verify that every tool reports the installed support-python version instead of cwd's project version."""

    def test_project_version_and_full_version_do_not_default_to_cwd(self) -> None:
        import os
        import subprocess
        import sys
        from pathlib import Path
        from tempfile import TemporaryDirectory
        from support_python.version import get_package_version, get_project_version

        src_dir = str(Path(__file__).resolve().parent.parent / "src")
        expected_ver = get_package_version("support-python")
        if expected_ver == "0.0.0+unknown":
            expected_ver = get_project_version(Path(src_dir) / "support_python")

        with TemporaryDirectory() as tmp:
            unrelated = Path(tmp)
            (unrelated / "pyproject.toml").write_text(
                '[project]\nname = "unrelated-project"\nversion = "9.9.9"\n',
                encoding="utf-8",
            )
            code = (
                "from support_python.cli import PROJECT_VERSION, get_full_version\n"
                "print('PROJECT_VERSION=' + PROJECT_VERSION)\n"
                "print('FULL_VERSION=' + get_full_version())\n"
            )
            env = dict(os.environ)
            env["PYTHONPATH"] = f"{src_dir}{os.pathsep}{env['PYTHONPATH']}" if env.get("PYTHONPATH") else src_dir
            res = subprocess.run(
                [sys.executable, "-c", code],
                cwd=unrelated,
                capture_output=True,
                text=True,
                env=env,
                timeout=15,
            )
            self.assertEqual(res.returncode, 0, res.stderr)
            self.assertNotIn("9.9.9", res.stdout)
            self.assertIn(f"PROJECT_VERSION={expected_ver}", res.stdout)
            self.assertTrue(res.stdout.startswith(f"PROJECT_VERSION={expected_ver}\nFULL_VERSION={expected_ver}"))

    def test_every_tool_version_reports_support_python_version_in_unrelated_directory(self) -> None:
        import os
        import subprocess
        import sys
        from pathlib import Path
        from tempfile import TemporaryDirectory
        from support_python.version import get_package_version, get_project_version

        src_dir = str(Path(__file__).resolve().parent.parent / "src")
        expected_ver = get_package_version("support-python")
        if expected_ver == "0.0.0+unknown":
            expected_ver = get_project_version(Path(src_dir) / "support_python")

        tools = [
            ("processes", "support_python.tools.processes"),
            ("agent-files", "support_python.tools.agent_files"),
            ("agent-digest", "support_python.tools.agent_digest"),
            ("lint-markdown", "support_python.tools.lint_markdown"),
            ("git-repository-backup", "support_python.tools.git_repository_backup"),
        ]

        with TemporaryDirectory() as tmp:
            unrelated = Path(tmp)
            (unrelated / "pyproject.toml").write_text(
                '[project]\nname = "unrelated-project"\nversion = "9.9.9"\n',
                encoding="utf-8",
            )
            env = dict(os.environ)
            env["PYTHONPATH"] = f"{src_dir}{os.pathsep}{env['PYTHONPATH']}" if env.get("PYTHONPATH") else src_dir

            for tool_name, mod_name in tools:
                for arg in ("--version", "version"):
                    with self.subTest(tool=tool_name, arg=arg):
                        code = f"import sys; from {mod_name} import main; sys.exit(main(sys.argv[1:]))"
                        res = subprocess.run(
                            [sys.executable, "-c", code, arg],
                            cwd=unrelated,
                            capture_output=True,
                            text=True,
                            env=env,
                            timeout=15,
                        )
                        self.assertEqual(res.returncode, 0, res.stderr)
                        output = res.stdout.strip()
                        self.assertNotIn("9.9.9", output)
                        self.assertTrue(
                            output.startswith(f"{tool_name} v{expected_ver}"),
                            f"Expected '{output}' to start with '{tool_name} v{expected_ver}'",
                        )


if __name__ == "__main__":
    unittest.main()
