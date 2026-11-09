from __future__ import annotations

import contextlib
import io
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

from support_python import (
    EXIT_COMMAND_NOT_FOUND,
    CliLogger,
    resolve_executable,
    run_step_command,
    stream_subprocess,
)


class StreamSubprocessUnitTests(unittest.TestCase):
    def test_streams_stdout_and_stderr_in_order_with_origin_and_skips_blank_lines(self) -> None:
        fake_stdout = io.StringIO("first stdout\n\n   \r\nsecond stderr\nthird line\r\n")
        fake_proc = MagicMock()
        fake_proc.pid = 4321
        fake_proc.stdout = fake_stdout
        fake_proc.wait.return_value = 0

        logged: list[tuple[str, str | None]] = []
        logger = MagicMock(spec=CliLogger)
        logger.log.side_effect = lambda msg, **kwargs: logged.append((msg, kwargs.get("origin")))

        with (
            patch("support_python.devops.steps.resolve_executable", return_value="/usr/bin/fake"),
            patch("support_python.devops.steps.subprocess.Popen", return_value=fake_proc) as mock_popen,
        ):
            code = stream_subprocess(["fake", "--arg"], logger=logger, origin="worker")

        self.assertEqual(code, 0)
        popen_kwargs = mock_popen.call_args.kwargs
        self.assertEqual(popen_kwargs["stdin"], subprocess.DEVNULL)
        self.assertEqual(popen_kwargs["stdout"], subprocess.PIPE)
        self.assertEqual(popen_kwargs["stderr"], subprocess.STDOUT)

        messages = [m for m, _ in logged]
        origins = [o for _, o in logged]
        self.assertTrue(all(o == "worker" for o in origins))
        self.assertEqual(
            messages[2:],
            ["first stdout", "second stderr", "third line"],
        )

    def test_logs_command_line_and_pid_before_output(self) -> None:
        fake_stdout = io.StringIO("child line 1\n")
        fake_proc = MagicMock()
        fake_proc.pid = 9876
        fake_proc.stdout = fake_stdout
        fake_proc.wait.return_value = 0

        logged: list[str] = []
        logger = MagicMock(spec=CliLogger)
        logger.log.side_effect = lambda msg, **kwargs: logged.append(msg)

        with (
            patch("support_python.devops.steps.resolve_executable", return_value="/usr/bin/my-tool"),
            patch("support_python.devops.steps.subprocess.Popen", return_value=fake_proc),
        ):
            code = stream_subprocess(["my-tool", "alpha", "beta gamma"], logger=logger, origin="agent")

        self.assertEqual(code, 0)
        self.assertGreaterEqual(len(logged), 3)
        self.assertTrue(logged[0].startswith("Command: "))
        self.assertIn("my-tool", logged[0])
        self.assertIn("beta gamma", logged[0])
        self.assertEqual(logged[1], "Process ID: 9876")
        self.assertEqual(logged[2], "child line 1")

    def test_returns_exit_code_and_missing_executable_returns_not_found_and_logs_error(self) -> None:
        fake_proc = MagicMock()
        fake_proc.pid = 1111
        fake_proc.stdout = io.StringIO("done\n")
        fake_proc.wait.return_value = 7

        logger = MagicMock(spec=CliLogger)
        with (
            patch("support_python.devops.steps.resolve_executable", return_value="/bin/tool"),
            patch("support_python.devops.steps.subprocess.Popen", return_value=fake_proc),
        ):
            code = stream_subprocess(["tool"], logger=logger)
        self.assertEqual(code, 7)

        err_logger = MagicMock(spec=CliLogger)
        with patch("support_python.devops.steps.resolve_executable", return_value=None):
            not_found_code = stream_subprocess(["no-such-binary-xyz-999"], logger=err_logger, origin="runner")
        self.assertEqual(not_found_code, EXIT_COMMAND_NOT_FOUND)
        self.assertEqual(EXIT_COMMAND_NOT_FOUND, 127)
        err_logger.error.assert_called_once()
        self.assertIn("no-such-binary-xyz-999", err_logger.error.call_args.args[0])

    def test_oserror_on_launch_returns_one_and_logs_error(self) -> None:
        logger = MagicMock(spec=CliLogger)
        with (
            patch("support_python.devops.steps.resolve_executable", return_value="/bin/broken"),
            patch("support_python.devops.steps.subprocess.Popen", side_effect=OSError("Permission denied")),
        ):
            code = stream_subprocess(["broken"], logger=logger)
        self.assertEqual(code, 1)
        logger.error.assert_called_once()
        self.assertIn("broken", logger.error.call_args.args[0])

    def test_on_line_callback_sees_every_raw_line_and_exceptions_do_not_kill_stream(self) -> None:
        raw_lines = ["line one\n", "\n", "raise here\n", "line two\r\n"]
        fake_proc = MagicMock()
        fake_proc.pid = 2222
        fake_proc.stdout = io.StringIO("".join(raw_lines))
        fake_proc.wait.return_value = 0

        seen_by_callback: list[str] = []

        def callback(raw_line: str) -> None:
            seen_by_callback.append(raw_line)
            if "raise" in raw_line:
                raise RuntimeError("callback boom")

        logged: list[str] = []
        logger = MagicMock(spec=CliLogger)
        logger.log.side_effect = lambda msg, **kwargs: logged.append(msg)

        with (
            patch("support_python.devops.steps.resolve_executable", return_value="/bin/tool"),
            patch("support_python.devops.steps.subprocess.Popen", return_value=fake_proc),
        ):
            code = stream_subprocess(["tool"], logger=logger, on_line=callback)

        self.assertEqual(code, 0)
        self.assertEqual(seen_by_callback, raw_lines)
        self.assertIn("line one", logged)
        self.assertIn("raise here", logged)
        self.assertIn("line two", logged)

    def test_keyboard_interrupt_terminates_waits_5s_kills_and_reraises(self) -> None:
        class InterruptingStdout:
            def __init__(self) -> None:
                self.calls = 0
                self.closed = False

            def readline(self) -> str:
                self.calls += 1
                if self.calls == 1:
                    return "first line before interrupt\n"
                raise KeyboardInterrupt()

            def close(self) -> None:
                self.closed = True

        fake_stdout = InterruptingStdout()
        fake_proc = MagicMock()
        fake_proc.pid = 5555
        fake_proc.stdout = fake_stdout
        fake_proc.wait.side_effect = [
            subprocess.TimeoutExpired(cmd=["tool"], timeout=5),
            -9,
        ]

        logger = MagicMock(spec=CliLogger)
        with (
            patch("support_python.devops.steps.resolve_executable", return_value="/bin/tool"),
            patch("support_python.devops.steps.subprocess.Popen", return_value=fake_proc),
        ):
            with self.assertRaises(KeyboardInterrupt):
                stream_subprocess(["tool"], logger=logger, origin="agent")

        fake_proc.terminate.assert_called_once_with()
        self.assertEqual(fake_proc.wait.call_count, 2)
        self.assertEqual(fake_proc.wait.call_args_list[0].kwargs.get("timeout"), 5)
        fake_proc.kill.assert_called_once_with()
        self.assertTrue(fake_stdout.closed)

    def test_resolve_executable_checks_scripts_dir_and_sys_executable(self) -> None:
        self.assertEqual(resolve_executable(sys.executable), sys.executable)
        with tempfile.TemporaryDirectory() as tmp:
            name = "custom-step-tool"
            tool = Path(tmp) / (f"{name}.exe" if os.name == "nt" else name)
            tool.write_text("", encoding="utf-8")
            tool.chmod(0o755)
            with patch("support_python.devops.steps.sysconfig.get_path", return_value=tmp):
                resolved = resolve_executable(name)
            self.assertIsNotNone(resolved)
            assert resolved is not None
            self.assertEqual(Path(resolved).resolve().parent, Path(tmp).resolve())

    def test_run_step_command_delegates_and_handles_missing_executable(self) -> None:
        err = io.StringIO()
        with contextlib.redirect_stderr(err):
            code = run_step_command(["nonexistent-step-binary-xyz"], Path("."))
        self.assertEqual(code, EXIT_COMMAND_NOT_FOUND)
        self.assertIn("Executable not found", err.getvalue())

    def test_run_step_stream_reuses_stream_subprocess(self) -> None:
        from support_python import run_step

        buf = io.StringIO()
        with (
            contextlib.redirect_stdout(buf),
            patch("support_python.devops.steps.stream_subprocess", return_value=0) as mock_stream,
        ):
            ok = run_step("Streaming step", ["some-cmd", "--flag"], stream=True, origin="step")
        self.assertTrue(ok)
        mock_stream.assert_called_once()
        self.assertEqual(mock_stream.call_args.kwargs["origin"], "step")


class StreamSubprocessIntegrationTests(unittest.TestCase):
    def test_real_child_python_prints_100_lines_and_exits_3(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            log_path = Path(tmp_dir) / "stream.log"
            logger = CliLogger(log_path=log_path, log_level="INFO", verbose=False)
            script = (
                "import sys\n"
                "for i in range(100):\n"
                "    stream = sys.stdout if i % 2 == 0 else sys.stderr\n"
                "    print(f'line-{i:03d}', file=stream, flush=True)\n"
                "sys.exit(3)\n"
            )
            seen_callbacks: list[str] = []
            stdout_buf = io.StringIO()
            with contextlib.redirect_stdout(stdout_buf):
                code = stream_subprocess(
                    [sys.executable, "-c", script],
                    cwd=tmp_dir,
                    logger=logger,
                    origin="child-test",
                    on_line=seen_callbacks.append,
                )

            self.assertEqual(code, 3)
            self.assertEqual(len(seen_callbacks), 100)
            self.assertTrue(log_path.exists())
            content = log_path.read_text(encoding="utf-8")
            self.assertIn("Command: ", content)
            self.assertIn("Process ID: ", content)
            self.assertIn("<child-test>", content)
            for i in range(100):
                self.assertIn(f"line-{i:03d}", content)


if __name__ == "__main__":
    unittest.main()
