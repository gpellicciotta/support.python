from __future__ import annotations

import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from tests.conftest import (
    REAL_HOME,
    check_snapshot_diff,
    format_leak_report,
    take_snapshot,
)


class ConftestGuardTests(unittest.TestCase):
    def test_home_redirected_to_temp_directory(self) -> None:
        """A test writing Path.home() / 'leak.txt' lands in the temporary home, never the real one."""
        target = Path.home() / "leak.txt"
        target.write_text("safe test leak\n", encoding="utf-8")
        try:
            self.assertTrue(target.exists())
            self.assertNotEqual(Path.home().resolve(), REAL_HOME)
            self.assertFalse((REAL_HOME / "leak.txt").exists())
            for env_var in ("HOME", "USERPROFILE", "APPDATA", "XDG_CONFIG_HOME"):
                self.assertIn(env_var, os.environ)
                self.assertNotEqual(Path(os.environ[env_var]).resolve(), REAL_HOME)
        finally:
            if target.exists():
                target.unlink()

    def test_guard_reports_write_under_real_home_and_fails(self) -> None:
        """Proves a deliberate write under the guarded home paths is detected and reported."""
        with tempfile.TemporaryDirectory() as tmp_home_str:
            fake_home = Path(tmp_home_str).resolve()
            before = take_snapshot(home_root=fake_home, plan_dir=None)

            # Simulate a deliberate write into the guarded home area
            leaked_file = fake_home / "leak.txt"
            leaked_file.write_text("deliberate leak\n", encoding="utf-8")

            after = take_snapshot(home_root=fake_home, plan_dir=None)
            diff = check_snapshot_diff(before, after)

            self.assertTrue(diff["created"] or diff["modified"])
            report = format_leak_report(diff)
            self.assertIn("leak.txt", report)
            self.assertIn("Real-state write guard failed", report)

    def test_guard_reports_write_into_plan_and_fails(self) -> None:
        """The guard reports a write into the repository's .plan/ and fails the session."""
        with tempfile.TemporaryDirectory() as tmp_plan_str:
            fake_plan = Path(tmp_plan_str).resolve()
            (fake_plan / "tasks").mkdir()
            (fake_plan / "tasks" / "existing.md").write_text("old content\n", encoding="utf-8")

            before = take_snapshot(home_root=fake_plan, plan_dir=fake_plan)

            # Simulate test modifying existing file and creating a new file in .plan
            (fake_plan / "tasks" / "existing.md").write_text("modified content\n", encoding="utf-8")
            (fake_plan / "tasks" / "leak_task.md").write_text("leaked task\n", encoding="utf-8")

            after = take_snapshot(home_root=fake_plan, plan_dir=fake_plan)
            diff = check_snapshot_diff(before, after)

            self.assertIn(str((fake_plan / "tasks" / "leak_task.md").resolve()), diff["created"])
            self.assertIn(str((fake_plan / "tasks" / "existing.md").resolve()), diff["modified"])

            report = format_leak_report(diff)
            self.assertIn("leak_task.md", report)
            self.assertIn("existing.md", report)
            self.assertIn("Real-state write guard failed", report)

    def test_guard_ignores_work_directory_in_plan(self) -> None:
        """The guard ignores changes inside .plan/work where worktrees reside."""
        with tempfile.TemporaryDirectory() as tmp_plan_str:
            fake_plan = Path(tmp_plan_str).resolve()
            work_dir = fake_plan / "work" / "task-branch"
            work_dir.mkdir(parents=True)

            before = take_snapshot(home_root=fake_plan, plan_dir=fake_plan)

            # Writes in work/ must be ignored
            (work_dir / "file.txt").write_text("worktree edit\n", encoding="utf-8")

            after = take_snapshot(home_root=fake_plan, plan_dir=fake_plan)
            diff = check_snapshot_diff(before, after)

            self.assertEqual(diff["created"], [])
            self.assertEqual(diff["modified"], [])
            self.assertEqual(diff["deleted"], [])

    def test_deliberate_write_fails_pytest_session(self) -> None:
        """Running pytest on a test suite with the guard active fails if a test leaks a write."""
        with tempfile.TemporaryDirectory() as tmp_run_str:
            run_dir = Path(tmp_run_str).resolve()
            fake_home = run_dir / "fake_home"
            fake_home.mkdir()
            conftest_source = (Path(__file__).resolve().parent / "conftest.py").read_text(encoding="utf-8")
            (run_dir / "conftest.py").write_text(conftest_source, encoding="utf-8")
            (run_dir / "test_leak.py").write_text(
                "import os\n"
                "from pathlib import Path\n"
                "def test_leak():\n"
                '    h = Path(os.environ["SUPPORT_PYTHON_GUARD_HOME"])\n'
                '    (h / "leak.txt").write_text("leak", encoding="utf-8")\n',
                encoding="utf-8",
            )
            env = {
                **os.environ,
                "SUPPORT_PYTHON_GUARD_HOME": str(fake_home),
                "SUPPORT_PYTHON_GUARD_PLAN": str(run_dir),
            }
            res = subprocess.run(
                [sys.executable, "-m", "pytest", str(run_dir / "test_leak.py")],
                capture_output=True,
                text=True,
                env=env,
                timeout=30,
            )
            self.assertNotEqual(res.returncode, 0)
            output = res.stdout + res.stderr
            self.assertIn("Real-state write guard failed", output)
            self.assertIn("leak.txt", output)


if __name__ == "__main__":
    unittest.main()
